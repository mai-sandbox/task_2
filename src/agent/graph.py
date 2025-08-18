import asyncio
from typing import cast, Any, Literal, Optional
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
    """Structured output for reflection decision."""
    
    decision: Literal["CONTINUE_RESEARCH", "FINISH_RESEARCH"] = Field(
        description="Decision on whether to continue research or finish"
    )
    
    years_of_experience: Optional[int] = Field(
        default=None,
        description="Extracted years of experience"
    )
    
    current_company: Optional[str] = Field(
        default=None,
        description="Extracted current company"
    )
    
    role: Optional[str] = Field(
        default=None,
        description="Extracted current role"
    )
    
    prior_companies: list[str] = Field(
        default_factory=list,
        description="List of prior companies"
    )
    
    missing_information: list[str] = Field(
        default_factory=list,
        description="List of missing information"
    )
    
    reasoning: str = Field(
        description="Reasoning for the decision"
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
    """Evaluate research completeness and decide whether to continue or finish.
    
    This function:
    1. Reviews all completed research notes
    2. Extracts structured information (years of experience, companies, role)
    3. Evaluates completeness of the research
    4. Decides whether to continue research or finish
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
    
    # Format all completed notes
    formatted_notes = format_all_notes(state.completed_notes)
    
    # Create structured LLM for decision making
    structured_llm = claude_3_5_sonnet.with_structured_output(ReflectionDecision)
    
    # Prepare the reflection prompt
    reflection_prompt = REFLECTION_PROMPT.format(
        person=person_str,
        extraction_schema=json.dumps(state.extraction_schema, indent=2),
        completed_notes=formatted_notes
    )
    
    # Get the reflection decision
    decision = await structured_llm.ainvoke([
        {
            "role": "system",
            "content": "You are a research quality evaluator. Analyze the research notes and make a decision about whether to continue or finish the research process."
        },
        {
            "role": "user",
            "content": reflection_prompt
        }
    ])
    
    # Prepare the return state update
    state_update = {
        "years_of_experience": decision.years_of_experience,
        "current_company": decision.current_company,
        "role": decision.role,
        "prior_companies": decision.prior_companies,
        "missing_information": decision.missing_information,
        "reflection_decision": decision.decision,
        "reflection_reasoning": decision.reasoning
    }
    
    # If research is complete, mark it as such
    if decision.decision == "FINISH_RESEARCH":
        state_update["research_complete"] = True
    
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



