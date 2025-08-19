#!/usr/bin/env python3
"""Test script to verify all imports work correctly."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    # Test state imports
    from agent.state import Person, PersonProfile, ReflectionDecision, InputState, OverallState, OutputState
    print("✅ All state models imported successfully")
    
    # Test configuration import
    from agent.configuration import Configuration
    print("✅ Configuration imported successfully")
    
    # Test prompts import
    from agent.prompts import QUERY_WRITER_PROMPT, INFO_PROMPT, REFLECTION_PROMPT
    print("✅ All prompts imported successfully")
    
    # Test utils import
    from agent.utils import deduplicate_and_format_sources, format_all_notes
    print("✅ Utils imported successfully")
    
    # Test graph import (this will test all dependencies)
    from agent.graph import graph, generate_queries, research_person, reflection
    print("✅ Graph and all functions imported successfully")
    
    print("\n🎉 All imports successful! No import errors found.")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    sys.exit(1)
