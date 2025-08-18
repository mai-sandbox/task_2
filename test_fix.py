#!/usr/bin/env python3
"""Simple test to verify the LangGraph import fix."""

print("Testing LangGraph import fix...")

# First, test that the correct import works
try:
    from langgraph.graph import END, START, StateGraph
    print("✓ Correct import path works: from langgraph.graph import END, START, StateGraph")
except ImportError as e:
    print(f"✗ Import failed: {e}")
    exit(1)

# Now test that our graph module compiles
try:
    # We'll compile the graph module by executing it
    import os
    import sys
    
    # Add project root to path
    sys.path.insert(0, '/home/daytona/task_2')
    
    # Import all dependencies first
    from langchain_anthropic import ChatAnthropic
    from langchain_core.runnables import RunnableConfig
    from pydantic import BaseModel, Field
    from tavily import AsyncTavilyClient
    
    # Import our modules
    from src.agent.configuration import Configuration
    from src.agent.prompts import INFO_PROMPT, QUERY_WRITER_PROMPT, REFLECTION_PROMPT
    from src.agent.state import InputState, OutputState, OverallState
    from src.agent.utils import deduplicate_and_format_sources, format_all_notes
    
    print("✓ All dependencies imported successfully")
    
    # Now import the graph module
    from src.agent import graph as graph_module
    print("✓ Graph module imported successfully")
    
    # Check if graph object exists
    if hasattr(graph_module, 'graph'):
        print(f"✓ Graph object exists: {type(graph_module.graph)}")
    else:
        print("✗ Graph object not found in module")
        exit(1)
    
    # Test agent.py import
    from agent import app
    print(f"✓ Agent app imported successfully: {type(app)}")
    
    print("\n✅ SUCCESS: LangGraph import issue is FIXED!")
    print("The import path has been updated from:")
    print("  from langgraph import END, START, StateGraph")
    print("to:")
    print("  from langgraph.graph import END, START, StateGraph")
    
except ImportError as e:
    print(f"✗ Import error: {e}")
    exit(1)
except Exception as e:
    print(f"✗ Unexpected error: {e}")
    exit(1)
