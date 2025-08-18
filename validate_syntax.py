#!/usr/bin/env python3
"""
Validate syntax of all Python files in the project using py_compile.
"""

import os
import py_compile
import sys
from pathlib import Path

def validate_python_files():
    """Validate all Python files in the project."""
    project_root = Path(__file__).parent
    python_files = []
    failed_files = []
    
    # Find all Python files
    for root, dirs, files in os.walk(project_root):
        # Skip __pycache__ directories
        if '__pycache__' in root:
            continue
        
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                python_files.append(filepath)
    
    print(f"Found {len(python_files)} Python files to validate\n")
    print("Validating syntax with py_compile...")
    print("-" * 50)
    
    # Validate each file
    for filepath in sorted(python_files):
        relative_path = os.path.relpath(filepath, project_root)
        try:
            py_compile.compile(filepath, doraise=True)
            print(f"✓ {relative_path}")
        except py_compile.PyCompileError as e:
            print(f"✗ {relative_path}: {e}")
            failed_files.append(relative_path)
        except Exception as e:
            print(f"✗ {relative_path}: Unexpected error: {e}")
            failed_files.append(relative_path)
    
    print("-" * 50)
    
    # Summary
    if failed_files:
        print(f"\n❌ Syntax validation FAILED")
        print(f"   {len(failed_files)} file(s) have syntax errors:")
        for file in failed_files:
            print(f"   - {file}")
        return False
    else:
        print(f"\n✅ All {len(python_files)} Python files passed syntax validation!")
        return True

if __name__ == "__main__":
    success = validate_python_files()
    sys.exit(0 if success else 1)
