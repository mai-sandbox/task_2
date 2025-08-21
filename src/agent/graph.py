import asyncio
from typing import cast, Any, Literal, Optional
import json

from tavily import AsyncTavilyClient
from langchain_anthropic import ChatAnthropic
from langchain_core.rate_limiters import InMemoryRateLimiter
from langchain_core.runnables import RunnableConfig
from langgraph.graph import START, END, StateGraph
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


class ReflectionResult(BaseModel):
    years_of_experience: Optional[str] = Field(
        description="Total years of professional experience"
    )
    current_company: Optional[str] = Field(
        description="Current employer/company"
    )
    current_role: Optional[str] = Field(
        description="Current job title/role"
    )
    prior_companies: list[str] = Field(
        default_factory=list,
        description="List of previous employers"
    )
    missing_information: list[str] = Field(
        default_factory=list,
        description="List of missing information that should be searched"
    )
    is_satisfactory: bool = Field(
        description="Whether the extracted information is complete and satisfactory"
    )
    needs_additional_search: bool = Field(
        description="Whether additional searches are needed"
    )
    reasoning: str = Field(
        description="Reasoning for the decision to continue or stop research"
    )



def generate_queries(state: OverallState, config: RunnableConfig) -> dict[str, Any]:
    """Generate search queries based on the user input and extraction schema."""
    # Get configuration
    configurable = Configuration.from_runnable_config(config)
    max_search_queries = configurable.max_search_queries
    
    # Initialize extraction schema if not provided
    if not state.extraction_schema:
        extraction_schema = {
            "years_of_experience": "Total years of professional experience",
            "current_company": "Current employer/organization",
            "current_role": "Current job title or role",
            "prior_companies": "List of previous employers",
            "key_skills": "Notable skills or expertise areas",
            "career_timeline": "Career progression and timeline"
        }
    else:
        extraction_schema = state.extraction_schema

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
        info=json.dumps(extraction_schema, indent=2),
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
    return {
        "search_queries": query_list,
        "extraction_schema": extraction_schema
    }


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
    """Reflect on research notes to extract structured professional information.
    
    This function:
    1. Analyzes all completed research notes
    2. Extracts key professional information (experience, company, role, etc.)
    3. Determines if additional research is needed
    4. Returns structured reflection result
    """
    
    # Combine all notes into a single text
    all_notes = format_all_notes(state.completed_notes)
    
    # Create structured LLM with reflection output
    structured_llm = claude_3_5_sonnet.with_structured_output(ReflectionResult)
    
    # Format reflection prompt
    reflection_prompt = REFLECTION_PROMPT.format(notes=all_notes)
    
    # Get structured reflection result
    reflection_result = cast(
        ReflectionResult,
        await structured_llm.ainvoke([
            {"role": "system", "content": reflection_prompt},
            {
                "role": "user", 
                "content": "Please analyze the research notes and provide structured professional information about the person."
            }
        ])
    )
    
    return {
        "reflection_result": reflection_result,
        "search_iteration": state.search_iteration + 1
    }


def should_continue_research(state: OverallState) -> Literal["research_person", "end"]:
    """Determine if additional research iterations are needed.
    
    This function checks:
    1. If reflection indicates more research is needed
    2. If we haven't exceeded maximum iterations (safety limit)
    3. Returns the next node to execute
    """
    MAX_ITERATIONS = 3  # Safety limit to prevent infinite loops
    
    # If no reflection result yet, we need to continue
    if not state.reflection_result:
        return "research_person"
    
    # If we've reached max iterations, stop
    if state.search_iteration >= MAX_ITERATIONS:
        return "end"
    
    # Check if reflection indicates we need more research
    if state.reflection_result.needs_additional_search:
        return "research_person"
    
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
builder.add_conditional_edges(
    "reflection",
    should_continue_research,
    {
        "research_person": "generate_queries",  # Loop back to generate new queries
        "end": END
    }
)

# Compile
graph = builder.compile()
