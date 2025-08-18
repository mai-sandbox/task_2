"""Graph module for the people research agent workflow."""

import asyncio
import json
from typing import Any, Literal, cast

from langchain_anthropic import ChatAnthropic
from langchain_core import InMemoryRateLimiter
from langchain_core.runnables import RunnableConfig
from langgraph import END, START, StateGraph
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
    queries: list[str] = Field(
        description="List of search queries.",
    )


class ReflectionOutput(BaseModel):
    """Structured output from the reflection step."""

    years_of_experience: int | None = Field(
        default=None, description="Total years of professional experience"
    )
    current_company: str | None = Field(
        default=None, description="Current company where the person works"
    )
    role: str | None = Field(default=None, description="Current role or job title")
    prior_companies: list[str] = Field(
        default_factory=list, description="List of previous companies worked at"
    )
    continue_research: bool = Field(
        description="Whether to continue research (True) or finish (False)"
    )
    reasoning: str = Field(
        description="Explanation for the decision to continue or finish research"
    )
    missing_information: list[str] = Field(
        default_factory=list,
        description="List of specific information that is missing if research should continue",
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


def reflection(state: OverallState, config: RunnableConfig) -> dict[str, Any]:
    """Analyze research notes, extract structured information, and decide next steps.

    This function:
    1. Takes completed research notes from state
    2. Uses structured LLM output to extract key person information
    3. Evaluates the completeness of gathered information
    4. Returns structured data and decision to continue or finish
    """
    # Format all completed notes into a single string
    formatted_notes = format_all_notes(state.completed_notes)

    # Format person information for the prompt
    person_str = f"Email: {state.person.email}"
    if state.person.name:
        person_str += f", Name: {state.person.name}"
    if state.person.company:
        person_str += f", Company: {state.person.company}"
    if state.person.role:
        person_str += f", Role: {state.person.role}"

    # Create structured LLM for reflection output
    structured_llm = claude_3_5_sonnet.with_structured_output(ReflectionOutput)

    # Format the reflection prompt
    reflection_prompt = REFLECTION_PROMPT.format(
        person=person_str, completed_notes=formatted_notes
    )

    # Get structured reflection output
    reflection_result = cast(
        ReflectionOutput,
        structured_llm.invoke(
            [
                {
                    "role": "system",
                    "content": "You are a research analyst evaluating the completeness of research notes and extracting structured information.",
                },
                {
                    "role": "user",
                    "content": reflection_prompt,
                },
            ]
        ),
    )

    # Prepare the state update with extracted information
    state_update = {
        "years_of_experience": reflection_result.years_of_experience,
        "current_company": reflection_result.current_company,
        "role": reflection_result.role,
        "prior_companies": reflection_result.prior_companies,
    }

    # Store the reflection decision in state for conditional routing
    # We'll use this in the routing function
    state_update["_continue_research"] = reflection_result.continue_research
    state_update["_reflection_reasoning"] = reflection_result.reasoning
    state_update["_missing_information"] = reflection_result.missing_information

    return state_update


def should_continue_research(state: OverallState) -> Literal["generate_queries", "END"]:
    """Conditional routing function that decides whether to continue research or finish.

    Examines the reflection output stored in state and returns:
    - 'generate_queries' if more research is needed (to regenerate search queries)
    - 'END' if the research is satisfactory
    """
    # Check the continue_research flag set by the reflection function
    if state._continue_research:
        # More research is needed - regenerate queries and continue
        return "generate_queries"
    else:
        # Research is satisfactory - end the workflow
        return END


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
# This will call should_continue_research to decide the next step
builder.add_conditional_edges(
    "reflection",
    should_continue_research,
    {
        "generate_queries": "generate_queries",  # If more research needed, go back to generate queries
        END: END,  # If satisfactory, end the workflow
    },
)

# Compile
graph = builder.compile()

