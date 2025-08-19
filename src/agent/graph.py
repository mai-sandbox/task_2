"""People researcher agent with reflection capabilities."""

import asyncio
import json
import re
from typing import Any, cast

from langchain_anthropic import ChatAnthropic
from langchain_core.rate_limiters import InMemoryRateLimiter
from langchain_core.runnables import RunnableConfig
from langgraph.constants import START, END
from langgraph.graph import StateGraph
from pydantic import BaseModel, Field
from tavily import AsyncTavilyClient

from agent.configuration import Configuration
from agent.prompts import INFO_PROMPT, QUERY_WRITER_PROMPT, REFLECTION_PROMPT
from agent.state import InputState, OutputState, OverallState
from agent.utils import deduplicate_and_format_sources

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
    """Pydantic model for structured query generation."""
    
    queries: list[str] = Field(
        description="List of search queries.",
    )


class ReflectionResult(BaseModel):
    """Structured result from reflection analysis."""
    structured_data: dict[str, Any] = Field(
        description="Extracted and structured information about the person"
    )
    assessment: dict[str, Any] = Field(
        description="Quality assessment including completeness and confidence scores"
    )
    recommendations: dict[str, Any] = Field(
        description="Recommendations for next steps including whether more research is needed"
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
    """Reflect on collected notes and structure the information."""
    # Format person information
    person_str = f"Email: {state.person.email}"
    if state.person.name:
        person_str += f" Name: {state.person.name}"
    if state.person.linkedin:
        person_str += f" LinkedIn URL: {state.person.linkedin}"
    if state.person.role:
        person_str += f" Role: {state.person.role}"
    if state.person.company:
        person_str += f" Company: {state.person.company}"
    
    # Combine all notes
    all_notes = "\n\n".join(state.completed_notes)
    
    # Create reflection prompt
    reflection_prompt = REFLECTION_PROMPT.format(
        person=person_str,
        notes=all_notes,
        schema=json.dumps(state.extraction_schema, indent=2)
    )
    
    # Get structured reflection from LLM
    structured_llm = claude_3_5_sonnet.with_structured_output(ReflectionResult)
    
    try:
        result = cast(
            ReflectionResult,
            await structured_llm.ainvoke([
                {"role": "system", "content": reflection_prompt},
                {"role": "user", "content": "Please analyze the research notes and provide your structured assessment."}
            ])
        )
        
        # Convert to dict for state
        reflection_dict = {
            "structured_data": result.structured_data,
            "assessment": result.assessment,
            "recommendations": result.recommendations
        }
        
        return {
            "reflection_result": reflection_dict,
            "needs_more_research": result.recommendations["needs_more_research"]
        }
        
    except Exception:
        # Fallback if structured output fails
        result = await claude_3_5_sonnet.ainvoke([
            {"role": "system", "content": reflection_prompt},
            {"role": "user", "content": "Please analyze the research notes and provide your structured assessment."}
        ])
        
        # Try to parse JSON from content
        try:
            json_match = re.search(r'\{.*\}', str(result.content), re.DOTALL)
            if json_match:
                reflection_dict = json.loads(json_match.group())
                return {
                    "reflection_result": reflection_dict,
                    "needs_more_research": reflection_dict.get("recommendations", {}).get("needs_more_research", False)
                }
        except (json.JSONDecodeError, AttributeError):
            pass
        
        # Ultimate fallback
        return {
            "reflection_result": {
                "structured_data": {},
                "assessment": {"completeness_score": 0.0, "confidence_score": 0.0},
                "recommendations": {"needs_more_research": True, "reasoning": "Failed to parse reflection"}
            },
            "needs_more_research": True
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
builder.add_edge("reflection", END)

# Compile
graph = builder.compile()
