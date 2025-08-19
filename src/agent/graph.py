import asyncio
from typing import cast, Any, Literal
import json

from tavily import AsyncTavilyClient
from langchain_anthropic import ChatAnthropic
from langchain_core import InMemoryRateLimiter
from langchain_core.runnables import RunnableConfig
from langgraph import START, END, StateGraph
from pydantic import BaseModel, Field
from typing import List, Optional

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
    
    years_experience: Optional[int] = Field(
        default=None,
        description="Total years of professional experience"
    )
    current_company: Optional[str] = Field(
        default=None,
        description="Current company where the person works"
    )
    current_role: Optional[str] = Field(
        default=None,
        description="Current job title or position"
    )
    prior_companies: List[str] = Field(
        default_factory=list,
        description="List of previous companies the person has worked at"
    )
    reflection_decision: Literal["continue", "finish"] = Field(
        description="Decision whether to continue research or finish"
    )
    reflection_reasoning: str = Field(
        description="Reasoning behind the reflection decision"
    )
    extracted_info: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional extracted information from research"
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


def reflection(state: OverallState, config: RunnableConfig) -> dict[str, Any]:
    """Analyze completed research notes and decide whether to continue or finish.
    
    This function:
    1. Reviews all completed research notes
    2. Extracts structured information (years of experience, companies, roles)
    3. Evaluates if sufficient information has been gathered
    4. Returns a decision to continue research or finish
    """
    
    # Format all completed notes for analysis
    formatted_notes = format_all_notes(state.completed_notes)
    
    # Format person information
    person_str = f"Email: {state.person.email}"
    if state.person.name:
        person_str += f", Name: {state.person.name}"
    if state.person.company:
        person_str += f", Company: {state.person.company}"
    if state.person.role:
        person_str += f", Role: {state.person.role}"
    if state.person.linkedin:
        person_str += f", LinkedIn: {state.person.linkedin}"
    
    # Create structured LLM for reflection
    structured_llm = claude_3_5_sonnet.with_structured_output(ReflectionOutput)
    
    # Format the reflection prompt
    reflection_prompt = REFLECTION_PROMPT.format(
        person=person_str,
        notes=formatted_notes,
        schema=json.dumps(state.extraction_schema, indent=2)
    )
    
    # Get structured reflection output
    reflection_result = cast(
        ReflectionOutput,
        structured_llm.invoke(
            [
                {
                    "role": "system",
                    "content": "You are a research analyst extracting structured information and evaluating research completeness.",
                },
                {
                    "role": "user",
                    "content": reflection_prompt,
                },
            ]
        ),
    )
    
    # Prepare the output state update
    output_update = {
        "years_experience": reflection_result.years_experience,
        "current_company": reflection_result.current_company,
        "current_role": reflection_result.current_role,
        "prior_companies": reflection_result.prior_companies,
        "reflection_decision": reflection_result.reflection_decision,
        "reflection_reasoning": reflection_result.reflection_reasoning,
        "extracted_info": reflection_result.extracted_info,
    }
    
    # Add any additional extracted information to the extracted_info field
    if reflection_result.extracted_info:
        output_update["extracted_info"].update(reflection_result.extracted_info)
    
    return output_update


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

# Add conditional edge from reflection node
def should_continue(state: OverallState) -> str:
    """Determine whether to continue research or finish based on reflection decision."""
    if state.reflection_decision == "continue":
        return "generate_queries"
    else:
        return END

builder.add_conditional_edges(
    "reflection",
    should_continue,
    {
        "generate_queries": "generate_queries",
        END: END,
    }
)

# Compile
graph = builder.compile()




