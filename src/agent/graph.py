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


class ReflectionDecision(BaseModel):
    """Structured output for reflection decision making."""
    
    years_of_experience: str = Field(
        description="Extracted years of experience or 'Not found'"
    )
    current_company: str = Field(
        description="Extracted current company or 'Not found'"
    )
    role: str = Field(
        description="Extracted current role or 'Not found'"
    )
    prior_companies: str = Field(
        description="Extracted prior companies or 'Not found'"
    )
    completeness_rate: str = Field(
        description="Assessment of research completeness"
    )
    missing_information: str = Field(
        description="List of missing information"
    )
    continue_research: bool = Field(
        description="Whether to continue research (True) or stop (False)"
    )
    reasoning: str = Field(
        description="Detailed reasoning for the decision"
    )
    search_suggestions: str = Field(
        description="Suggested search terms if continuing research"
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
    """Evaluate research completeness and decide whether to continue research.
    
    This function:
    1. Takes research notes and converts them to structured format
    2. Evaluates completeness against required information
    3. Returns decision on whether to continue research
    """
    
    # Get configuration
    configurable = Configuration.from_runnable_config(config)
    max_reflection_steps = configurable.max_reflection_steps
    
    # Check if we've reached max reflection steps
    current_reflection_count = len(state.completed_notes) - 1  # Subtract 1 for initial research
    if current_reflection_count >= max_reflection_steps:
        # Force stop if max reflections reached
        return {
            "continue_research": False,
            "reflection_reasoning": f"Maximum reflection steps ({max_reflection_steps}) reached."
        }
    
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
    
    # Format all research notes
    all_notes = format_all_notes(state.completed_notes)
    
    # Create reflection prompt
    reflection_prompt = REFLECTION_PROMPT.format(
        person=person_str,
        info=json.dumps(state.extraction_schema, indent=2),
        research_notes=all_notes
    )
    
    # Use structured output for reliable decision making
    structured_llm = claude_3_5_sonnet.with_structured_output(ReflectionDecision)
    
    # Get reflection decision
    reflection_result = await structured_llm.ainvoke(reflection_prompt)
    
    # Return state updates based on reflection decision
    return {
        "continue_research": reflection_result.continue_research,
        "reflection_reasoning": reflection_result.reasoning,
        "extracted_info": {
            "years_of_experience": reflection_result.years_of_experience,
            "current_company": reflection_result.current_company,
            "role": reflection_result.role,
            "prior_companies": reflection_result.prior_companies
        },
        "completeness_assessment": {
            "rate": reflection_result.completeness_rate,
            "missing": reflection_result.missing_information,
            "suggestions": reflection_result.search_suggestions
        }
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

# Compile
graph = builder.compile()


