#!/usr/bin/env python3
"""
Test script to verify the People Research Agent imports correctly and compiles without errors.

This script validates:
1. All imports resolve correctly
2. The graph compiles successfully
3. State classes are properly defined
4. Basic functionality is accessible
"""

import sys
import traceback
from typing import Dict, Any


def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...")

    try:
        # Test core agent import
        from agent import app

        print("✅ Successfully imported agent.app")

        # Test individual components
        from src.agent.state import InputState, OutputState, OverallState

        print("✅ Successfully imported state classes")

        from src.agent.graph import graph

        print("✅ Successfully imported graph")

        from src.agent.prompts import REFLECTION_PROMPT

        print("✅ Successfully imported REFLECTION_PROMPT")

        from src.agent.configuration import Configuration

        print("✅ Successfully imported Configuration")

        return True, app, graph

    except Exception as e:
        print(f"❌ Import failed: {e}")
        traceback.print_exc()
        return False, None, None


def test_graph_compilation(graph):
    """Test that the graph compiles successfully."""
    print("\nTesting graph compilation...")

    try:
        # Verify graph is compiled
        if graph is None:
            print("❌ Graph is None")
            return False

        # Check if graph has expected attributes
        if not hasattr(graph, "invoke"):
            print("❌ Graph missing invoke method")
            return False

        print("✅ Graph compiled successfully with invoke method")
        return True

    except Exception as e:
        print(f"❌ Graph compilation test failed: {e}")
        traceback.print_exc()
        return False


def test_state_classes():
    """Test that state classes are properly defined."""
    print("\nTesting state classes...")

    try:
        from src.agent.state import InputState, OutputState, OverallState

        # Test InputState
        input_state = InputState(
            person={"email": "test@example.com"}, user_notes="Test notes"
        )
        print("✅ InputState can be instantiated")

        # Test OutputState fields
        output_fields = OutputState.__annotations__.keys()
        expected_fields = {
            "years_experience",
            "current_company",
            "role",
            "prior_companies",
            "satisfaction_score",
            "missing_info",
            "needs_more_research",
            "reasoning",
        }

        if expected_fields.issubset(output_fields):
            print("✅ OutputState has all required fields")
        else:
            missing = expected_fields - set(output_fields)
            print(f"❌ OutputState missing fields: {missing}")
            return False

        # Test OverallState
        overall_state = OverallState(
            person={"email": "test@example.com"},
            user_notes="Test notes",
            search_queries=[],
            completed_notes=[],
            extraction_schema={},
        )
        print("✅ OverallState can be instantiated")

        return True

    except Exception as e:
        print(f"❌ State class test failed: {e}")
        traceback.print_exc()
        return False


def test_prompt_availability():
    """Test that prompts are properly defined."""
    print("\nTesting prompt availability...")

    try:
        from src.agent.prompts import (
            REFLECTION_PROMPT,
            INFO_PROMPT,
            QUERY_WRITER_PROMPT,
        )

        if not REFLECTION_PROMPT or not isinstance(REFLECTION_PROMPT, str):
            print("❌ REFLECTION_PROMPT is not properly defined")
            return False

        if "{completed_notes}" not in REFLECTION_PROMPT:
            print("❌ REFLECTION_PROMPT missing required placeholder")
            return False

        print("✅ REFLECTION_PROMPT is properly defined")
        print("✅ All prompts imported successfully")

        return True

    except Exception as e:
        print(f"❌ Prompt test failed: {e}")
        traceback.print_exc()
        return False


def main():
    """Run all tests and report results."""
    print("=" * 60)
    print("People Research Agent - Import and Compilation Test")
    print("=" * 60)

    all_tests_passed = True

    # Test imports
    imports_ok, app, graph = test_imports()
    all_tests_passed &= imports_ok

    if imports_ok:
        # Test graph compilation
        graph_ok = test_graph_compilation(graph)
        all_tests_passed &= graph_ok

        # Test state classes
        state_ok = test_state_classes()
        all_tests_passed &= state_ok

        # Test prompts
        prompt_ok = test_prompt_availability()
        all_tests_passed &= prompt_ok

    print("\n" + "=" * 60)
    if all_tests_passed:
        print("🎉 ALL TESTS PASSED! Agent is ready for deployment.")
        print("✅ Imports work correctly")
        print("✅ Graph compiles successfully")
        print("✅ State classes are properly defined")
        print("✅ Prompts are available and formatted correctly")
    else:
        print("❌ SOME TESTS FAILED! Please fix the issues above.")
        sys.exit(1)

    print("=" * 60)


if __name__ == "__main__":
    main()
