"""
LangGraph deployment entry point.

This module imports the compiled graph from the agent implementation
and exports it as 'app' for LangGraph Platform compatibility.
"""

from src.agent.graph import graph

# Export the compiled graph as 'app' for LangGraph deployment
# This is the required variable name for LangGraph Platform
app = graph
