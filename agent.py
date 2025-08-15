"""
People Research Agent

A LangGraph agent that performs iterative web research about people,
extracting structured information and using reflection to determine
when research is complete or needs to continue.

This module exports the compiled graph as 'app' for LangGraph deployment.
"""

from src.agent.graph import graph

# Export the compiled graph as 'app' for LangGraph deployment compatibility
app = graph
