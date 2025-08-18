#!/usr/bin/env python3
"""Test script to verify the graph module can be imported without errors."""

try:
    from src.agent.graph import graph
    print("✓ Graph module imported successfully")
    print(f"✓ Graph type: {type(graph)}")
    print("✓ No import errors detected")
except ImportError as e:
    print(f"✗ Import error: {e}")
    exit(1)
except AttributeError as e:
    print(f"✗ Attribute error: {e}")
    exit(1)
except Exception as e:
    print(f"✗ Unexpected error: {e}")
    exit(1)
