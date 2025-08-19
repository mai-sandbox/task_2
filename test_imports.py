#!/usr/bin/env python3
"""Test script to validate imports and graph compilation."""

import sys
import traceback

def test_imports():
    """Test all module imports."""
    try:
        print("Testing imports...")
        
        # Test state imports
        from agent.state import InputState, OutputState, OverallState, Person
        print("✅ State classes imported successfully")
        
        # Test prompts imports
        from agent.prompts import REFLECTION_PROMPT, INFO_PROMPT, QUERY_WRITER_PROMPT
        print("✅ Prompts imported successfully")
        
        # Test configuration imports
        from agent.configuration import Configuration
        print("✅ Configuration imported successfully")
        
        # Test utils imports
        from agent.utils import deduplicate_and_format_sources, format_all_notes
        print("✅ Utils imported successfully")
        
        # Test graph imports
        from agent.graph import graph, generate_queries, research_person, reflection, should_continue
        print("✅ Graph components imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        traceback.print_exc()
        return False

def test_graph_compilation():
    """Test graph compilation."""
    try:
        print("\nTesting graph compilation...")
        from agent.graph import graph
        print("✅ Graph compiled successfully")
        
        # Test graph structure
        print(f"Graph nodes: {list(graph.nodes.keys())}")
        print(f"Graph has {len(graph.nodes)} nodes")
        
        return True
        
    except Exception as e:
        print(f"❌ Graph compilation error: {e}")
        traceback.print_exc()
        return False

def test_state_consistency():
    """Test state class consistency."""
    try:
        print("\nTesting state consistency...")
        from agent.state import InputState, OutputState, OverallState
        
        # Test OverallState has required fields
        required_fields = ['extraction_schema', 'reflection_result', 'needs_more_research', 'reflection_reasoning']
        for field in required_fields:
            if not hasattr(OverallState, '__dataclass_fields__') or field not in OverallState.__dataclass_fields__:
                print(f"❌ Missing field in OverallState: {field}")
                return False
        
        print("✅ State consistency validated")
        return True
        
    except Exception as e:
        print(f"❌ State consistency error: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Running code validation tests...\n")
    
    success = True
    success &= test_imports()
    success &= test_graph_compilation()
    success &= test_state_consistency()
    
    if success:
        print("\n🎉 All tests passed! Code validation successful.")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        sys.exit(1)
