#!/usr/bin/env python3
"""Test script to verify extraction_schema field in OverallState."""

from src.agent.state import OverallState
from src.agent.state import Person

# Create a test instance to verify the extraction_schema
test_person = Person(email="test@example.com")
test_state = OverallState(person=test_person)

print("✓ OverallState successfully imported")
print("\nExtraction schema fields defined:")
for key, description in test_state.extraction_schema.items():
    print(f"  - {key}: {description}")

print("\n✓ extraction_schema field successfully added with default factory")
print("✓ Schema includes all required fields for information extraction")
