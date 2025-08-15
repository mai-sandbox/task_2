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


async def reflection(state: OverallState, config: RunnableConfig) -> dict[str, Any]:
    """Analyze completed research notes and decide whether to continue or redo research.
    
    This function:
    1. Takes completed_notes from state
    2. Uses Claude with REFLECTION_PROMPT to convert notes to structured format
    3. Evaluates information satisfaction for years of experience, current company, role, prior companies
    4. Returns decision on whether to redo research or complete the process
    """
    
    # Format all completed notes into a single string
    all_notes = format_all_notes(state.completed_notes)
    
    # Create reflection prompt with notes and extraction schema
    reflection_prompt = REFLECTION_PROMPT.format(
        completed_notes=all_notes,
        extraction_schema=json.dumps(state.extraction_schema, indent=2)
    )
    
    # Get reflection analysis from Claude
    reflection_result = await claude_3_5_sonnet.ainvoke(reflection_prompt)
    reflection_content = str(reflection_result.content)
    
    # Parse the reflection response to extract structured information and decision
    # Look for the decision line in the response
    decision = "needs_more_research"  # Default to more research if parsing fails
    reasoning = "Unable to parse reflection response"
    
    # Extract structured information
    years_of_experience = "Unknown"
    current_company = "Unknown" 
    current_role = "Unknown"
    prior_companies = []
    
    try:
        # Parse the reflection response
        lines = reflection_content.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Extract structured information
            if line.startswith('- years_of_experience:'):
                years_of_experience = line.split(':', 1)[1].strip().strip('[]')
            elif line.startswith('- current_company:'):
                current_company = line.split(':', 1)[1].strip().strip('[]')
            elif line.startswith('- current_role:'):
                current_role = line.split(':', 1)[1].strip().strip('[]')
            elif line.startswith('- prior_companies:'):
                companies_str = line.split(':', 1)[1].strip().strip('[]')
                if companies_str and companies_str != "Unknown" and companies_str != "empty list":
                    # Simple parsing - split by comma and clean up
                    prior_companies = [c.strip().strip('"\'') for c in companies_str.split(',') if c.strip()]
            
            # Extract decision
            elif line.startswith('Decision:'):
                decision_text = line.split(':', 1)[1].strip().strip('[]')
                if 'satisfied' in decision_text.lower():
                    decision = "satisfied"
                elif 'needs_more_research' in decision_text.lower():
                    decision = "needs_more_research"
            
            # Extract reasoning
            elif line.startswith('Reasoning:'):
                # Get reasoning from this line and potentially next lines
                reasoning_parts = [line.split(':', 1)[1].strip()]
                # Look for continuation lines
                for j in range(i + 1, len(lines)):
                    next_line = lines[j].strip()
                    if next_line.startswith('**') or next_line.startswith('Decision:') or not next_line:
                        break
                    reasoning_parts.append(next_line)
                reasoning = ' '.join(reasoning_parts)
    
    except Exception as e:
        print(f"Warning: Error parsing reflection response: {e}")
        # Keep default values
    
    # Return state updates based on decision
    return {
        "years_of_experience": years_of_experience,
        "current_company": current_company,
        "current_role": current_role,
        "prior_companies": prior_companies,
        "reflection_decision": decision,
        "reflection_reasoning": reasoning
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
    """Determine whether to continue research or end based on reflection decision."""
    reflection_decision = state.get("reflection_decision", "needs_more_research")
    
    if reflection_decision == "satisfied":
        return "__end__"
    else:
        return "generate_queries"

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


