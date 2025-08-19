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

def get_tavily_client():
    """Get Tavily client with lazy initialization."""
    return AsyncTavilyClient()


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
    tavily_client = get_tavily_client()
    search_tasks = []
    for query in state.search_queries:
        search_tasks.append(
            tavily_client.search(
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
    """Reflect on completed research notes and determine if additional research is needed.
    
    This function:
    1. Converts research notes to structured format based on extraction schema
    2. Evaluates completeness of the research
    3. Determines whether additional research is needed
    4. Provides reasoning for the decision
    """
    
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
    
    # Format completed notes
    notes_str = "\n\n".join([f"Research Note {i+1}:\n{note}" for i, note in enumerate(state.completed_notes)])
    
    # Create reflection prompt
    reflection_prompt = REFLECTION_PROMPT.format(
        person=person_str,
        completed_notes=notes_str,
        extraction_schema=json.dumps(state.extraction_schema, indent=2)
    )
    
    # Get structured reflection from LLM
    structured_llm = claude_3_5_sonnet.with_structured_output(
        schema={
            "type": "object",
            "properties": {
                "structured_research_results": {
                    "type": "object",
                    "properties": {
                        "years_of_experience": {"type": "string"},
                        "current_company": {"type": "string"},
                        "current_role": {"type": "string"},
                        "prior_companies": {"type": "string"}
                    },
                    "required": ["years_of_experience", "current_company", "current_role", "prior_companies"]
                },
                "research_satisfaction_assessment": {
                    "type": "object",
                    "properties": {
                        "satisfaction_level": {"type": "string", "enum": ["high", "medium", "low"]},
                        "information_found": {"type": "array", "items": {"type": "string"}},
                        "missing_information": {"type": "array", "items": {"type": "string"}},
                        "additional_search_needed": {"type": "boolean"},
                        "reasoning": {"type": "string"},
                        "suggested_search_queries": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["satisfaction_level", "information_found", "missing_information", 
                               "additional_search_needed", "reasoning", "suggested_search_queries"]
                }
            },
            "required": ["structured_research_results", "research_satisfaction_assessment"]
        }
    )
    
    # Execute reflection
    reflection_result = await structured_llm.ainvoke(reflection_prompt)
    
    return {
        "structured_research_results": reflection_result["structured_research_results"],
        "research_satisfaction_assessment": reflection_result["research_satisfaction_assessment"]
    }


def should_continue_research(state: OverallState) -> Literal["generate_queries", "END"]:
    """Conditional routing function to determine if additional research is needed.
    
    Based on the reflection assessment, decides whether to:
    - Continue research by generating new queries
    - End the process with current results
    """
    if not state.research_satisfaction_assessment:
        # If no assessment exists, end the process (safety fallback)
        return "END"
    
    # Check if additional research is needed based on reflection assessment
    additional_search_needed = state.research_satisfaction_assessment.get("additional_search_needed", False)
    
    if additional_search_needed:
        return "generate_queries"
    else:
        return "END"

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
builder.add_conditional_edges(
    "reflection",
    should_continue_research,
    {
        "generate_queries": "generate_queries",  # Loop back for additional research
        "END": END  # Terminate the process
    }
)

# Compile
graph = builder.compile()







