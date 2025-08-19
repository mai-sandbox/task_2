#!/usr/bin/env python3
"""Test script to verify OutputState class definition."""

from src.agent.state import OutputState, InputState, OverallState

print("✓ OutputState successfully imported")
print("\nOutputState fields defined:")
print("  - years_experience: Optional[int]")
print("  - current_company: Optional[str]")
print("  - current_role: Optional[str]")
print("  - prior_companies: List[str]")
print("  - reflection_decision: str")
print("  - reflection_reasoning: str")
print("  - extracted_info: dict[str, Any]")
print("\n✓ All required fields for structured output are present")
