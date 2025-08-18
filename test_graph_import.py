#!/usr/bin/env python3
"""Test that the graph module can be imported after fixing the import path."""

try:
    from src.agent.graph import graph
    print("✓ Graph module imported successfully")
    print(f"Graph type: {type(graph)}")
    print(f"Graph object: {graph}")
    
    # Test that we can also import the agent app
    from agent import app
    print("✓ Agent app imported successfully")
    print(f"App type: {type(app)}")
    
    # Verify they're the same object
    if app is graph:
        print("✓ Agent app and graph are the same object (as expected)")
    else:
        print("⚠ Agent app and graph are different objects")
    
    print("\n✅ ALL IMPORTS SUCCESSFUL - LangGraph import issue is fixed!")
    
except ImportError as e:
    print(f"✗ Import failed: {e}")
    print("\n❌ LangGraph import issue still exists")
except Exception as e:
    print(f"✗ Unexpected error: {e}")
    print("\n❌ Unexpected error occurred")
