"""
LangGraph deployment entry point for the People Research Agent.

This module imports the compiled graph from the agent implementation
and exports it as 'app' for LangGraph platform compatibility.
"""

from src.agent.graph import graph

# Export the compiled graph as 'app' for LangGraph deployment
# This is the standard variable name expected by LangGraph platform
app = graph
