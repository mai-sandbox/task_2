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
    """Structured output for reflection decision making."""
    
    years_of_experience: Optional[int] = Field(
        default=None,
        description="Extracted years of professional experience"
    )
    current_company: Optional[str] = Field(
        default=None,
        description="Extracted current company name"
    )
    current_role: Optional[str] = Field(
        default=None,
        description="Extracted current job title/role"
    )
    prior_companies: list[str] = Field(
        default_factory=list,
        description="List of previous companies"
    )
    missing_information: list[str] = Field(
        default_factory=list,
        description="Critical information that is missing"
    )
    confidence_score: float = Field(
        default=0.0,
        description="Confidence in the completeness of information (0-1)"
    )
    reasoning: str = Field(
        description="Detailed reasoning for the decision"
    )
    decision: Literal["satisfactory", "needs_more_research"] = Field(
        description="Final decision on whether research is complete"
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
    """Evaluate the completeness of research and decide whether to continue or finish.
    
    This function:
    1. Analyzes the collected research notes
    2. Extracts structured information
    3. Assesses completeness and quality
    4. Decides whether additional research is needed
    """
    
    # Get configuration
    configurable = Configuration.from_runnable_config(config)
    
    # Format all collected notes
    research_notes = format_all_notes(state.completed_notes)
    
    # Format person information
    person_dict = state.person.model_dump() if hasattr(state.person, 'model_dump') else dict(state.person)
    person_str = json.dumps(person_dict, indent=2)
    
    # Create structured LLM for reflection decision
    structured_llm = claude_3_5_sonnet.with_structured_output(ReflectionDecision)
    
    # Generate reflection prompt
    reflection_prompt = REFLECTION_PROMPT.format(
        person=person_str,
        research_notes=research_notes,
        extraction_schema=json.dumps(state.extraction_schema, indent=2)
    )
    
    # Get reflection decision
    decision = cast(
        ReflectionDecision,
        await structured_llm.ainvoke(
            [
                {
                    "role": "system",
                    "content": "You are a research quality assessor. Analyze the research notes and make a decision about whether the research is complete.",
                },
                {
                    "role": "user",
                    "content": reflection_prompt,
                },
            ]
        ),
    )
    
    # Prepare output state with extracted information
    output_update = {
        "years_of_experience": decision.years_of_experience,
        "current_company": decision.current_company,
        "current_role": decision.current_role,
        "prior_companies": decision.prior_companies,
        "research_notes": research_notes,
        "confidence_score": decision.confidence_score,
        "missing_information": decision.missing_information,
        "reflection_count": state.reflection_count + 1,
    }
    
    # Store the decision for routing
    output_update["reflection_decision"] = decision.decision
    output_update["reflection_reasoning"] = decision.reasoning
    
    return output_update


def should_continue_research(state: OverallState) -> Literal["reflection", "end"]:
    """Determine whether to continue to reflection or end after research."""
    # Always go to reflection after research to evaluate completeness
    return "reflection"


def reflection_routing(state: OverallState) -> Literal["generate_queries", "end"]:
    """Route based on reflection decision and iteration count.
    
    Returns:
        - "generate_queries" if research needs improvement and haven't exceeded max iterations
        - "end" if research is satisfactory or max iterations reached
    """
    # Check if we have a reflection decision
    if not state.reflection_decision:
        return "end"
    
    # Check if research is satisfactory
    if state.reflection_decision == "satisfactory":
        return "end"
    
    # Check if we've exceeded max reflection steps
    # Using a default of 2 which will be configured in configuration.py
    # The actual value will be set via Configuration class
    max_steps = getattr(state, 'max_reflection_steps', 2)
    if state.reflection_count >= max_steps:
        return "end"
    
    # Continue researching if not satisfactory and under iteration limit
    return "generate_queries"


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

# Add conditional edge from research_person to reflection
# After research, always go to reflection for evaluation
builder.add_edge("research_person", "reflection")

# Add conditional edge from reflection
# Based on the reflection decision, either continue research or end
builder.add_conditional_edges(
    "reflection",
    reflection_routing,
    {
        "generate_queries": "generate_queries",
        "end": END,
    }
)

# Compile
graph = builder.compile()






