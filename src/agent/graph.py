import asyncio
from typing import cast, Any, Literal, List
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
    """Structured output for the reflection step."""
    
    years_experience: int = Field(
        description="Total years of professional experience (best estimate as integer)",
        default=0
    )
    current_company: str = Field(
        description="Name of the current company where the person works",
        default=""
    )
    current_role: str = Field(
        description="Current job title or position",
        default=""
    )
    prior_companies: List[str] = Field(
        description="List of previous companies the person has worked at",
        default_factory=list
    )
    reflection_notes: str = Field(
        description="Analysis of information completeness and quality"
    )
    satisfaction_score: float = Field(
        description="Score from 0.0 to 1.0 indicating satisfaction with information completeness",
        ge=0.0,
        le=1.0
    )
    decision: Literal["continue", "complete"] = Field(
        description="Decision whether to continue research or mark as complete"
    )
    missing_information: List[str] = Field(
        description="List of specific information that is still missing or unclear",
        default_factory=list
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
    """Reflect on the research notes to extract structured information and decide next steps.
    
    This function:
    1. Formats all completed research notes
    2. Uses structured output to extract key professional information
    3. Evaluates the completeness and quality of information
    4. Decides whether to continue research or mark as complete
    """
    
    # Format all completed notes into a single string
    formatted_notes = format_all_notes(state.completed_notes)
    
    # Create structured LLM for reflection output
    structured_llm = claude_3_5_sonnet.with_structured_output(ReflectionOutput)
    
    # Format person information for context
    person_str = f"Email: {state.person.email}"
    if state.person.name:
        person_str += f", Name: {state.person.name}"
    if state.person.company:
        person_str += f", Company: {state.person.company}"
    if state.person.role:
        person_str += f", Role: {state.person.role}"
    if state.person.linkedin:
        person_str += f", LinkedIn: {state.person.linkedin}"
    
    # Create the reflection prompt with the research notes
    reflection_prompt = REFLECTION_PROMPT.format(
        person=person_str,
        notes=formatted_notes
    )
    
    # Get structured reflection output
    reflection_result = cast(
        ReflectionOutput,
        structured_llm.invoke(
            [
                {
                    "role": "system",
                    "content": "You are an expert at extracting structured professional information from research notes and assessing information completeness.",
                },
                {
                    "role": "user",
                    "content": reflection_prompt,
                },
            ]
        ),
    )
    
    # Return the extracted information and decision as state updates
    # Note: The decision field is used by the routing function to determine next steps
    return {
        "years_experience": reflection_result.years_experience,
        "current_company": reflection_result.current_company,
        "current_role": reflection_result.current_role,
        "prior_companies": reflection_result.prior_companies,
        "reflection_notes": reflection_result.reflection_notes,
        "satisfaction_score": reflection_result.satisfaction_score,
        "decision": reflection_result.decision,  # This will be used for conditional routing
    }


def route_reflection(state: OverallState) -> Literal["generate_queries", "__end__"]:
    """Route based on the reflection decision.
    
    This function determines the next step based on the reflection's assessment:
    - If decision is 'continue': Route back to generate_queries to create new targeted queries
    - If decision is 'complete': Route to END to finish the process
    """
    # Check the decision from the reflection step
    decision = state.get("decision", None)
    
    if decision == "continue":
        # Need more research - go back to generate new queries based on what's missing
        return "generate_queries"
    else:
        # Satisfied with the information - end the process
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

# Add conditional edge from reflection node
# This creates the feedback loop: reflection can either go back to research_person or end
builder.add_conditional_edges(
    "reflection",
    route_reflection,
    {
        "research_person": "research_person",
        "__end__": END,
    }
)

# Compile
graph = builder.compile()







