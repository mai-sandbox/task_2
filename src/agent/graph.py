import asyncio
from typing import cast, Any, Literal, Optional, Union
import json

from tavily import AsyncTavilyClient
from langchain_anthropic import ChatAnthropic
from langchain_core.runnables import RunnableConfig
from langgraph import START, END, StateGraph
from pydantic import BaseModel, Field

from agent.configuration import Configuration
from agent.state import InputState, OutputState, OverallState, ExtractedInfo
from agent.utils import deduplicate_and_format_sources, format_all_notes
from agent.prompts import (
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


class ReflectionResult(BaseModel):
    """Structured output for reflection evaluation."""
    
    years_experience: Optional[int] = Field(
        default=None,
        description="Extracted years of professional experience"
    )
    current_company: Optional[str] = Field(
        default=None,
        description="Extracted current company name"
    )
    role: Optional[str] = Field(
        default=None,
        description="Extracted current role or job title"
    )
    prior_companies: list[str] = Field(
        default_factory=list,
        description="List of previous companies"
    )
    missing_information: list[str] = Field(
        default_factory=list,
        description="List of missing key information"
    )
    quality_assessment: Literal["complete", "partial", "insufficient"] = Field(
        description="Overall quality of the research"
    )
    additional_search_suggestions: list[str] = Field(
        default_factory=list,
        description="Suggested search queries for missing information"
    )
    decision: Literal["continue", "complete"] = Field(
        description="Whether to continue researching or complete the task"
    )
    reasoning: str = Field(
        description="Explanation for the decision"
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
    """Reflect on the research notes and decide whether to continue or complete."""
    
    # Format all collected notes
    all_notes = format_all_notes(state.completed_notes)
    
    # Create structured LLM for reflection
    structured_llm = claude_3_5_sonnet.with_structured_output(ReflectionResult)
    
    # Format person information for the prompt
    person_str = f"Email: {state.person.email}"
    if state.person.name:
        person_str += f", Name: {state.person.name}"
    if state.person.company:
        person_str += f", Company: {state.person.company}"
    if state.person.role:
        person_str += f", Role: {state.person.role}"
    
    # Generate reflection prompt
    reflection_prompt = REFLECTION_PROMPT.format(
        person=person_str,
        notes=all_notes
    )
    
    # Get structured reflection result
    reflection_result = cast(
        ReflectionResult,
        await structured_llm.ainvoke(
            [
                {
                    "role": "system",
                    "content": "You are a research quality evaluator. Analyze the research notes and provide a structured assessment."
                },
                {
                    "role": "user",
                    "content": reflection_prompt
                }
            ]
        )
    )
    
    # Create ExtractedInfo object from reflection results
    extracted_info = ExtractedInfo(
        years_experience=reflection_result.years_experience,
        current_company=reflection_result.current_company,
        role=reflection_result.role,
        prior_companies=reflection_result.prior_companies
    )
    
    # Update state with extracted information and decision
    return {
        "extracted_info": extracted_info,
        "reflection_decision": reflection_result.decision,
        "search_queries": reflection_result.additional_search_suggestions if reflection_result.decision == "continue" else []
    }


def route_after_reflection(state: OverallState) -> Literal["generate_queries", END]:
    """Route based on reflection decision."""
    if state.reflection_decision == "continue":
        return "generate_queries"
    else:
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
builder.add_edge("research_person", "reflection")
builder.add_conditional_edges(
    "reflection",
    route_after_reflection,
    {
        "generate_queries": "generate_queries",
        END: END
    }
)

# Compile
graph = builder.compile()

# Export as 'app' for LangGraph platform deployment
app = graph








