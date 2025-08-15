"""
LangGraph People Research Agent

This module exports the compiled graph for deployment on the LangGraph platform.
"""

from src.agent.graph import graph

# Export the compiled graph as 'app' for LangGraph deployment
app = graph
