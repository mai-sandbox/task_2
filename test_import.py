#!/usr/bin/env python3
"""Test script to verify graph compilation."""

import sys
sys.path.append('src')

try:
    from agent.graph import graph
    print("✅ Graph imported successfully!")
    
    # Test that the graph has the expected nodes
    nodes = list(graph.nodes.keys())
    expected_nodes = ['generate_queries', 'research_person', 'reflection']
    
    for node in expected_nodes:
        if node in nodes:
            print(f"✅ Node '{node}' found in graph")
        else:
            print(f"❌ Node '{node}' missing from graph")
    
    print("✅ Graph compilation test completed successfully!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Graph compilation error: {e}")
    sys.exit(1)
