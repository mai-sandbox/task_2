import asyncio
from typing import cast, Any, Literal
import json

from tavily import AsyncTavilyClient
from langchain_anthropic import ChatAnthropic
# Rate limiter import removed - not available in current langchain-core version
from langchain_core.runnables import RunnableConfig
from langgraph.graph import START, END, StateGraph
from pydantic import BaseModel, Field

from src.agent.configuration import Configuration
from src.agent.state import InputState, OutputState, OverallState
from src.agent.utils import deduplicate_and_format_sources, format_all_notes
from src.agent.prompts import (
    REFLECTION_PROMPT,
    INFO_PROMPT,
    QUERY_WRITER_PROMPT,
)

# LLMs

claude_3_5_sonnet = ChatAnthropic(
    model="claude-3-5-sonnet-latest", temperature=0
)

# Search

tavily_async_client = AsyncTavilyClient()


class Queries(BaseModel):
    queries: list[str] = Field(
        description="List of search queries.",
    )


class ReflectionOutput(BaseModel):
    """Structured output for reflection analysis."""
    
    years_experience: int | None = Field(
        description="Total years of professional experience, or null if not found"
    )
    current_company: str | None = Field(
        description="Current company or organization, or null if not found"
    )
    role: str | None = Field(
        description="Current job title or position, or null if not found"
    )
    prior_companies: list[str] = Field(
        description="List of previous companies worked at",
        default_factory=list
    )
    satisfaction_score: float = Field(
        description="Score from 0.0 to 1.0 indicating research completeness satisfaction",
        ge=0.0,
        le=1.0
    )
    missing_info: list[str] = Field(
        description="List of information that is still missing or unclear",
        default_factory=list
    )
    needs_more_research: bool = Field(
        description="Whether additional research is needed"
    )
    reasoning: str = Field(
        description="Reasoning for the satisfaction score and decision on whether to continue research"
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
    """Analyze completed research notes and decide whether to continue research.
    
    This function:
    1. Takes the completed research notes from the state
    2. Uses the REFLECTION_PROMPT with structured output to extract key information
    3. Evaluates research completeness and satisfaction
    4. Returns structured data with decision on whether to continue research
    """
    
    # Format all completed notes into a single string
    all_notes = format_all_notes(state.completed_notes)
    
    # Create structured LLM for reflection analysis
    structured_llm = claude_3_5_sonnet.with_structured_output(ReflectionOutput)
    
    # Format the reflection prompt with completed notes
    reflection_prompt = REFLECTION_PROMPT.format(
        completed_notes=all_notes
    )
    
    # Get reflection analysis from LLM
    reflection_result = structured_llm.invoke(reflection_prompt)
    
    # Convert the structured output to state updates
    return {
        "years_experience": reflection_result.years_experience,
        "current_company": reflection_result.current_company,
        "role": reflection_result.role,
        "prior_companies": reflection_result.prior_companies,
        "satisfaction_score": reflection_result.satisfaction_score,
        "missing_info": reflection_result.missing_info,
        "needs_more_research": reflection_result.needs_more_research,
        "reasoning": reflection_result.reasoning,
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
builder.add_edge("research_person", "reflection")

# Add conditional edge from reflection
def should_continue_research(state: OverallState) -> Literal["generate_queries", "__end__"]:
    """Determine whether to continue research or end based on reflection analysis."""
    if state.needs_more_research:
        return "generate_queries"
    else:
        return "__end__"

builder.add_conditional_edges(
    "reflection",
    should_continue_research,
    {
        "generate_queries": "generate_queries",
        "__end__": END,
    }
)

# Compile
graph = builder.compile()







