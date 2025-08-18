#!/usr/bin/env python3
"""Comprehensive agent compilation and import test."""

import sys
import traceback

def test_imports():
    """Test that all modules can be imported."""
    print("=" * 60)
    print("AGENT COMPILATION AND IMPORT TEST")
    print("=" * 60)
    
    all_success = True
    
    # Test 1: Import core dependencies
    print("\n1. Testing core dependency imports...")
    print("-" * 40)
    try:
        from langgraph.graph import END, START, StateGraph
        print("  ✓ LangGraph imports successful")
        from langchain_anthropic import ChatAnthropic
        print("  ✓ LangChain Anthropic imports successful")
        from tavily import AsyncTavilyClient
        print("  ✓ Tavily imports successful")
    except ImportError as e:
        print(f"  ✗ Core dependency import failed: {e}")
        all_success = False
    
    # Test 2: Import agent modules
    print("\n2. Testing agent module imports...")
    print("-" * 40)
    try:
        from src.agent.state import Person, InputState, OutputState, OverallState
        print("  ✓ State classes imported successfully")
        from src.agent.configuration import Configuration
        print("  ✓ Configuration imported successfully")
        from src.agent.prompts import QUERY_WRITER_PROMPT, INFO_PROMPT, REFLECTION_PROMPT
        print("  ✓ Prompts imported successfully")
        from src.agent.utils import deduplicate_and_format_sources, format_all_notes
        print("  ✓ Utils imported successfully")
    except ImportError as e:
        print(f"  ✗ Agent module import failed: {e}")
        all_success = False
    
    # Test 3: Import and verify graph module
    print("\n3. Testing graph module import and compilation...")
    print("-" * 40)
    try:
        from src.agent.graph import graph
        print("  ✓ Graph module imported successfully")
        print(f"  ✓ Graph type: {type(graph)}")
        
        # Check graph attributes
        if hasattr(graph, 'nodes'):
            print(f"  ✓ Graph has nodes: {list(graph.nodes.keys()) if hasattr(graph.nodes, 'keys') else 'yes'}")
        if hasattr(graph, 'invoke'):
            print("  ✓ Graph has invoke method (ready for execution)")
        if hasattr(graph, 'stream'):
            print("  ✓ Graph has stream method")
            
    except ImportError as e:
        print(f"  ✗ Graph import failed: {e}")
        all_success = False
    except Exception as e:
        print(f"  ✗ Graph verification failed: {e}")
        all_success = False
    
    # Test 4: Import agent app
    print("\n4. Testing agent.py app export...")
    print("-" * 40)
    try:
        from agent import app
        print("  ✓ Agent app imported successfully")
        print(f"  ✓ App type: {type(app)}")
        
        # Verify app is the same as graph
        from src.agent.graph import graph
        if app is graph:
            print("  ✓ App correctly references the compiled graph")
        else:
            print("  ⚠ App and graph are different objects")
            
    except ImportError as e:
        print(f"  ✗ Agent app import failed: {e}")
        all_success = False
    
    # Test 5: Test instantiation of state classes
    print("\n5. Testing state class instantiation...")
    print("-" * 40)
    try:
        from src.agent.state import Person, InputState, OutputState, OverallState
        
        # Create a test person
        person = Person(
            name="Test User",
            email="test@example.com",
            company="Test Company",
            linkedin="https://linkedin.com/in/test"
        )
        print(f"  ✓ Person created: {person.name}")
        
        # Create input state
        input_state = InputState(person=person)
        print(f"  ✓ InputState created with person: {input_state.person.name}")
        
        # Create output state
        output_state = OutputState(
            years_of_experience=5,
            current_company="Test Corp",
            role="Software Engineer"
        )
        print(f"  ✓ OutputState created with {output_state.years_of_experience} years experience")
        
        # Create overall state
        overall_state = OverallState(
            person=person,
            search_queries=["test query"],
            completed_notes=["test note"]
        )
        print("  ✓ OverallState created successfully")
        
    except Exception as e:
        print(f"  ✗ State instantiation failed: {e}")
        traceback.print_exc()
        all_success = False
    
    # Test 6: Verify configuration
    print("\n6. Testing configuration...")
    print("-" * 40)
    try:
        from src.agent.configuration import Configuration
        
        config = Configuration()
        print(f"  ✓ Default configuration created")
        print(f"    - max_search_queries: {config.max_search_queries}")
        print(f"    - max_search_results: {config.max_search_results}")
        
        # Test from_runnable_config
        from langchain_core.runnables import RunnableConfig
        runnable_config = RunnableConfig(
            configurable={"max_search_queries": 5}
        )
        config2 = Configuration.from_runnable_config(runnable_config)
        print(f"  ✓ Configuration from RunnableConfig: max_search_queries={config2.max_search_queries}")
        
    except Exception as e:
        print(f"  ✗ Configuration test failed: {e}")
        all_success = False
    
    print("\n" + "=" * 60)
    
    if all_success:
        print("✅ ALL TESTS PASSED - AGENT COMPILES AND IMPORTS SUCCESSFULLY")
        print("\nThe agent is ready for deployment and execution.")
    else:
        print("❌ SOME TESTS FAILED - Please review the errors above")
        return 1
    
    print("=" * 60)
    return 0

if __name__ == "__main__":
    sys.exit(test_imports())

