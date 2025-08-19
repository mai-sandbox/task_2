import asyncio
import json
from typing import Any, Literal, cast

from langchain_anthropic import ChatAnthropic
from langchain_core.rate_limiters import InMemoryRateLimiter
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field
from tavily import AsyncTavilyClient

from agent.configuration import Configuration
from agent.prompts import (
    INFO_PROMPT,
    QUERY_WRITER_PROMPT,
    REFLECTION_PROMPT,
)
from agent.state import InputState, OutputState, OverallState, ReflectionResult
from agent.utils import deduplicate_and_format_sources, format_all_notes

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
    """Model for structured search queries."""
    
    queries: list[str] = Field(
        description="List of search queries.",
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
    """Reflect on the gathered information and determine if more searches are needed."""
    # Format person information
    person_str = f"Email: {state.person.email}"
    if state.person.name:
        person_str += f", Name: {state.person.name}"
    if state.person.linkedin:
        person_str += f", LinkedIn: {state.person.linkedin}"
    if state.person.company:
        person_str += f", Company: {state.person.company}"
    if state.person.role:
        person_str += f", Role: {state.person.role}"
    
    # Combine all notes
    all_notes = format_all_notes(state.completed_notes)
    
    # Create structured LLM
    structured_llm = claude_3_5_sonnet.with_structured_output(ReflectionResult)
    
    # Format reflection prompt
    reflection_prompt = REFLECTION_PROMPT.format(
        person=person_str,
        notes=all_notes,
        schema=json.dumps(state.extraction_schema, indent=2)
    )
    
    # Get reflection result
    reflection_result = await structured_llm.ainvoke([
        {"role": "system", "content": reflection_prompt},
        {"role": "user", "content": "Please analyze the research notes and provide a structured evaluation."}
    ])
    
    return {"reflection_result": reflection_result}


def should_continue_search(state: OverallState) -> Literal["research_person", "format_output"]:
    """Decide whether to continue searching or format the final output."""
    if (state.reflection_result and 
        state.reflection_result.should_redo_search and 
        state.search_iteration < state.max_search_iterations):
        return "research_person"
    else:
        return "format_output"


def increment_iteration(state: OverallState, config: RunnableConfig) -> dict[str, Any]:
    """Increment the search iteration counter and update queries."""
    new_queries = []
    if state.reflection_result and state.reflection_result.additional_search_queries:
        new_queries = state.reflection_result.additional_search_queries
    
    return {
        "search_iteration": state.search_iteration + 1,
        "search_queries": new_queries
    }


def format_output(state: OverallState, config: RunnableConfig) -> dict[str, Any]:
    """Format the final output for the user."""
    all_notes = format_all_notes(state.completed_notes)
    
    return {
        "structured_info": state.reflection_result.structured_info,
        "reflection_result": state.reflection_result,
        "all_notes": all_notes
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
builder.add_node("increment_iteration", increment_iteration)
builder.add_node("format_output", format_output)

# Add edges
builder.add_edge(START, "generate_queries")
builder.add_edge("generate_queries", "research_person")
builder.add_edge("research_person", "reflection")

# Add conditional edge after reflection
builder.add_conditional_edges(
    "reflection",
    should_continue_search,
    {
        "research_person": "increment_iteration",
        "format_output": "format_output"
    }
)

builder.add_edge("increment_iteration", "research_person")
builder.add_edge("format_output", END)

# Compile
graph = builder.compile()
