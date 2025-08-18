#!/usr/bin/env python3
"""
LangGraph agent entry point for deployment.

This module imports the compiled graph from the src/agent package
and exports it as 'app' for LangGraph Platform compatibility.
"""

# Import the compiled graph directly from the src.agent module
from src.agent.graph import graph

# Export the graph as 'app' for LangGraph deployment
# This is the standard variable name expected by LangGraph Platform
app = graph

# Optional: Add metadata for debugging
if __name__ == "__main__":
    print("People Research Agent with Reflection")
    print("=" * 40)
    print("Graph successfully loaded and exported as 'app'")
    print(f"Graph nodes: {list(app.nodes.keys())}")
    print(f"Entry point: START → generate_queries")
    print(f"Workflow: generate_queries → research_person → reflection → [continue/stop]")

