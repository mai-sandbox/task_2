#!/usr/bin/env python3
"""Test script to validate all imports and basic functionality."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test all critical imports."""
    try:
        # Test state imports
        from agent.state import Person, InputState, OutputState, OverallState
        print("✓ State classes imported successfully")
        
        # Test configuration import
        from agent.configuration import Configuration
        print("✓ Configuration imported successfully")
        
        # Test utils import
        from agent.utils import deduplicate_and_format_sources, format_all_notes
        print("✓ Utils imported successfully")
        
        # Test prompts import
        from agent.prompts import QUERY_WRITER_PROMPT, INFO_PROMPT, REFLECTION_PROMPT
        print("✓ Prompts imported successfully")
        
        # Test graph import (this is the most complex one)
        from agent.graph import graph, generate_queries, research_person, reflection
        print("✓ Graph and functions imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

def test_state_creation():
    """Test creating state objects."""
    try:
        from agent.state import Person, OverallState
        
        # Test Person creation
        person = Person(email="test@example.com", name="Test User")
        print("✓ Person object created successfully")
        
        # Test OverallState creation
        state = OverallState(person=person)
        print("✓ OverallState object created successfully")
        
        # Test extraction_schema exists
        assert hasattr(state, 'extraction_schema')
        assert 'years_of_experience' in state.extraction_schema
        assert 'current_company' in state.extraction_schema
        assert 'current_role' in state.extraction_schema
        assert 'prior_companies' in state.extraction_schema
        print("✓ extraction_schema properly configured")
        
        # Test reflection-related attributes
        assert hasattr(state, 'research_complete')
        assert hasattr(state, 'structured_info')
        assert hasattr(state, 'missing_info')
        assert hasattr(state, 'reflection_reasoning')
        print("✓ Reflection state attributes present")
        
        return True
        
    except Exception as e:
        print(f"✗ State creation error: {e}")
        return False

if __name__ == "__main__":
    print("Testing People Research Agent with Reflection...")
    print("=" * 50)
    
    import_success = test_imports()
    state_success = test_state_creation()
    
    print("=" * 50)
    if import_success and state_success:
        print("✓ All tests passed! The enhanced agent is ready for deployment.")
        sys.exit(0)
    else:
        print("✗ Some tests failed. Please check the errors above.")
        sys.exit(1)
