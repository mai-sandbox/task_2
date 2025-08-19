import asyncio
from typing import cast, Any, Literal
import json

from tavily import AsyncTavilyClient
from langchain_anthropic import ChatAnthropic
from langchain_core.rate_limiters import InMemoryRateLimiter
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
    """Analyze completed research notes and extract structured information.
    
    This function performs reflection on the research notes to:
    1. Extract structured information about the person
    2. Assess the completeness of the research
    3. Determine if more research is needed
    """
    
    # Format the completed notes
    all_notes = format_all_notes(state.completed_notes)
    
    # Format person information
    person_str = f"Email: {state.person.email}"
    if state.person.name:
        person_str += f"\nName: {state.person.name}"
    if state.person.linkedin:
        person_str += f"\nLinkedIn URL: {state.person.linkedin}"
    if state.person.role:
        person_str += f"\nRole: {state.person.role}"
    if state.person.company:
        person_str += f"\nCompany: {state.person.company}"
    
    # Create reflection prompt
    reflection_prompt = REFLECTION_PROMPT.format(
        completed_notes=all_notes,
        person=person_str,
        extraction_schema=json.dumps(state.extraction_schema, indent=2)
    )
    
    # Get reflection analysis from Claude
    result = await claude_3_5_sonnet.ainvoke(reflection_prompt)
    reflection_content = str(result.content)
    
    # Parse the reflection response to extract structured information
    # This is a simplified parser - in production you might want more robust parsing
    extracted_info = {}
    needs_more_research = True
    reasoning = ""
    
    try:
        # Extract years of experience
        if "Years of Experience:" in reflection_content:
            years_line = reflection_content.split("Years of Experience:")[1].split("\n")[0].strip()
            if years_line.lower() != "unknown" and years_line.lower() != "unclear":
                try:
                    # Extract numeric value from the line
                    import re
                    years_match = re.search(r'\d+', years_line)
                    if years_match:
                        extracted_info["years_of_experience"] = int(years_match.group())
                except:
                    pass
        
        # Extract current company
        if "Current Company:" in reflection_content:
            company_line = reflection_content.split("Current Company:")[1].split("\n")[0].strip()
            if company_line.lower() not in ["unknown", "unclear"]:
                extracted_info["current_company"] = company_line
        
        # Extract current role
        if "Current Role:" in reflection_content:
            role_line = reflection_content.split("Current Role:")[1].split("\n")[0].strip()
            if role_line.lower() not in ["unknown", "unclear"]:
                extracted_info["current_role"] = role_line
        
        # Extract prior companies
        if "Prior Companies:" in reflection_content:
            companies_line = reflection_content.split("Prior Companies:")[1].split("\n")[0].strip()
            if companies_line.lower() not in ["unknown", "unclear"]:
                extracted_info["prior_companies"] = companies_line
        
        # Determine if more research is needed
        if "Needs More Research:" in reflection_content:
            decision_line = reflection_content.split("Needs More Research:")[1].split("\n")[0].strip()
            needs_more_research = decision_line.upper().startswith("YES")
        
        # Extract reasoning
        if "Reasoning:" in reflection_content:
            reasoning_section = reflection_content.split("Reasoning:")[1]
            if "Suggested Next Steps:" in reasoning_section:
                reasoning = reasoning_section.split("Suggested Next Steps:")[0].strip()
            else:
                reasoning = reasoning_section.strip()
    
    except Exception as e:
        # If parsing fails, default to needing more research
        reasoning = f"Failed to parse reflection response: {str(e)}"
        needs_more_research = True
    
    return {
        "reflection_result": extracted_info,
        "needs_more_research": needs_more_research,
        "reflection_reasoning": reasoning
    }


def should_continue(state: OverallState) -> Literal["generate_queries", "END"]:
    """Determine whether to continue research or end the workflow.
    
    This function checks the reflection results to decide if more research is needed.
    If more research is needed, it routes back to generate_queries.
    If research is complete, it routes to END.
    """
    if state.needs_more_research:
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

# Add edges for the workflow
builder.add_edge(START, "generate_queries")
builder.add_edge("generate_queries", "research_person")
builder.add_edge("research_person", "reflection")

# Add conditional edge from reflection
builder.add_conditional_edges(
    "reflection",
    should_continue,
    {
        "generate_queries": "generate_queries",
        "END": END
    }
)

# Compile
graph = builder.compile()




