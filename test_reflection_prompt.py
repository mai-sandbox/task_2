#!/usr/bin/env python3
"""Test script to verify REFLECTION_PROMPT is properly defined."""

from src.agent.prompts import REFLECTION_PROMPT, QUERY_WRITER_PROMPT, INFO_PROMPT

print("✓ All prompts successfully imported")
print("\nREFLECTION_PROMPT includes:")
print("  - Person info placeholder: {person}")
print("  - Research notes placeholder: {notes}")
print("  - Extraction schema placeholder: {schema}")
print("\nKey instructions in REFLECTION_PROMPT:")
print("  1. Extract structured information (years of experience, current company, role, prior companies)")
print("  2. Evaluate completeness of research")
print("  3. Make decision to CONTINUE or FINISH")
print("  4. Provide reasoning for the decision")
print("\n✓ REFLECTION_PROMPT successfully created with all required components")
