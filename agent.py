"""
LangGraph deployment entry point.

This module imports the compiled graph from the agent implementation
and exports it as 'app' for LangGraph deployment compatibility.
"""

from src.agent.graph import graph

# Export the compiled graph as 'app' for LangGraph deployment
app = graph
