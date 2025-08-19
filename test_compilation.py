#!/usr/bin/env python3
"""Simple compilation test for final validation."""

import sys
sys.path.insert(0, 'src')

try:
    from agent.graph import graph
    print("✓ Graph compilation successful")
    
    # Test basic graph structure
    nodes = list(graph.nodes.keys())
    print(f"✓ Graph nodes: {nodes}")
    
    expected_nodes = ["generate_queries", "research_person", "reflection"]
    missing_nodes = [node for node in expected_nodes if node not in nodes]
    if missing_nodes:
        print(f"✗ Missing nodes: {missing_nodes}")
    else:
        print("✓ All expected nodes present")
        
except Exception as e:
    print(f"✗ Graph compilation failed: {e}")
    import traceback
    traceback.print_exc()
