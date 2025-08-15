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
    """Structured output from reflection analysis."""
    
    years_of_experience: int | None = Field(
        default=None,
        description="Total years of professional experience"
    )
    
    current_company: str | None = Field(
        default=None,
        description="Name of the current company where the person works"
    )
    
    current_role: str | None = Field(
        default=None,
        description="Current job title or position"
    )
    
    prior_companies: list[str] = Field(
        default_factory=list,
        description="List of previous companies the person has worked at"
    )
    
    is_satisfactory: bool = Field(
        default=False,
        description="Whether the research results are satisfactory and complete"
    )
    
    missing_information: list[str] = Field(
        default_factory=list,
        description="List of specific missing information that should be searched for"
    )
    
    should_continue_research: bool = Field(
        default=True,
        description="Whether to continue the research process or finish"
    )
    
    reasoning: str = Field(
        description="Detailed reasoning for the decision to continue or stop research"
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
    """Analyze research notes and determine if more research is needed.
    
    This function:
    1. Parses completed notes into structured format
    2. Assesses completeness of information
    3. Decides whether to continue research based on quality and iteration count
    """
    
    # Get configuration
    configurable = Configuration.from_runnable_config(config)
    max_reflection_steps = configurable.max_reflection_steps
    
    # Calculate current reflection iteration (based on number of completed notes)
    reflection_iteration = len(state.completed_notes)
    
    # Format all completed notes
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
    
    # Format reflection prompt
    reflection_prompt = REFLECTION_PROMPT.format(
        person=person_str,
        completed_notes=formatted_notes,
        extraction_schema=json.dumps(state.extraction_schema, indent=2),
        reflection_iteration=reflection_iteration,
        max_reflection_steps=max_reflection_steps
    )
    
    # Get structured reflection output
    reflection_result = cast(
        ReflectionOutput,
        structured_llm.invoke(
            [
                {
                    "role": "system",
                    "content": "You are a research quality assessor. Analyze the research notes and provide a structured assessment.",
                },
                {
                    "role": "user",
                    "content": reflection_prompt,
                },
            ]
        ),
    )
    
    # Check if we've reached max reflection steps
    if reflection_iteration >= max_reflection_steps:
        reflection_result.should_continue_research = False
        if not reflection_result.reasoning:
            reflection_result.reasoning = f"Reached maximum reflection iterations ({max_reflection_steps}). Stopping research."
    
    # Convert Pydantic model to dict for state update
    return {
        "years_of_experience": reflection_result.years_of_experience,
        "current_company": reflection_result.current_company,
        "current_role": reflection_result.current_role,
        "prior_companies": reflection_result.prior_companies,
        "is_satisfactory": reflection_result.is_satisfactory,
        "missing_information": reflection_result.missing_information,
        "should_continue_research": reflection_result.should_continue_research,
        "reasoning": reflection_result.reasoning,
    }

# Define routing function for conditional edge
def should_continue(state: OverallState) -> Literal["generate_queries", "__end__"]:
    """Determine whether to continue research or end based on reflection results."""
    if state.should_continue_research:
        return "generate_queries"
    else:
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

builder.add_edge(START, "generate_queries")
builder.add_edge("generate_queries", "research_person")
builder.add_edge("research_person", "reflection")
builder.add_conditional_edges(
    "reflection",
    should_continue,
    {
        "generate_queries": "generate_queries",
        "__end__": END,
    }
)

# Compile
graph = builder.compile()



