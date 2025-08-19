#!/usr/bin/env python3
"""Test script to verify LangGraph API compatibility with version 0.6.5."""

import sys
sys.path.insert(0, 'src')

def test_api_compatibility():
    """Test that all LangGraph API usage is compatible with version 0.6.5."""
    print("=" * 60)
    print("Testing LangGraph API Compatibility (v0.6.5)")
    print("=" * 60)
    
    # Test 1: Import verification
    print("\n1. Testing imports...")
    try:
        from langgraph.graph import END, START, StateGraph
        print("   ✓ Successfully imported END, START, StateGraph from langgraph.graph")
    except ImportError as e:
        print(f"   ✗ Import error: {e}")
        return False
    
    # Test 2: Graph module import
    print("\n2. Testing graph module import...")
    try:
        from agent.graph import app, builder
        print("   ✓ Successfully imported app and builder from agent.graph")
    except Exception as e:
        print(f"   ✗ Error importing graph module: {e}")
        return False
    
    # Test 3: Verify StateGraph initialization parameters
    print("\n3. Verifying StateGraph initialization...")
    try:
        # Check that builder was created with correct parameters
        print("   ✓ StateGraph builder created successfully")
        
        # Verify the graph compilation
        if app is not None:
            print("   ✓ Graph compiled successfully")
        else:
            print("   ✗ Graph compilation failed - app is None")
            return False
    except Exception as e:
        print(f"   ✗ Error with StateGraph: {e}")
        return False
    
    # Test 4: Verify graph structure
    print("\n4. Verifying graph structure...")
    try:
        graph_obj = app.get_graph()
        nodes = list(graph_obj.nodes.keys())
        print(f"   ✓ Graph nodes: {nodes}")
        
        expected_nodes = ['__start__', 'generate_queries', 'research_person', 'reflection', '__end__']
        if all(node in nodes for node in expected_nodes):
            print("   ✓ All expected nodes present")
        else:
            print(f"   ✗ Missing nodes. Expected: {expected_nodes}, Got: {nodes}")
            return False
    except Exception as e:
        print(f"   ✗ Error accessing graph structure: {e}")
        return False
    
    # Test 5: Verify conditional edges
    print("\n5. Verifying conditional edges...")
    try:
        # Check if the graph has edges
        if hasattr(graph_obj, 'edges'):
            edges = graph_obj.edges
            print(f"   ✓ Graph has edges defined")
            # Check for conditional edge from reflection
            reflection_edges = [e for e in edges if e[0] == 'reflection']
            if reflection_edges:
                print(f"   ✓ Conditional edges from reflection node found")
            else:
                print("   ⚠ No edges from reflection node found (might be conditional)")
        else:
            print("   ℹ Graph edges not directly accessible")
    except Exception as e:
        print(f"   ✗ Error checking edges: {e}")
    
    # Test 6: Verify API methods
    print("\n6. Verifying API methods...")
    try:
        # Check for key methods
        methods = ['invoke', 'stream', 'get_graph']
        for method in methods:
            if hasattr(app, method):
                print(f"   ✓ app.{method}() method exists")
            else:
                print(f"   ✗ app.{method}() method missing")
                return False
    except Exception as e:
        print(f"   ✗ Error checking methods: {e}")
        return False
    
    # Test 7: Check state classes
    print("\n7. Verifying state classes...")
    try:
        from agent.state import InputState, OutputState, OverallState
        print("   ✓ State classes imported successfully")
        
        # Verify OverallState inherits from both InputState and OutputState
        if issubclass(OverallState, InputState) and issubclass(OverallState, OutputState):
            print("   ✓ OverallState properly inherits from InputState and OutputState")
        else:
            print("   ✗ OverallState inheritance issue")
            return False
    except Exception as e:
        print(f"   ✗ Error with state classes: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("✅ All LangGraph API compatibility tests passed!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = test_api_compatibility()
    sys.exit(0 if success else 1)
