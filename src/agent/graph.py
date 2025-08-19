import asyncio
from typing import cast, Any, Literal
import json

from tavily import AsyncTavilyClient
from langchain_anthropic import ChatAnthropic
from langchain_core import InMemoryRateLimiter
from langchain_core.runnables import RunnableConfig
from langgraph import START, END, StateGraph
from pydantic import BaseModel, Field

from agent.configuration import Configuration
from agent.state import InputState, OutputState, OverallState
from agent.utils import deduplicate_and_format_sources, format_all_notes
from agent.prompts import (
    REFLECTION_PROMPT,
    INFO_PROMPT,
    QUERY_WRITER_PROMPT,
)

# LLMs

rate_limiter = InMemoryRateLimiter(
    requests_per_second=4,
    check_every_n_seconds=0.1,
    max_bucket_size=10,  # Controls the maximum burst size.
)
claude_3_5_sonnet = ChatAnthropic(
    model="claude-3-5-sonnet-latest", temperature=0, rate_limiter=rate_limiter
)

# Search

tavily_async_client = AsyncTavilyClient()


class Queries(BaseModel):
    queries: list[str] = Field(
        description="List of search queries.",
    )


class ReflectionOutput(BaseModel):
    """Structured output from the reflection analysis."""
    
    extracted_info: dict[str, Any] = Field(
        description="Dictionary containing the structured information found in the research notes"
    )
    
    completeness_assessment: dict[str, float] = Field(
        description="Analysis of how complete each schema field is (0-100%)"
    )
    
    missing_information: list[str] = Field(
        description="List of specific information gaps that need to be addressed"
    )
    
    research_decision: Literal["CONTINUE", "CONCLUDE"] = Field(
        description="Decision on whether to continue research or conclude the process"
    )
    
    reasoning: str = Field(
        description="Detailed explanation of the research decision"
    )
    
    suggested_queries: list[str] = Field(
        default_factory=list,
        description="If continuing, specific search queries to fill the gaps"
    )



def generate_queries(state: OverallState, config: RunnableConfig) -> dict[str, Any]:
    """Generate search queries based on the user input and extraction schema."""
    # Get configuration
    configurable = Configuration.from_runnable_config(config)
    max_search_queries = configurable.max_search_queries

    # Generate search queries
    structured_llm = claude_3_5_sonnet.with_structured_output(Queries)

    # Format system instructions
    person_str = f"Email: {state.person['email']}"
    if "name" in state.person:
        person_str += f" Name: {state.person['name']}"
    if "linkedin" in state.person:
        person_str += f" LinkedIn URL: {state.person['linkedin']}"
    if "role" in state.person:
        person_str += f" Role: {state.person['role']}"
    if "company" in state.person:
        person_str += f" Company: {state.person['company']}"

    query_instructions = QUERY_WRITER_PROMPT.format(
        person=person_str,
        info=json.dumps(state.extraction_schema, indent=2),
        user_notes=state.user_notes,
        max_search_queries=max_search_queries,
    )

    # Generate queries
    results = cast(
        Queries,
        structured_llm.invoke(
            [
                {"role": "system", "content": query_instructions},
                {
                    "role": "user",
                    "content": "Please generate a list of search queries related to the schema that you want to populate.",
                },
            ]
        ),
    )

    # Queries
    query_list = [query for query in results.queries]
    return {"search_queries": query_list}


async def research_person(state: OverallState, config: RunnableConfig) -> dict[str, Any]:
    """Execute a multi-step web search and information extraction process.

    This function performs the following steps:
    1. Executes concurrent web searches using the Tavily API
    2. Deduplicates and formats the search results
    """

    # Get configuration
    configurable = Configuration.from_runnable_config(config)
    max_search_results = configurable.max_search_results

    # Web search
    search_tasks = []
    for query in state.search_queries:
        search_tasks.append(
            tavily_async_client.search(
                query,
                days=360,
                max_results=max_search_results,
                include_raw_content=True,
                topic="general",
            )
        )

    # Execute all searches concurrently
    search_docs = await asyncio.gather(*search_tasks)

    # Deduplicate and format sources
    source_str = deduplicate_and_format_sources(
        search_docs, max_tokens_per_source=1000, include_raw_content=True
    )

    # Generate structured notes relevant to the extraction schema
    p = INFO_PROMPT.format(
        info=json.dumps(state.extraction_schema, indent=2),
        content=source_str,
        people=state.person,
        user_notes=state.user_notes,
    )
    result = await claude_3_5_sonnet.ainvoke(p)
    return {"completed_notes": [str(result.content)]}


async def reflection(state: OverallState, config: RunnableConfig) -> dict[str, Any]:
    """Analyze completed research notes and determine if additional research is needed.
    
    This function performs the following steps:
    1. Takes the completed research notes from the state
    2. Uses the REFLECTION_PROMPT to analyze them against the extraction schema
    3. Returns a structured assessment with a decision on whether to continue or conclude
    """
    
    # Get the structured LLM for reflection output
    structured_llm = claude_3_5_sonnet.with_structured_output(ReflectionOutput)
    
    # Format person information for the prompt
    person_str = f"Email: {state.person.email}"
    if state.person.name:
        person_str += f", Name: {state.person.name}"
    if state.person.linkedin:
        person_str += f", LinkedIn: {state.person.linkedin}"
    if state.person.role:
        person_str += f", Role: {state.person.role}"
    if state.person.company:
        person_str += f", Company: {state.person.company}"
    
    # Format completed notes
    notes_str = "\n\n".join(state.completed_notes) if state.completed_notes else "No research notes available yet."
    
    # Create the reflection prompt
    reflection_prompt = REFLECTION_PROMPT.format(
        person=person_str,
        completed_notes=notes_str,
        extraction_schema=json.dumps(state.extraction_schema, indent=2)
    )
    
    # Get the reflection analysis
    reflection_result = await structured_llm.ainvoke(reflection_prompt)
    
    # Return the reflection analysis as part of the state
    return {
        "reflection_output": reflection_result.model_dump(),
        "research_decision": reflection_result.research_decision,
        "extracted_info": reflection_result.extracted_info,
        "missing_information": reflection_result.missing_information
    }

# Add nodes and edges
builder = StateGraph(
    OverallState,
    input=InputState,
    output=OutputState,
    config_schema=Configuration,
)
builder.add_node("generate_queries", generate_queries)
builder.add_node("research_person", research_person)
builder.add_node("reflection", reflection)

builder.add_edge(START, "generate_queries")
builder.add_edge("generate_queries", "research_person")
builder.add_edge("research_person", "reflection")

# Add conditional logic based on reflection decision
def should_continue_research(state: OverallState) -> Literal["generate_queries", "__end__"]:
    """Determine whether to continue research or end based on reflection decision."""
    if state.research_decision == "CONTINUE":
        return "generate_queries"
    else:
        return "__end__"

builder.add_conditional_edges(
    "reflection",
    should_continue_research,
    {
        "generate_queries": "generate_queries",
        "__end__": END
    }
)

# Compile
graph = builder.compile()



