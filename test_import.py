#!/usr/bin/env python3
"""Test script to verify agent.py imports correctly."""

import sys
sys.path.append(".")

try:
    from agent import app
    print("✓ Successfully imported app from agent.py")
    print(f"✓ App type: {type(app)}")
    print("✓ Agent.py is properly configured for LangGraph deployment")
except ImportError as e:
    print(f"✗ Import error: {e}")
except Exception as e:
    print(f"✗ Unexpected error: {e}")
