# People Researcher Agent

An intelligent research agent that searches for information about people and returns structured data with a reflection step for quality assurance.

## Features

- **Automatic Query Generation**: Generates targeted search queries based on person's information
- **Web Search**: Searches multiple sources using Tavily API
- **Structured Data Extraction**: Extracts key information including:
  - Years of experience
  - Current company and role
  - Prior companies and roles with durations
  - Educational background
  - Skills and expertise
- **Reflection & Retry Logic**: Evaluates completeness and retries if information is missing (max 2 retries)
- **LangGraph Deployment Ready**: Includes `langgraph.json` for easy deployment

## Installation

```bash
pip install -e .
```

## Environment Variables

Set the following environment variables:
```bash
export TAVILY_API_KEY="your-tavily-api-key"
export ANTHROPIC_API_KEY="your-anthropic-api-key"
```

## Usage

```python
from src.agent.graph import graph
from src.agent.state import Person

# Create a person to research
person = Person(
    email="john.doe@example.com",
    name="John Doe",
    company="Example Corp",
    role="Software Engineer",
    linkedin="https://linkedin.com/in/johndoe"
)

# Run the agent
result = await graph.ainvoke({
    "person": person,
    "user_notes": "Looking for work experience and education"
})

# Access structured information
structured_info = result["structured_info"]
print(f"Years of experience: {structured_info.years_of_experience}")
print(f"Current role: {structured_info.current_role} at {structured_info.current_company}")
print(f"Prior companies: {structured_info.prior_companies}")
```

## Deployment with LangGraph

Deploy using the included `langgraph.json`:

```bash
langgraph deploy
```

## Testing

Run the test script to verify the agent works:

```bash
python test_agent.py
```

## Architecture

The agent follows this flow:
1. **Generate Queries**: Creates targeted search queries
2. **Research Person**: Executes web searches and collects information
3. **Reflection**: Extracts structured data and assesses completeness
4. **Conditional Retry**: If information is incomplete, loops back (max 2 times)
5. **Finalize**: Prepares the final structured output

## Configuration

The agent supports configurable parameters:
- `max_search_queries`: Maximum number of search queries per iteration (default: 3)
- `max_search_results`: Maximum search results per query (default: 3)