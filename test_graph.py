#!/usr/bin/env python3
"""Test script to verify the graph compiles correctly."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from agent.graph import graph
    print("✅ Graph imported successfully")
    
    # Check if graph is compiled
    if graph:
        print("✅ Graph compiled successfully")
        print(f"Graph type: {type(graph)}")
        
        # Check nodes
        if hasattr(graph, 'nodes'):
            print(f"Graph nodes: {graph.nodes}")
    else:
        print("❌ Graph is None or not compiled")
        
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
