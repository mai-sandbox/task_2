"""
LangGraph People Research Agent with Reflection

This module exports the compiled graph as 'app' for LangGraph deployment compatibility.
The agent performs iterative research on people, using reflection to evaluate completeness
and decide whether additional research iterations are needed.

Key features:
- Web search using Tavily API
- LLM-powered research note generation
- Reflection-based completeness evaluation
- Iterative research improvement
- Structured output for key information (years of experience, current company, role, prior companies)
"""

from src.agent.graph import graph

# Export the compiled graph as 'app' for LangGraph deployment
app = graph
