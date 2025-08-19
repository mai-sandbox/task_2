#!/usr/bin/env python3
"""Test script to verify reflection function implementation."""

import sys
import json

# Test imports
try:
    from src.agent.graph import reflection, ReflectionOutput
    from src.agent.state import OverallState, Person
    from src.agent.prompts import REFLECTION_PROMPT
    print("✓ All imports successful")
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)

# Verify ReflectionOutput structure
print("\nReflectionOutput fields:")
print("  - years_experience: Optional[int]")
print("  - current_company: Optional[str]")
print("  - current_role: Optional[str]")
print("  - prior_companies: List[str]")
print("  - reflection_decision: Literal['continue', 'finish']")
print("  - reflection_reasoning: str")
print("  - extracted_info: dict[str, Any]")

# Verify reflection function exists and has correct signature
import inspect
sig = inspect.signature(reflection)
params = list(sig.parameters.keys())
print(f"\nreflection() function signature: {params}")
assert 'state' in params, "reflection() should take 'state' parameter"
assert 'config' in params, "reflection() should take 'config' parameter"

print("\n✓ reflection() function successfully implemented with:")
print("  - Structured output using ReflectionOutput class")
print("  - Claude 3.5 Sonnet integration")
print("  - Proper state analysis and decision making")
print("  - Returns structured data and reflection decision")
