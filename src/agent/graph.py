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
    structured_info: dict[str, Any] = Field(
        description="Structured information extracted from research notes matching the extraction schema"
    )
    completeness_score: float = Field(
        description="Score from 0-1 indicating how complete the extracted information is"
    )
    missing_information: list[str] = Field(
        description="List of information categories that are missing or incomplete"
    )
    should_continue: bool = Field(
        description="Boolean indicating whether additional research should be conducted"
    )
    reasoning: str = Field(
        description="Explanation for the completeness assessment and decision to continue or finish"
    )



def generate_queries(state: OverallState, config: RunnableConfig) -> dict[str, Any]:
    """Generate search queries based on the user input and extraction schema."""
    # Get configuration
    configurable = Configuration.from_runnable_config(config)
    max_search_queries = configurable.max_search_queries

    # Generate search queries
    structured_llm = claude_3_5_sonnet.with_structured_output(Queries)

    # Format system instructions
    person_str = f"Email: {state.person.email}"
    if state.person.name:
        person_str += f" Name: {state.person.name}"
    if state.person.linkedin:
        person_str += f" LinkedIn URL: {state.person.linkedin}"
    if state.person.role:
        person_str += f" Role: {state.person.role}"
    if state.person.company:
        person_str += f" Company: {state.person.company}"

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
    
    This function performs reflection on the research notes by:
    1. Converting notes to structured format matching the extraction schema
    2. Evaluating information completeness on a 0-1 scale
    3. Identifying missing information
    4. Deciding whether to continue research or finish
    5. Providing reasoning for the decision
    """
    
    # Use Claude 3.5 Sonnet with structured output for reflection
    structured_llm = claude_3_5_sonnet.with_structured_output(ReflectionOutput)
    
    # Format person information for the prompt
    person_str = f"Email: {state.person.email}"
    if state.person.name:
        person_str += f", Name: {state.person.name}"
    if state.person.company:
        person_str += f", Company: {state.person.company}"
    if state.person.role:
        person_str += f", Role: {state.person.role}"
    if state.person.linkedin:
        person_str += f", LinkedIn: {state.person.linkedin}"
    
    # Format completed notes for analysis
    notes_str = format_all_notes(state.completed_notes)
    
    # Create reflection prompt
    reflection_instructions = REFLECTION_PROMPT.format(
        person=person_str,
        completed_notes=notes_str,
        extraction_schema=json.dumps(state.extraction_schema, indent=2)
    )
    
    # Execute reflection analysis
    reflection_result = cast(
        ReflectionOutput,
        await structured_llm.ainvoke(
            [
                {
                    "role": "system",
                    "content": reflection_instructions,
                },
                {
                    "role": "user", 
                    "content": "Please analyze the research notes and provide your structured reflection according to the instructions.",
                },
            ]
        ),
    )
    
    # Return results in the format expected by the graph state
    return {
        "structured_info": reflection_result.structured_info,
        "completeness_score": reflection_result.completeness_score,
        "missing_information": reflection_result.missing_information,
        "should_continue": reflection_result.should_continue,
        "reasoning": reflection_result.reasoning,
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

# Add conditional edge from reflection
def should_continue_research(state: OverallState) -> Literal["generate_queries", "END"]:
    """Determine whether to continue research or end based on reflection results."""
    if state.should_continue:
        return "generate_queries"
    else:
        return "END"

builder.add_conditional_edges(
    "reflection",
    should_continue_research,
    {
        "generate_queries": "generate_queries",
        "END": END,
    },
)

# Compile
graph = builder.compile()




