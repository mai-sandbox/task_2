#!/usr/bin/env python3
"""Verify that all required dependencies are installed."""

import sys

def check_import(module_name, package_name=None):
    """Check if a module can be imported."""
    if package_name is None:
        package_name = module_name
    try:
        __import__(module_name)
        print(f"  ✓ {package_name} imported successfully")
        return True
    except ImportError as e:
        print(f"  ✗ {package_name} import failed: {e}")
        return False

def main():
    """Check all required dependencies."""
    print("=" * 60)
    print("DEPENDENCY VERIFICATION")
    print("=" * 60)
    
    dependencies = [
        ("langgraph", "LangGraph"),
        ("langchain_anthropic", "LangChain Anthropic"),
        ("langchain_community", "LangChain Community"),
        ("tavily", "Tavily Python"),
        ("langsmith", "LangSmith"),
    ]
    
    print("\nChecking required dependencies...")
    print("-" * 40)
    
    all_success = True
    for module_name, package_name in dependencies:
        if not check_import(module_name, package_name):
            all_success = False
    
    print("\n" + "=" * 60)
    
    if all_success:
        print("✅ ALL DEPENDENCIES INSTALLED SUCCESSFULLY")
    else:
        print("❌ SOME DEPENDENCIES ARE MISSING")
    
    print("=" * 60)
    
    return 0 if all_success else 1

if __name__ == "__main__":
    sys.exit(main())
