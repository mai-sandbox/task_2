import asyncio
from typing import cast, Any, Literal
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



def generate_queries(state: OverallState, config: RunnableConfig) -> dict[str, Any]:
    """Generate search queries based on the user input and extraction schema."""
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
    
    # Include missing information from reflection if this is a continuation
    additional_context = ""
    if state.missing_information:
        additional_context = f"\n\nAdditional context: Focus on finding the following missing information: {', '.join(state.missing_information)}"

    query_instructions = QUERY_WRITER_PROMPT.format(
        person=person_str,
        info=json.dumps(state.extraction_schema, indent=2),
        user_notes=state.user_notes,
        max_search_queries=max_search_queries,
    ) + additional_context

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
    """Analyze completed research notes and structure them, deciding if more research is needed."""
    
    # Format all notes into a single string
    all_notes = format_all_notes(state.completed_notes)
    
    # Create the reflection prompt
    reflection_prompt = REFLECTION_PROMPT.format(notes=all_notes)
    
    # Get structured response using JSON mode
    result = await claude_3_5_sonnet.ainvoke(reflection_prompt)
    
    try:
        # Parse the JSON response
        reflection_data = json.loads(str(result.content))
        
        structured_info = reflection_data.get("structured_info", {})
        analysis = reflection_data.get("analysis", {})
        
        return {
            "structured_info": structured_info,
            "reflection_decision": "continue" if analysis.get("continue_research", False) else "stop",
            "reflection_reasoning": analysis.get("reasoning", ""),
            "missing_information": analysis.get("missing_information", []),
            "research_complete": not analysis.get("continue_research", False)
        }
    except json.JSONDecodeError:
        # Fallback if JSON parsing fails
        return {
            "structured_info": {},
            "reflection_decision": "stop",
            "reflection_reasoning": "Failed to parse reflection response, stopping research.",
            "missing_information": [],
            "research_complete": True
        }


def should_continue_research(state: OverallState) -> Literal["continue", "end"]:
    """Decide whether to continue research based on reflection analysis."""
    if state.reflection_decision == "continue":
        return "continue"
    return "end"

def initialize_state(state: OverallState, config: RunnableConfig) -> dict[str, Any]:
    """Initialize the state with default extraction schema if not provided."""
    if not state.extraction_schema:
        # Default schema focusing on professional information
        default_schema = {
            "years_of_experience": "Total years of professional experience",
            "current_company": "Current employer/organization",
            "current_role": "Current job title/position",
            "prior_companies": "List of previous employers in chronological order",
            "education": "Educational background",
            "skills": "Professional skills and expertise",
            "achievements": "Notable accomplishments or awards"
        }
        return {"extraction_schema": default_schema}
    return {}


# Add nodes and edges
builder = StateGraph(
    OverallState,
    input=InputState,
    output=OutputState,
    config_schema=Configuration,
)
builder.add_node("initialize_state", initialize_state)
builder.add_node("generate_queries", generate_queries)
builder.add_node("research_person", research_person)
builder.add_node("reflection", reflection)

builder.add_edge(START, "initialize_state")
builder.add_edge("initialize_state", "generate_queries")
builder.add_edge("generate_queries", "research_person")
builder.add_edge("research_person", "reflection")
builder.add_conditional_edges(
    "reflection",
    should_continue_research,
    {"continue": "generate_queries", "end": END}
)

# Compile
graph = builder.compile()
