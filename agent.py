"""
LangGraph Agent Entry Point

This module imports the compiled graph from src/agent/graph.py and exports it as 'app'
for LangGraph deployment compatibility.
"""

from src.agent.graph import graph

# Export the compiled graph as 'app' for LangGraph deployment
app = graph
