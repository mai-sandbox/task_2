"""
People Research Agent - LangGraph Deployment Entry Point

This module serves as the main entry point for the LangGraph deployment.
It imports the compiled graph and exports it as 'app' for the LangGraph platform.
"""

import os
import sys
from typing import Optional

# Import the compiled graph from the src.agent module
from src.agent.graph import graph

# Export the graph as 'app' for LangGraph deployment
# This is the standard variable name expected by LangGraph platform
app = graph

# Optional: Add metadata for the deployment
__version__ = "0.0.1"
__description__ = "Researcher agent that searches information about a person and returns it in a structured format with reflection capabilities."


def get_app():
    """
    Factory function to get the configured app instance.
    This can be useful for testing or custom initialization.
    
    Returns:
        The compiled LangGraph application
    """
    return app


# Configuration validation (optional but recommended)
def validate_environment():
    """
    Validate that required environment variables are set.
    This helps catch configuration issues early in deployment.
    """
    required_vars = [
        "ANTHROPIC_API_KEY",  # Required for Claude model
        "TAVILY_API_KEY",      # Required for web search
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"Warning: Missing environment variables: {', '.join(missing_vars)}")
        print("These should be configured in your deployment environment or .env file")
    
    return len(missing_vars) == 0


# Run validation when module is imported (helps catch issues early)
if __name__ != "__main__":
    # Only validate when imported, not when run directly
    validate_environment()


# For local testing
if __name__ == "__main__":
    print(f"People Research Agent v{__version__}")
    print(f"Description: {__description__}")
    print("\nEnvironment validation:")
    if validate_environment():
        print("✓ All required environment variables are set")
    else:
        print("✗ Some environment variables are missing (see warnings above)")
    
    print("\nGraph structure:")
    print(f"- Nodes: {list(app.nodes.keys())}")
    print(f"- Entry point: START → generate_queries")
    print(f"- Workflow: generate_queries → research_person → reflection → [conditional routing]")
    print("\nThe agent is ready for deployment!")

