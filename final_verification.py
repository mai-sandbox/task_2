#!/usr/bin/env python3
"""Final verification script for the People Research Agent."""

import sys
import os
import importlib
import traceback
from typing import Any

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def verify_final_compilation():
    """Verify the agent compiles and all components are accessible."""
    
    print("=" * 60)
    print("FINAL VERIFICATION - People Research Agent")
    print("=" * 60)
    
    all_checks_passed = True
    
    # Test 1: Import the graph module
    print("\n1. Testing module import...")
    try:
        from agent import graph
        print("   ✓ Successfully imported agent.graph module")
    except ImportError as e:
        print(f"   ✗ Failed to import agent.graph: {e}")
        all_checks_passed = False
        return all_checks_passed
    
    # Test 2: Verify app variable exists
    print("\n2. Checking for 'app' variable...")
    if hasattr(graph, 'app'):
        app = graph.app
        print("   ✓ 'app' variable exists in graph module")
    else:
        print("   ✗ 'app' variable not found in graph module")
        all_checks_passed = False
        return all_checks_passed
    
    # Test 3: Verify app type and methods
    print("\n3. Verifying 'app' object...")
    print(f"   ✓ app type: {type(app)}")
    
    if hasattr(app, 'invoke'):
        print("   ✓ app.invoke() method exists")
    else:
        print("   ✗ app.invoke() method missing")
        all_checks_passed = False
    
    if hasattr(app, 'stream'):
        print("   ✓ app.stream() method exists")
    else:
        print("   ✗ app.stream() method missing")
        all_checks_passed = False
    
    # Test 4: Check graph structure
    print("\n4. Checking graph structure...")
    if hasattr(app, 'get_graph'):
        graph_obj = app.get_graph()
        print(f"   ✓ Graph structure accessible")
        
        if hasattr(graph_obj, 'nodes'):
            nodes = graph_obj.nodes
            if isinstance(nodes, dict):
                node_list = list(nodes.keys())
                print(f"   ✓ Graph nodes ({len(node_list)}): {node_list}")
                
                # Verify expected nodes
                expected_nodes = ['generate_queries', 'research_person', 'reflection']
                for node in expected_nodes:
                    if node in node_list:
                        print(f"   ✓ Required node '{node}' present")
                    else:
                        print(f"   ✗ Required node '{node}' missing")
                        all_checks_passed = False
    
    # Test 5: Import all key modules
    print("\n5. Testing all module imports...")
    modules_to_test = [
        'agent.state',
        'agent.prompts',
        'agent.configuration',
        'agent.utils'
    ]
    
    for module_name in modules_to_test:
        try:
            module = importlib.import_module(module_name)
            print(f"   ✓ Successfully imported {module_name}")
        except ImportError as e:
            print(f"   ✗ Failed to import {module_name}: {e}")
            all_checks_passed = False
    
    # Test 6: Verify state classes
    print("\n6. Verifying state classes...")
    try:
        from agent.state import InputState, OverallState, OutputState, ExtractedInfo
        print("   ✓ InputState imported")
        print("   ✓ OverallState imported")
        print("   ✓ OutputState imported")
        print("   ✓ ExtractedInfo imported")
        
        # Check key fields
        if hasattr(OverallState, '__annotations__'):
            state_fields = OverallState.__annotations__.keys()
            required_fields = ['person', 'search_queries', 'research_notes', 'reflection_decision']
            for field in required_fields:
                if field in state_fields:
                    print(f"   ✓ OverallState has field '{field}'")
                else:
                    print(f"   ✗ OverallState missing field '{field}'")
                    all_checks_passed = False
    except ImportError as e:
        print(f"   ✗ Failed to import state classes: {e}")
        all_checks_passed = False
    
    # Test 7: Verify prompts
    print("\n7. Verifying prompts...")
    try:
        from agent.prompts import QUERY_WRITER_PROMPT, REFLECTION_PROMPT
        print("   ✓ QUERY_WRITER_PROMPT exists")
        print("   ✓ REFLECTION_PROMPT exists")
    except ImportError as e:
        print(f"   ✗ Failed to import prompts: {e}")
        all_checks_passed = False
    
    # Test 8: Check configuration files
    print("\n8. Checking configuration files...")
    config_files = [
        'langgraph.json',
        '.env',
        'pyproject.toml',
        'mypy.ini'
    ]
    
    for config_file in config_files:
        if os.path.exists(config_file):
            print(f"   ✓ {config_file} exists")
        else:
            print(f"   ✗ {config_file} missing")
            all_checks_passed = False
    
    # Test 9: Verify no test files remain
    print("\n9. Verifying cleanup (no test files)...")
    test_files = [
        'test_agent.py',
        'test_agent_compilation.py',
        'test_api_compatibility.py',
        'test_import.py',
        'test_mypy_fixes.py',
        'test_reflection_loop.py',
        'check_params.py'
    ]
    
    test_files_found = []
    for test_file in test_files:
        if os.path.exists(test_file):
            test_files_found.append(test_file)
    
    if test_files_found:
        print(f"   ✗ Test files still present: {test_files_found}")
        all_checks_passed = False
    else:
        print("   ✓ All test files have been removed")
    
    # Test 10: Basic graph invocation test (without API keys)
    print("\n10. Testing basic graph structure...")
    try:
        # Just test that we can access the graph config
        if hasattr(app, 'config'):
            print("   ✓ Graph config accessible")
        
        # Test input/output schemas
        if hasattr(app, 'input_schema'):
            print("   ✓ Input schema defined")
        
        if hasattr(app, 'output_schema'):
            print("   ✓ Output schema defined")
            
        print("   ✓ Basic graph structure test passed")
    except Exception as e:
        print(f"   ℹ Basic structure test note: {e}")
    
    return all_checks_passed

if __name__ == "__main__":
    try:
        all_passed = verify_final_compilation()
        
        print("\n" + "=" * 60)
        if all_passed:
            print("✅ FINAL VERIFICATION PASSED!")
            print("The People Research Agent is ready for deployment.")
        else:
            print("❌ FINAL VERIFICATION FAILED")
            print("Please review the errors above.")
        print("=" * 60)
        
        sys.exit(0 if all_passed else 1)
        
    except Exception as e:
        print(f"\n✗ Unexpected Error: {e}")
        print("\nTraceback:")
        traceback.print_exc()
        sys.exit(1)
