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


def reflection(state: OverallState, config: RunnableConfig) -> dict[str, Any]:
    """Analyze completed research notes and extract structured information.
    
    This function:
    1. Processes all completed research notes
    2. Extracts structured person information (experience, companies, roles)
    3. Evaluates research completeness
    4. Determines if more research is needed
    5. Provides reasoning for the decision
    """
    # Format the completed notes for analysis
    formatted_notes = format_all_notes(state.completed_notes)
    
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
    
    # Create structured LLM with ReflectionResult output
    structured_llm = claude_3_5_sonnet.with_structured_output(ReflectionResult)
    
    # Format the reflection prompt
    reflection_prompt = REFLECTION_PROMPT.format(
        person=person_str,
        completed_notes=formatted_notes,
        user_notes=state.user_notes or "No additional notes provided"
    )
    
    # Get structured reflection result
    reflection_result = cast(
        ReflectionResult,
        structured_llm.invoke(
            [
                {
                    "role": "system",
                    "content": "You are an expert research analyst specializing in professional background analysis.",
                },
                {
                    "role": "user",
                    "content": reflection_prompt,
                },
            ]
        ),
    )
    
    # Return the reflection result to update the state
    return {"reflection_result": reflection_result}


def should_continue_research(state: OverallState) -> Literal["generate_queries", "end"]:
    """Determine whether to continue research or end based on reflection results.
    
    This routing function checks the reflection_result to decide:
    - If needs_more_research is True: Route back to generate_queries for another iteration
    - If needs_more_research is False: Route to END to complete the workflow
    """
    if state.reflection_result and state.reflection_result.needs_more_research:
        return "generate_queries"
    return "end"


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
# Routes to generate_queries if more research needed, or END if complete
builder.add_conditional_edges(
    "reflection",
    should_continue_research,
    {
        "generate_queries": "generate_queries",
        "end": END
    }
)

# Compile
graph = builder.compile()




