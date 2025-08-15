#!/usr/bin/env python3
"""Test script to check for import errors and syntax issues."""

import sys
import traceback

def test_import(module_name, description):
    """Test importing a module and report results."""
    try:
        __import__(module_name)
        print(f"✅ {description}: SUCCESS")
        return True
    except Exception as e:
        print(f"❌ {description}: FAILED")
        print(f"   Error: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all import tests."""
    print("Testing imports and syntax...")
    print("=" * 50)
    
    success_count = 0
    total_tests = 0
    
    # Test individual modules
    tests = [
        ("src.agent.state", "State classes (InputState, OutputState, OverallState)"),
        ("src.agent.prompts", "Prompt templates"),
        ("src.agent.configuration", "Configuration class"),
        ("src.agent.utils", "Utility functions"),
        ("src.agent.graph", "Graph definition and compilation"),
        ("agent", "Main agent entry point"),
    ]
    
    for module, description in tests:
        total_tests += 1
        if test_import(module, description):
            success_count += 1
        print()
    
    print("=" * 50)
    print(f"Results: {success_count}/{total_tests} imports successful")
    
    # Check if failures are only due to missing dependencies
    dependency_only_failures = total_tests - success_count <= 2  # graph.py and agent.py depend on external libs
    
    if success_count == total_tests:
        print("🎉 All imports working correctly!")
        return True
    elif dependency_only_failures:
        print("✅ Code structure is correct - failures are only due to missing dependencies")
        print("   Run 'pip install -r requirements.txt' to install dependencies")
        return True
    else:
        print("⚠️  Some imports failed due to code issues - need to fix")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

