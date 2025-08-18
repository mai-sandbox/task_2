import asyncio
from typing import cast, Any, Literal
import json

from tavily import AsyncTavilyClient
from langchain_anthropic import ChatAnthropic
# from langchain_core import InMemoryRateLimiter  # Not available in current version
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, START, END
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

# Rate limiter not available in current langchain_core version
# rate_limiter = InMemoryRateLimiter(
#     requests_per_second=4,
#     check_every_n_seconds=0.1,
#     max_bucket_size=10,  # Controls the maximum burst size.
# )
claude_3_5_sonnet = ChatAnthropic(
    model="claude-3-5-sonnet-latest", temperature=0
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


class ReflectionDecision(BaseModel):
    decision: Literal["STOP", "CONTINUE"] = Field(
        description="Whether to stop research (STOP) or continue with more queries (CONTINUE)"
    )
    structured_info: dict[str, Any] = Field(
        description="Extracted information in structured format matching the schema"
    )
    missing_info: list[str] = Field(
        description="List of missing or unclear information that needs to be found"
    )
    reasoning: str = Field(
        description="Detailed explanation of the decision and what information is complete/missing"
    )


async def reflection(state: OverallState, config: RunnableConfig) -> dict[str, Any]:
    """Evaluate research completeness and decide whether to continue or stop.
    
    This function:
    1. Takes completed_notes and converts to structured format
    2. Evaluates information completeness against required fields
    3. Determines if research is satisfactory or needs continuation
    4. Returns decision with reasoning and missing information
    """
    
    # Format completed notes for evaluation
    all_notes = format_all_notes(state.completed_notes)
    
    # Format person information
    person_str = f"Email: {state.person.email}"
    if state.person.name:
        person_str += f", Name: {state.person.name}"
    if state.person.linkedin:
        person_str += f", LinkedIn: {state.person.linkedin}"
    if state.person.role:
        person_str += f", Role: {state.person.role}"
    if state.person.company:
        person_str += f", Company: {state.person.company}"
    
    # Create structured LLM for reflection
    structured_llm = claude_3_5_sonnet.with_structured_output(ReflectionDecision)
    
    # Format reflection prompt
    reflection_prompt = REFLECTION_PROMPT.format(
        person=person_str,
        info=json.dumps(state.extraction_schema, indent=2),
        completed_notes=all_notes
    )
    
    # Get reflection decision
    reflection_result = await structured_llm.ainvoke(reflection_prompt)
    
    # If decision is STOP, we're done - return the structured information
    if reflection_result.decision == "STOP":
        return {
            "research_complete": True,
            "structured_info": reflection_result.structured_info,
            "missing_info": reflection_result.missing_info,
            "reflection_reasoning": reflection_result.reasoning
        }
    
    # If decision is CONTINUE, prepare for another research iteration
    # Clear previous search queries to generate new ones
    return {
        "research_complete": False,
        "search_queries": [],  # Reset queries to trigger new generation
        "missing_info": reflection_result.missing_info,
        "reflection_reasoning": reflection_result.reasoning
    }


def should_continue_research(state: OverallState) -> Literal["generate_queries", "__end__"]:
    """Conditional edge function to determine workflow continuation.
    
    Returns:
        "generate_queries": If research should continue (more information needed)
        "__end__": If research is complete (sufficient information gathered)
    """
    # Check if research is marked as complete by the reflection step
    if hasattr(state, 'research_complete') and getattr(state, 'research_complete', False):
        return "__end__"
    
    # If we have search queries that need to be processed, continue research
    if state.search_queries and len(state.search_queries) > 0:
        return "generate_queries"
    
    # Default to ending if no clear continuation signal
    return "__end__"


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
    {
        "generate_queries": "generate_queries",  # Continue research - loop back
        "__end__": END,  # Stop research - end workflow
    }
)

# Compile
graph = builder.compile()






