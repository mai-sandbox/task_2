#!/usr/bin/env python3
"""Final compilation check for all Python modules."""

import py_compile
import os
import sys
from pathlib import Path

def compile_file(filepath):
    """Compile a single Python file and return success status."""
    try:
        py_compile.compile(filepath, doraise=True)
        return True, None
    except py_compile.PyCompileError as e:
        return False, str(e)
    except Exception as e:
        return False, str(e)

def main():
    """Run compilation check on all Python files."""
    print("=" * 60)
    print("FINAL COMPILATION CHECK")
    print("=" * 60)
    
    # List of files to check
    files_to_check = [
        "src/agent/state.py",
        "src/agent/configuration.py",
        "src/agent/prompts.py",
        "src/agent/utils.py",
        "src/agent/graph.py",
        "agent.py",
        "test_import.py"
    ]
    
    all_success = True
    results = []
    
    print("\nChecking Python syntax and compilation...")
    print("-" * 40)
    
    for filepath in files_to_check:
        if os.path.exists(filepath):
            success, error = compile_file(filepath)
            if success:
                print(f"  ✓ {filepath} - Compiled successfully")
                results.append((filepath, True, None))
            else:
                print(f"  ✗ {filepath} - Compilation failed: {error}")
                results.append((filepath, False, error))
                all_success = False
        else:
            print(f"  ⚠ {filepath} - File not found")
            results.append((filepath, False, "File not found"))
            all_success = False
    
    print("\n" + "=" * 60)
    
    # Summary
    successful = sum(1 for _, success, _ in results if success)
    failed = len(results) - successful
    
    print(f"SUMMARY: {successful}/{len(results)} files compiled successfully")
    
    if all_success:
        print("✅ ALL PYTHON FILES COMPILE SUCCESSFULLY")
        print("\nNote: Import errors for external dependencies (like")
        print("langchain_anthropic) are expected in a test environment")
        print("without all runtime dependencies installed.")
    else:
        print(f"❌ {failed} FILE(S) FAILED TO COMPILE")
        print("\nFailed files:")
        for filepath, success, error in results:
            if not success:
                print(f"  - {filepath}: {error}")
    
    print("=" * 60)
    
    return 0 if all_success else 1

if __name__ == "__main__":
    sys.exit(main())
