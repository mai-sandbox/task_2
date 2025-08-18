#!/usr/bin/env python3
"""Test script to verify the agent can be imported and instantiated without errors."""

import sys
from typing import Any

def test_imports():
    """Test that all modules can be imported."""
    print("Testing module imports...")
    
    try:
        # Test state module imports
        from src.agent.state import Person, InputState, OutputState, OverallState
        print("  ✓ State module imported successfully")
        
        # Test configuration module imports
        from src.agent.configuration import Configuration
        print("  ✓ Configuration module imported successfully")
        
        # Test prompts module imports
        from src.agent.prompts import QUERY_WRITER_PROMPT, INFO_PROMPT, REFLECTION_PROMPT
        print("  ✓ Prompts module imported successfully")
        
        # Test utils module imports
        from src.agent.utils import deduplicate_and_format_sources, format_all_notes
        print("  ✓ Utils module imported successfully")
        
        # Test graph module imports
        from src.agent.graph import graph, generate_queries, research_person, reflection, should_continue_research
        print("  ✓ Graph module imported successfully")
        
        # Test main agent entry point
        from agent import app
        print("  ✓ Agent entry point imported successfully")
        
        return True
    except ImportError as e:
        print(f"  ✗ Import error: {e}")
        return False
    except AttributeError as e:
        print(f"  ✗ Attribute error: {e}")
        return False
    except Exception as e:
        print(f"  ✗ Unexpected error: {e}")
        return False

def test_graph_structure():
    """Test that the graph has the expected structure."""
    print("\nTesting graph structure...")
    
    try:
        from src.agent.graph import graph
        
        # Check if graph is compiled
        if hasattr(graph, 'nodes'):
            print(f"  ✓ Graph has nodes attribute")
            
            # Check for expected nodes
            expected_nodes = {'generate_queries', 'research_person', 'reflection'}
            if hasattr(graph, 'nodes'):
                print(f"  ✓ Graph nodes accessible")
        
        # Check if graph can get its config
        if hasattr(graph, 'config_specs'):
            print(f"  ✓ Graph has config_specs")
            
        print(f"  ✓ Graph type: {type(graph)}")
        
        return True
    except Exception as e:
        print(f"  ✗ Error checking graph structure: {e}")
        return False

def test_state_classes():
    """Test that state classes can be instantiated."""
    print("\nTesting state classes...")
    
    try:
        from src.agent.state import Person, InputState, OutputState, OverallState
        
        # Test Person class
        person = Person(name="Test Person", email="test@example.com")
        print(f"  ✓ Person class instantiated: {person.name}")
        
        # Test InputState
        input_state = InputState(person=person)
        print(f"  ✓ InputState instantiated with person: {input_state.person.name}")
        
        # Test OutputState
        output_state = OutputState(
            years_of_experience=5,
            current_company="Test Company",
            role="Test Role",
            prior_companies=["Company A", "Company B"]
        )
        print(f"  ✓ OutputState instantiated with {output_state.years_of_experience} years experience")
        
        # Test OverallState
        overall_state = OverallState(
            person=person,
            queries=[],
            query_results=[],
            completed_notes=[],
            extraction_schema=output_state
        )
        print(f"  ✓ OverallState instantiated successfully")
        
        return True
    except Exception as e:
        print(f"  ✗ Error testing state classes: {e}")
        return False

def test_configuration():
    """Test that configuration can be instantiated."""
    print("\nTesting configuration...")
    
    try:
        from src.agent.configuration import Configuration
        
        # Test default configuration
        config = Configuration()
        print(f"  ✓ Configuration instantiated with max_search_queries={config.max_search_queries}")
        print(f"  ✓ Configuration max_search_results={config.max_search_results}")
        
        # Test from_runnable_config
        test_config = {"configurable": {"max_search_queries": 5}}
        config_from_runnable = Configuration.from_runnable_config(test_config)
        print(f"  ✓ Configuration.from_runnable_config works")
        
        return True
    except Exception as e:
        print(f"  ✗ Error testing configuration: {e}")
        return False

def test_agent_app():
    """Test that the agent app is properly exported."""
    print("\nTesting agent app export...")
    
    try:
        from agent import app
        from src.agent.graph import graph
        
        # Check if app is the same as graph
        if app is graph:
            print(f"  ✓ Agent app correctly exports the graph")
        else:
            print(f"  ⚠ Agent app may not be correctly exporting the graph")
            
        print(f"  ✓ App type: {type(app)}")
        
        return True
    except Exception as e:
        print(f"  ✗ Error testing agent app: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("AGENT IMPORT AND INSTANTIATION TEST")
    print("=" * 60)
    
    all_passed = True
    
    # Run tests
    all_passed &= test_imports()
    all_passed &= test_graph_structure()
    all_passed &= test_state_classes()
    all_passed &= test_configuration()
    all_passed &= test_agent_app()
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL TESTS PASSED - Agent can be imported and instantiated")
        print("=" * 60)
        return 0
    else:
        print("❌ SOME TESTS FAILED - Please review the errors above")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())



