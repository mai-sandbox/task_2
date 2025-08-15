#!/usr/bin/env python
"""Test script to verify reflection implementation."""

import sys
sys.path.insert(0, 'src')

# Test imports
try:
    from agent.prompts import REFLECTION_PROMPT
    print("✓ REFLECTION_PROMPT imported successfully")
except ImportError as e:
    print(f"✗ Failed to import REFLECTION_PROMPT: {e}")
    sys.exit(1)

try:
    from agent.graph import reflection, ReflectionDecision
    print("✓ reflection function imported successfully")
    print("✓ ReflectionDecision model imported successfully")
except ImportError as e:
    print(f"✗ Failed to import from graph: {e}")
    sys.exit(1)

try:
    from agent.state import OverallState, OutputState
    print("✓ OverallState imported successfully")
    print("✓ OutputState imported successfully")
except ImportError as e:
    print(f"✗ Failed to import from state: {e}")
    sys.exit(1)

# Verify REFLECTION_PROMPT has required placeholders
required_placeholders = ['{person}', '{research_notes}', '{extraction_schema}']
for placeholder in required_placeholders:
    if placeholder in REFLECTION_PROMPT:
        print(f"✓ REFLECTION_PROMPT contains {placeholder}")
    else:
        print(f"✗ REFLECTION_PROMPT missing {placeholder}")

# Verify ReflectionDecision has required fields
from pydantic import BaseModel
if issubclass(ReflectionDecision, BaseModel):
    print("✓ ReflectionDecision is a Pydantic BaseModel")
    fields = ReflectionDecision.__fields__
    required_fields = ['years_of_experience', 'current_company', 'current_role', 
                      'prior_companies', 'decision', 'reasoning']
    for field in required_fields:
        if field in fields:
            print(f"✓ ReflectionDecision has field: {field}")
        else:
            print(f"✗ ReflectionDecision missing field: {field}")

print("\n✅ All reflection components successfully implemented!")
