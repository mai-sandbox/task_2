#!/usr/bin/env python
"""Test script to verify agent imports correctly."""

try:
    from agent import app
    print(f"✓ Successfully imported app from agent module")
    print(f"✓ app type: {type(app)}")
    print(f"✓ app object: {app}")
    print("\nAgent compilation successful!")
except ImportError as e:
    print(f"✗ Import error: {e}")
    exit(1)
except Exception as e:
    print(f"✗ Unexpected error: {e}")
    exit(1)
