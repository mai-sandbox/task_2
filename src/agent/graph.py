"""Main graph module for the people research agent.

This module implements the LangGraph workflow for researching people, including
query generation, web search, information extraction, and reflection capabilities.
"""

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
from agent.state import InputState, OutputState, OverallState
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
    """Pydantic model for structured query generation output."""

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


async def research_person(
    state: OverallState, config: RunnableConfig
) -> dict[str, Any]:
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


class ReflectionOutput(BaseModel):
    """Structured output from the reflection analysis."""

    structured_data: dict[str, Any] = Field(
        description="Extracted structured person data"
    )
    completeness_assessment: str = Field(
        description="Assessment of information quality and completeness"
    )
    should_continue_research: bool = Field(
        description="Whether additional research is needed"
    )
    reasoning: str = Field(description="Detailed explanation of the decision")


async def reflection(state: OverallState, config: RunnableConfig) -> dict[str, Any]:
    """Analyze completed research notes and determine if additional research is needed.

    This function:
    1. Uses the REFLECTION_PROMPT to analyze research notes
    2. Extracts structured person data (years of experience, current company, role, prior companies)
    3. Assesses information completeness
    4. Decides whether to continue research with detailed reasoning
    5. Returns structured output and research continuation decision
    """
    try:
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
        formatted_notes = format_all_notes(state.completed_notes)

        # Create structured LLM for JSON output
        structured_llm = claude_3_5_sonnet.with_structured_output(ReflectionOutput)

        # Format the reflection prompt
        reflection_prompt = REFLECTION_PROMPT.format(
            person=person_str, completed_notes=formatted_notes
        )

        # Get reflection analysis
        reflection_result = await structured_llm.ainvoke(reflection_prompt)

        # Extract structured data and update state
        structured_data = reflection_result.structured_data
        reflection_notes = f"Assessment: {reflection_result.completeness_assessment}\n\nReasoning: {reflection_result.reasoning}"

        return {
            "reflection_notes": reflection_notes,
            "should_continue_research": reflection_result.should_continue_research,
            # Store structured data for potential output
            "completed_notes": [
                f"REFLECTION ANALYSIS:\n{reflection_notes}\n\nEXTRACTED DATA:\n{json.dumps(structured_data, indent=2)}"
            ],
        }

    except Exception as e:
        # Error handling - default to continuing research if reflection fails
        error_msg = (
            f"Reflection analysis failed: {str(e)}. Defaulting to continue research."
        )
        return {
            "reflection_notes": error_msg,
            "should_continue_research": True,
            "completed_notes": [f"REFLECTION ERROR: {error_msg}"],
        }


def should_continue_research(state: OverallState) -> Literal["generate_queries", "END"]:
    """Conditional edge function that determines whether to continue research or end.

    Routes based on the reflection analysis:
    - If should_continue_research is True: route back to "generate_queries" for another research iteration
    - If should_continue_research is False: route to "END" to complete the workflow

    Args:
        state: The current OverallState containing reflection analysis results

    Returns:
        "generate_queries" if more research is needed, "END" if research is complete
    """
    if state.should_continue_research:
        return "generate_queries"
    else:
        return "END"


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

# Define the workflow edges
builder.add_edge(START, "generate_queries")
builder.add_edge("generate_queries", "research_person")
builder.add_edge("research_person", "reflection")

# Add conditional edge from reflection
builder.add_conditional_edges(
    "reflection",
    should_continue_research,
    {"generate_queries": "generate_queries", "END": END},
)

# Compile
graph = builder.compile()
