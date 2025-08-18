"""LangGraph agent entry point for deployment.

This module serves as the main entry point for the LangGraph deployment.
It imports the compiled graph from the agent module and exports it as 'app'
for compatibility with LangGraph Platform.
"""

from src.agent.graph import graph

# Export the compiled graph as 'app' for LangGraph deployment
# This is the required variable name for LangGraph Platform
app = graph
