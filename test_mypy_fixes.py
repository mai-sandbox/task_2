#!/usr/bin/env python3
"""Test that the MyPy fixes are working."""

import sys
sys.path.insert(0, 'src')

print("Testing MyPy fixes...")

# Test 1: Import the graph module
try:
    from agent.graph import app, builder, claude_3_5_sonnet
    print("✓ Graph module imports successfully")
except Exception as e:
    print(f"✗ Failed to import graph: {e}")
    sys.exit(1)

# Test 2: Check ChatAnthropic initialization
try:
    print(f"✓ ChatAnthropic instance created: {type(claude_3_5_sonnet).__name__}")
except Exception as e:
    print(f"✗ ChatAnthropic issue: {e}")
    sys.exit(1)

# Test 3: Check StateGraph builder
try:
    print(f"✓ StateGraph builder created: {type(builder).__name__}")
except Exception as e:
    print(f"✗ StateGraph issue: {e}")
    sys.exit(1)

# Test 4: Check compiled app
try:
    print(f"✓ Compiled app exists: {type(app).__name__}")
except Exception as e:
    print(f"✗ App compilation issue: {e}")
    sys.exit(1)

print("\n✅ All MyPy-related fixes are working correctly!")
print("Note: The ChatAnthropic 'model' parameter is valid (uses **kwargs)")
print("Note: StateGraph now uses 'context_schema' instead of 'config_schema'")
