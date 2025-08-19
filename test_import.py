#!/usr/bin/env python3
"""Test script to verify LangGraph imports."""

try:
    from langgraph.graph import END, START, StateGraph
    print("✓ Successfully imported END, START, StateGraph from langgraph.graph")
    print(f"  - END: {END}")
    print(f"  - START: {START}")
    print(f"  - StateGraph: {StateGraph}")
except ImportError as e:
    print(f"✗ Failed to import from langgraph.graph: {e}")
    print("\nTrying alternative import paths...")
    
    # Try alternative import paths
    try:
        from langgraph.constants import END, START
        from langgraph.graph import StateGraph
        print("✓ Successfully imported from alternative paths:")
        print("  - END, START from langgraph.constants")
        print("  - StateGraph from langgraph.graph")
    except ImportError as e2:
        print(f"✗ Alternative import also failed: {e2}")
