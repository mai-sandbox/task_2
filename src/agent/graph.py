import asyncio
import json
from typing import Any, Literal, cast

from langchain_anthropic import ChatAnthropic
from langchain_core.rate_limiters import InMemoryRateLimiter
from langchain_core.runnables import RunnableConfig
from langgraph.constants import END, START
from langgraph.graph import StateGraph
from pydantic import BaseModel, Field
from tavily import AsyncTavilyClient

from agent.configuration import Configuration
from agent.prompts import (
    INFO_PROMPT,
    QUERY_WRITER_PROMPT,
    REFLECTION_PROMPT,
)
from agent.state import (
    InputState,
    OutputState,
    OverallState,
    ReflectionDecision,
    ReflectionResult,
)
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
    # If this is a follow-up iteration and we have additional queries from reflection, use those
    if state.reflection_result and state.reflection_result.additional_queries:
        return {"search_queries": state.reflection_result.additional_queries}
    
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
    """Reflect on the research notes and determine if additional research is needed.
    
    This function:
    1. Analyzes all completed research notes
    2. Extracts structured information about the person
    3. Determines if the information is complete or if more research is needed
    4. Generates additional search queries if needed
    """
    # Format all notes for analysis
    all_notes = format_all_notes(state.completed_notes)
    
    # Format person information for context
    person_str = f"Email: {state.person.email}"
    if state.person.name:
        person_str += f" Name: {state.person.name}"
    if state.person.linkedin:
        person_str += f" LinkedIn URL: {state.person.linkedin}"
    if state.person.role:
        person_str += f" Role: {state.person.role}"
    if state.person.company:
        person_str += f" Company: {state.person.company}"
    
    # Generate structured reflection
    structured_llm = claude_3_5_sonnet.with_structured_output(ReflectionResult)
    
    reflection_prompt = REFLECTION_PROMPT.format(
        person=person_str,
        notes=all_notes
    )
    
    reflection_result = cast(
        ReflectionResult,
        await structured_llm.ainvoke([
            {"role": "system", "content": reflection_prompt},
            {
                "role": "user", 
                "content": "Please analyze the research notes and provide structured information with your assessment."
            }
        ])
    )
    
    # Update iteration count
    new_iteration_count = state.iteration_count + 1
    
    return {
        "reflection_result": reflection_result,
        "iteration_count": new_iteration_count
    }


def should_continue_research(state: OverallState) -> Literal["research_person", "format_output"]:
    """Determine if more research is needed based on reflection results."""
    if not state.reflection_result:
        return "format_output"
    
    # Limit to maximum 3 iterations to prevent infinite loops
    if state.iteration_count >= 3:
        return "format_output"
    
    # Continue research if reflection suggests it and we haven't hit limits
    if state.reflection_result.decision == ReflectionDecision.SEARCH_MORE:
        return "research_person"
    
    return "format_output"


def format_output(state: OverallState) -> dict[str, Any]:
    """Format the final output with structured information."""
    # Get structured info from reflection result, or create basic fallback
    if state.reflection_result:
        structured_info = state.reflection_result.structured_info
        final_reasoning = state.reflection_result.reasoning
    else:
        # Fallback if no reflection was performed
        from agent.state import StructuredPersonInfo
        structured_info = StructuredPersonInfo(
            current_company=state.person.company,
            current_role=state.person.role
        )
        final_reasoning = "Research completed without reflection analysis."
    
    # Format all notes
    all_notes = format_all_notes(state.completed_notes)
    
    return {
        "structured_info": structured_info,
        "all_notes": all_notes,
        "final_reasoning": final_reasoning
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
builder.add_node("format_output", format_output)

# Initial flow: generate queries -> research -> reflection
builder.add_edge(START, "generate_queries")
builder.add_edge("generate_queries", "research_person")
builder.add_edge("research_person", "reflection")

# Conditional edge from reflection: either continue research or finish
builder.add_conditional_edges(
    "reflection",
    should_continue_research,
    {
        "research_person": "generate_queries",  # Generate new queries for additional research
        "format_output": "format_output"
    }
)

# Final edge to END
builder.add_edge("format_output", END)

# Compile
graph = builder.compile()
