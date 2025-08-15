"""
LangGraph People Research Agent with Reflection

This module exports the compiled graph as 'app' for LangGraph deployment compatibility.
The agent performs iterative research on people, focusing on work experience information,
and uses a reflection mechanism to evaluate completeness and decide whether to continue research.
"""

from src.agent.graph import graph

# Export the compiled graph as 'app' - this is required for LangGraph deployment
app = graph

# Optional: Add metadata for deployment
__version__ = "1.0.0"
__description__ = "People Research Agent with Reflection Mechanism"
