import asyncio
import json
from typing import Any, Literal, cast

from langchain_anthropic import ChatAnthropic
from langchain_core import InMemoryRateLimiter
from langchain_core.runnables import RunnableConfig
from langgraph import END, START, StateGraph
from pydantic import BaseModel, Field
from tavily import AsyncTavilyClient

from agent.configuration import Configuration
from agent.prompts import (
    INFO_PROMPT,
    QUERY_WRITER_PROMPT,
    REFLECTION_PROMPT,
)
from agent.state import InputState, OutputState, OverallState, ResearchCompleteness
from agent.utils import deduplicate_and_format_sources, format_all_notes

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


async def research_person(
    state: OverallState, config: RunnableConfig
) -> dict[str, Any]:
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


class ReflectionOutput(BaseModel):
    """Structured output for the reflection evaluation."""

    # Extracted information
    years_of_experience: int = Field(
        default=0, description="Total years of professional experience"
    )
    current_company: str = Field(
        default="", description="Name of the current employer/company"
    )
    current_role: str = Field(default="", description="Current job title or position")
    prior_companies: list[str] = Field(
        default_factory=list, description="List of previous companies worked at"
    )
    education: str = Field(
        default="", description="Educational background and qualifications"
    )
    skills: list[str] = Field(
        default_factory=list, description="Key technical and professional skills"
    )
    notable_achievements: list[str] = Field(
        default_factory=list, description="Significant accomplishments or projects"
    )

    # Completeness assessment
    is_complete: bool = Field(
        description="Whether the research gathered all essential information"
    )
    missing_information: list[str] = Field(
        default_factory=list,
        description="List of missing information that should be searched",
    )
    confidence_score: float = Field(
        default=0.0, description="Confidence score of the research completeness (0-1)"
    )
    reasoning: str = Field(
        description="Reasoning for the completeness assessment and decision to continue or finish"
    )
    suggested_queries: list[str] = Field(
        default_factory=list,
        description="Suggested search queries if more research is needed",
    )

    # Decision
    decision: Literal["continue", "complete"] = Field(
        description="Decision to continue research or complete"
    )


async def reflection(state: OverallState, config: RunnableConfig) -> dict[str, Any]:
    """Reflect on the research notes to evaluate completeness and decide next steps.

    This function:
    1. Consolidates all research notes
    2. Extracts structured information from the notes
    3. Assesses the completeness of the research
    4. Decides whether to continue or complete the research
    """
    # Get configuration
    configurable = Configuration.from_runnable_config(config)
    max_iterations = getattr(configurable, "max_research_iterations", 4)

    # Calculate current iteration (based on number of completed notes)
    current_iteration = len(state.completed_notes)

    # Format all notes for evaluation
    consolidated_notes = format_all_notes(state.completed_notes)

    # Format person information
    person_str = f"Email: {state.person.email}"
    if state.person.name:
        person_str += f", Name: {state.person.name}"
    if state.person.company:
        person_str += f", Company: {state.person.company}"
    if state.person.role:
        person_str += f", Role: {state.person.role}"
    if state.person.linkedin:
        person_str += f", LinkedIn: {state.person.linkedin}"

    # Create structured LLM for reflection
    structured_llm = claude_3_5_sonnet.with_structured_output(ReflectionOutput)

    # Format the reflection prompt
    reflection_prompt = REFLECTION_PROMPT.format(
        person=person_str,
        schema=json.dumps(state.extraction_schema, indent=2),
        notes=consolidated_notes,
        iteration=current_iteration,
        max_iterations=max_iterations,
    )

    # Get structured reflection output
    reflection_result = await structured_llm.ainvoke(
        [
            {
                "role": "system",
                "content": "You are a research quality evaluator. Analyze the research notes and provide a structured assessment.",
            },
            {"role": "user", "content": reflection_prompt},
        ]
    )

    # Prepare the output state update
    output_update = {
        "years_of_experience": reflection_result.years_of_experience
        if reflection_result.years_of_experience > 0
        else None,
        "current_company": reflection_result.current_company
        if reflection_result.current_company
        else None,
        "current_role": reflection_result.current_role
        if reflection_result.current_role
        else None,
        "prior_companies": reflection_result.prior_companies,
        "education": reflection_result.education
        if reflection_result.education
        else None,
        "skills": reflection_result.skills,
        "notable_achievements": reflection_result.notable_achievements,
        "completeness_assessment": ResearchCompleteness(
            is_complete=reflection_result.is_complete,
            missing_information=reflection_result.missing_information,
            confidence_score=reflection_result.confidence_score,
            reasoning=reflection_result.reasoning,
            suggested_queries=reflection_result.suggested_queries,
        ),
        "raw_notes": consolidated_notes,
        "research_iterations": current_iteration,
    }

    # Store the decision in state for conditional routing
    # We'll use a special key that the conditional edge can check
    output_update["__decision__"] = reflection_result.decision

    # If continuing, update search queries with suggestions
    if reflection_result.decision == "continue" and reflection_result.suggested_queries:
        output_update["search_queries"] = reflection_result.suggested_queries[
            :3
        ]  # Limit to 3 queries

    return output_update


def should_continue(state: OverallState) -> Literal["generate_queries", "end"]:
    """Determine whether to continue research or finish based on reflection decision.

    This function checks the decision made by the reflection node and routes accordingly:
    - If decision is "continue", route back to generate_queries for another iteration
    - If decision is "complete", route to END to finish the research
    """
    # Check for the decision stored by the reflection function
    # Since we can't add arbitrary fields to the dataclass, we'll check the completeness assessment
    decision = "complete"  # Default to complete

    # Check if we have a completeness assessment
    if hasattr(state, "completeness_assessment") and state.completeness_assessment:
        # If research is not complete and we have suggested queries, continue
        if (
            not state.completeness_assessment.is_complete
            and state.completeness_assessment.suggested_queries
        ):
            decision = "continue"

    # Also check iteration count as a safety measure
    current_iteration = len(state.completed_notes) if state.completed_notes else 0
    max_iterations = 4  # Hard limit to prevent infinite loops

    if decision == "continue" and current_iteration < max_iterations:
        return "generate_queries"
    else:
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

# Add edges
builder.add_edge(START, "generate_queries")
builder.add_edge("generate_queries", "research_person")
builder.add_edge("research_person", "reflection")  # Connect research to reflection

# Add conditional edge from reflection
builder.add_conditional_edges(
    "reflection",
    should_continue,
    {
        "generate_queries": "generate_queries",  # Continue research
        "end": END,  # Complete research
    },
)

# Compile
graph = builder.compile()

# Export for LangGraph Platform
app = graph
