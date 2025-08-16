#!/usr/bin/env python
"""
People Research Agent with Reflection

This agent researches information about people and uses reflection to ensure
the quality and completeness of the gathered information.
"""

# Import the compiled graph from the agent module
from src.agent.graph import graph

# Export the compiled graph as 'app' for LangGraph deployment
app = graph

# Optional: Add metadata for the application
if __name__ == "__main__":
    print("People Research Agent with Reflection")
    print("=" * 50)
    print("This agent is configured for LangGraph deployment.")
    print("The compiled graph is exported as 'app'.")
    print("\nFeatures:")
    print("- Automated web research about people")
    print("- Structured information extraction")
    print("- Reflection-based quality assessment")
    print("- Iterative research improvement")
    print("\nTo run locally, use: langgraph dev")

