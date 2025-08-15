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


class ReflectionResult(BaseModel):
    """Structured result from reflection evaluation."""
    
    extracted_data: dict[str, Any] = Field(
        description="Structured data extracted from research notes according to schema"
    )
    completeness_assessment: dict[str, dict[str, str]] = Field(
        description="Assessment of each required field with status, confidence, and notes"
    )
    decision: Literal["SATISFACTORY", "CONTINUE", "REDO"] = Field(
        description="Decision on whether research is satisfactory, needs continuation, or should be redone"
    )
    reasoning: str = Field(
        description="Detailed reasoning for the decision and recommendations"
    )


async def reflection(state: OverallState, config: RunnableConfig) -> dict[str, Any]:
    """Evaluate research completeness and decide whether to continue, redo, or finish.
    
    This function:
    1. Takes completed research notes
    2. Converts them to structured format using extraction_schema
    3. Evaluates completeness against required fields
    4. Returns reflection results with reasoning for next steps
    """
    
    # Format person information for the prompt
    person_str = f"Email: {state.person.email}"
    if state.person.name:
        person_str += f", Name: {state.person.name}"
    if state.person.company:
        person_str += f", Company: {state.person.company}"
    if state.person.role:
        person_str += f", Role: {state.person.role}"
    if state.person.linkedin:
        person_str += f", LinkedIn: {state.person.linkedin}"
    
    # Format completed notes
    notes_str = format_all_notes(state.completed_notes)
    
    # Create reflection prompt
    reflection_prompt = REFLECTION_PROMPT.format(
        person=person_str,
        completed_notes=notes_str,
        extraction_schema=json.dumps(state.extraction_schema, indent=2)
    )
    
    # Use structured output for consistent reflection results
    structured_llm = claude_3_5_sonnet.with_structured_output(ReflectionResult)
    
    # Get reflection evaluation
    reflection_result = await structured_llm.ainvoke(reflection_prompt)
    
    # Return the reflection results to be used by conditional edges
    return {
        "reflection_result": reflection_result,
        "reflection_decision": reflection_result.decision,
        "extracted_data": reflection_result.extracted_data
    }


def should_continue_reflection(state: OverallState) -> str:
    """Determine the next step based on reflection results."""
    if not hasattr(state, 'reflection_decision') or state.reflection_decision is None:
        # If no reflection decision yet, go to reflection
        return "reflection"
    
    decision = state.reflection_decision
    
    if decision == "SATISFACTORY":
        # Research is complete, end the workflow
        return END
    elif decision == "CONTINUE":
        # Need more targeted research, generate new queries
        return "generate_queries"
    elif decision == "REDO":
        # Research quality is poor, start over with new queries
        return "generate_queries"
    else:
        # Default fallback
        return END


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

# Add conditional edge from research_person to reflection
builder.add_edge("research_person", "reflection")

# Add conditional edges from reflection based on decision
builder.add_conditional_edges(
    "reflection",
    should_continue_reflection,
    {
        "generate_queries": "generate_queries",  # Continue or redo research
        END: END  # Research is satisfactory
    }
)

# Compile
graph = builder.compile()



