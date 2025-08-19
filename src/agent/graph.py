import asyncio
from typing import cast, Any, Literal, Dict
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


class StructuredPersonInfo(BaseModel):
    """Structured information about a person's professional background."""
    years_of_experience: str = Field(
        default="Not found",
        description="Total years of professional experience"
    )
    current_company: str = Field(
        default="Not found",
        description="Name of the current employer/company"
    )
    current_role: str = Field(
        default="Not found",
        description="Current job title or position"
    )
    prior_companies: list[str] = Field(
        default_factory=list,
        description="List of previous companies with roles and duration"
    )
    education: str = Field(
        default="Not found",
        description="Educational background"
    )
    skills: list[str] = Field(
        default_factory=list,
        description="Key technical and professional skills"
    )
    notable_achievements: list[str] = Field(
        default_factory=list,
        description="Significant accomplishments or projects"
    )


class ReflectionDecision(BaseModel):
    """Decision from the reflection step."""
    is_satisfactory: bool = Field(
        description="Whether the research is satisfactory and complete"
    )
    missing_information: list[str] = Field(
        default_factory=list,
        description="List of missing critical information"
    )
    reasoning: str = Field(
        description="Reasoning for the decision to continue or redo research"
    )
    suggested_queries: list[str] = Field(
        default_factory=list,
        description="Additional search queries if research needs to continue"
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
    """Reflect on the research results and decide whether to continue or conclude.
    
    This function:
    1. Structures the collected notes into the required format
    2. Evaluates if the information is satisfactory
    3. Identifies missing information
    4. Decides whether to redo the research or conclude
    """
    
    # Format all collected notes
    formatted_notes = format_all_notes(state.completed_notes)
    
    # First, extract structured information from the notes
    structured_llm = claude_3_5_sonnet.with_structured_output(StructuredPersonInfo)
    
    extraction_prompt = f"""Based on the following research notes about {state.person.name or state.person.email}, 
    extract and structure the professional information. If information is not found, indicate "Not found".
    
    Research Notes:
    {formatted_notes}
    
    Please extract:
    - Years of experience (calculate if possible from career history)
    - Current company and role
    - Prior companies with roles and duration
    - Education background
    - Key skills
    - Notable achievements
    """
    
    structured_info = await structured_llm.ainvoke(extraction_prompt)
    
    # Now evaluate the completeness and quality of the research
    reflection_llm = claude_3_5_sonnet.with_structured_output(ReflectionDecision)
    
    reflection_prompt = REFLECTION_PROMPT.format(
        person=state.person.dict(),
        structured_info=structured_info.dict(),
        raw_notes=formatted_notes,
        user_notes=state.user_notes or "No specific requirements provided"
    )
    
    reflection_result = await reflection_llm.ainvoke(reflection_prompt)
    
    # Prepare the state update
    state_update = {
        "structured_output": structured_info.dict(),
        "reflection_result": reflection_result.dict()
    }
    
    # If research is not satisfactory and we have suggested queries, add them
    if not reflection_result.is_satisfactory and reflection_result.suggested_queries:
        state_update["search_queries"] = reflection_result.suggested_queries
    
    return state_update

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



