#!/usr/bin/env python3
"""Test script to validate all imports and graph compilation."""

import sys
import traceback

def test_imports():
    """Test all module imports."""
    try:
        print("Testing state imports...")
        from agent.state import OverallState, InputState, OutputState, Person
        print("✓ State imports successful")
        
        print("Testing prompts imports...")
        from agent.prompts import REFLECTION_PROMPT, INFO_PROMPT, QUERY_WRITER_PROMPT
        print("✓ Prompts imports successful")
        
        print("Testing configuration imports...")
        from agent.configuration import Configuration
        print("✓ Configuration imports successful")
        
        print("Testing utils imports...")
        from agent.utils import deduplicate_and_format_sources, format_all_notes
        print("✓ Utils imports successful")
        
        print("Testing graph imports...")
        from agent.graph import graph, builder, ReflectionOutput
        print("✓ Graph imports successful")
        
        return True
        
    except Exception as e:
        print(f"✗ Import error: {e}")
        traceback.print_exc()
        return False

def test_graph_compilation():
    """Test graph compilation."""
    try:
        print("Testing graph compilation...")
        from agent.graph import graph
        print("✓ Graph compilation successful")
        
        # Test graph structure
        print("Testing graph structure...")
        nodes = list(graph.nodes.keys())
        print(f"Graph nodes: {nodes}")
        
        expected_nodes = ["generate_queries", "research_person", "reflection"]
        for node in expected_nodes:
            if node in nodes:
                print(f"✓ Node '{node}' found")
            else:
                print(f"✗ Node '{node}' missing")
                return False
                
        return True
        
    except Exception as e:
        print(f"✗ Graph compilation error: {e}")
        traceback.print_exc()
        return False

def test_state_creation():
    """Test state object creation."""
    try:
        print("Testing state creation...")
        from agent.state import OverallState, Person
        
        # Create a test person
        person = Person(email="test@example.com", name="Test Person")
        print("✓ Person creation successful")
        
        # Create overall state
        state = OverallState(person=person)
        print("✓ OverallState creation successful")
        
        # Check extraction schema
        if state.extraction_schema:
            print("✓ Extraction schema present")
            schema_keys = list(state.extraction_schema.keys())
            print(f"Schema keys: {schema_keys}")
        else:
            print("✗ Extraction schema missing")
            return False
            
        return True
        
    except Exception as e:
        print(f"✗ State creation error: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Starting comprehensive import and compilation tests...\n")
    
    # Add src to path
    sys.path.insert(0, 'src')
    
    success = True
    
    # Run tests
    success &= test_imports()
    print()
    success &= test_graph_compilation()
    print()
    success &= test_state_creation()
    
    print("\n" + "="*50)
    if success:
        print("✓ ALL TESTS PASSED - System is ready for deployment!")
    else:
        print("✗ SOME TESTS FAILED - Issues need to be addressed")
    print("="*50)
