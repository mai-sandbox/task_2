#!/usr/bin/env python3
"""Test different LangGraph import paths to find the correct one."""

import sys

print("Testing LangGraph import paths...")
print("-" * 40)

# Test 1: Direct import from langgraph
try:
    from langgraph import END, START, StateGraph
    print("✓ Success: from langgraph import END, START, StateGraph")
    print(f"  END = {END}")
    print(f"  START = {START}")
except ImportError as e:
    print(f"✗ Failed: from langgraph import END, START, StateGraph")
    print(f"  Error: {e}")

# Test 2: Import from langgraph.graph
try:
    from langgraph.graph import END, START, StateGraph
    print("✓ Success: from langgraph.graph import END, START, StateGraph")
    print(f"  END = {END}")
    print(f"  START = {START}")
except ImportError as e:
    print(f"✗ Failed: from langgraph.graph import END, START, StateGraph")
    print(f"  Error: {e}")

# Test 3: Import from langgraph.constants
try:
    from langgraph.constants import END, START
    print("✓ Success: from langgraph.constants import END, START")
    print(f"  END = {END}")
    print(f"  START = {START}")
except ImportError as e:
    print(f"✗ Failed: from langgraph.constants import END, START")
    print(f"  Error: {e}")

# Test 4: Check what's available in langgraph module
try:
    import langgraph
    print("\nAvailable in langgraph module:")
    attrs = [attr for attr in dir(langgraph) if not attr.startswith('_')]
    for attr in attrs[:10]:  # Show first 10 attributes
        print(f"  - {attr}")
    if len(attrs) > 10:
        print(f"  ... and {len(attrs) - 10} more")
except ImportError as e:
    print(f"✗ Cannot import langgraph: {e}")

# Test 5: Check what's available in langgraph.graph module
try:
    import langgraph.graph
    print("\nAvailable in langgraph.graph module:")
    attrs = [attr for attr in dir(langgraph.graph) if not attr.startswith('_')]
    for attr in attrs[:10]:  # Show first 10 attributes
        print(f"  - {attr}")
    if len(attrs) > 10:
        print(f"  ... and {len(attrs) - 10} more")
except ImportError as e:
    print(f"✗ Cannot import langgraph.graph: {e}")
