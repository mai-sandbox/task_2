#!/usr/bin/env python3
"""Verify syntax and structure without imports."""

import ast
import sys

def check_syntax(filepath):
    """Check if a Python file has valid syntax."""
    try:
        with open(filepath, 'r') as f:
            source = f.read()
        ast.parse(source)
        return True, "Valid syntax"
    except SyntaxError as e:
        return False, f"Syntax error at line {e.lineno}: {e.msg}"
    except Exception as e:
        return False, str(e)

# Files to check
files_to_check = [
    "src/agent/state.py",
    "src/agent/prompts.py",
    "src/agent/graph.py",
    "src/agent/configuration.py",
    "src/agent/utils.py",
]

print("Checking Python syntax for all files...")
print("-" * 50)

all_valid = True
for filepath in files_to_check:
    valid, message = check_syntax(filepath)
    status = "✓" if valid else "✗"
    print(f"{status} {filepath}: {message}")
    if not valid:
        all_valid = False

print("-" * 50)
if all_valid:
    print("✅ All files have valid Python syntax!")
else:
    print("❌ Some files have syntax errors. Please fix them.")
    sys.exit(1)
