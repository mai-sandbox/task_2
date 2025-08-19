#!/usr/bin/env python3
"""Test script to verify agent compilation and app export."""

import sys
import traceback

def test_agent_compilation():
    """Test that the agent graph compiles and exports correctly."""
    print("=" * 60)
    print("Testing Agent Compilation")
    print("=" * 60)
    
    try:
        # Test 1: Import the graph module
        print("\n1. Testing module import...")
        from agent import graph
        print("   ✓ Successfully imported agent.graph module")
        
        # Test 2: Check if 'app' exists
        print("\n2. Checking for 'app' variable...")
        if hasattr(graph, 'app'):
            print("   ✓ 'app' variable exists in graph module")
        else:
            print("   ✗ 'app' variable not found in graph module")
            print("   Available attributes:", dir(graph))
            return False
        
        # Test 3: Get the app and check its type
        print("\n3. Verifying 'app' object...")
        app = graph.app
        print(f"   ✓ app type: {type(app)}")
        print(f"   ✓ app object: {app}")
        
        # Test 4: Check if app has expected methods
        print("\n4. Checking app methods...")
        expected_methods = ['invoke', 'stream']
        for method in expected_methods:
            if hasattr(app, method):
                print(f"   ✓ app.{method}() method exists")
            else:
                print(f"   ✗ app.{method}() method not found")
        
        # Test 5: Try to get graph structure
        print("\n5. Checking graph structure...")
        if hasattr(app, 'get_graph'):
            graph_obj = app.get_graph()
            print(f"   ✓ Graph structure accessible: {type(graph_obj)}")
            if hasattr(graph_obj, 'nodes'):
                print(f"   ✓ Graph nodes: {list(graph_obj.nodes())}")
        else:
            print("   ℹ get_graph() method not available")
        
        print("\n" + "=" * 60)
        print("✅ All tests passed! Agent compiled successfully.")
        print("=" * 60)
        return True
        
    except ImportError as e:
        print(f"\n✗ Import Error: {e}")
        print("\nTraceback:")
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n✗ Unexpected Error: {e}")
        print("\nTraceback:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_agent_compilation()
    sys.exit(0 if success else 1)
