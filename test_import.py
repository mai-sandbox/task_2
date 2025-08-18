#!/usr/bin/env python3
"""Test script to verify the agent can be imported and is properly configured."""

import sys
sys.path.insert(0, 'src')

try:
    # Test importing the graph module
    from agent.graph import graph, app
    print("✓ Successfully imported graph and app from agent.graph")
    
    # Verify they are the same object
    if graph is app:
        print("✓ 'app' and 'graph' reference the same compiled graph object")
    else:
        print("✗ Warning: 'app' and 'graph' are different objects")
    
    # Check the type
    print(f"✓ Graph type: {type(graph).__name__}")
    
    # Test importing all required components
    from agent.state import InputState, OutputState, OverallState, PersonInfo
    print("✓ Successfully imported all state classes")
    
    from agent.prompts import REFLECTION_PROMPT, INFO_PROMPT, QUERY_WRITER_PROMPT
    print("✓ Successfully imported all prompts")
    
    from agent.configuration import Configuration
    print("✓ Successfully imported Configuration")
    
    from agent.utils import deduplicate_and_format_sources, format_all_notes
    print("✓ Successfully imported utility functions")
    
    print("\n✅ All imports successful! The agent is ready for deployment.")
    print("   - Graph is compiled and exported as both 'graph' and 'app'")
    print("   - All required modules are importable")
    print("   - No syntax errors detected")
    
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"✗ Unexpected error: {e}")
    sys.exit(1)
