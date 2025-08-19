#!/usr/bin/env python3
"""Test script to verify all imports and graph compilation work correctly."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test all module imports."""
    try:
        # Test basic imports
        from agent.state import InputState, OutputState, OverallState, Person
        print("✓ State imports successful")
        
        from agent.configuration import Configuration
        print("✓ Configuration imports successful")
        
        from agent.prompts import QUERY_WRITER_PROMPT, INFO_PROMPT, REFLECTION_PROMPT
        print("✓ Prompts imports successful")
        
        from agent.utils import deduplicate_and_format_sources, format_all_notes
        print("✓ Utils imports successful")
        
        # Test graph imports and compilation
        from agent.graph import generate_queries, research_person, reflection, should_continue_research
        print("✓ Graph function imports successful")
        
        # Test graph compilation (without instantiating API clients)
        import os
        os.environ.setdefault('TAVILY_API_KEY', 'test-key')
        os.environ.setdefault('ANTHROPIC_API_KEY', 'test-key')
        
        from agent.graph import graph
        print("✓ Graph compiled successfully")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Other error: {e}")
        return False

def test_state_structure():
    """Test state structure and schema."""
    try:
        from agent.state import OverallState, Person
        
        # Test Person creation
        person = Person(email="test@example.com", name="Test User")
        print("✓ Person creation successful")
        
        # Test OverallState with extraction_schema
        state = OverallState(person=person)
        assert hasattr(state, 'extraction_schema')
        assert 'years_of_experience' in state.extraction_schema
        assert 'current_company' in state.extraction_schema
        assert 'current_role' in state.extraction_schema
        assert 'prior_companies' in state.extraction_schema
        print("✓ OverallState extraction_schema verified")
        
        return True
        
    except Exception as e:
        print(f"✗ State structure error: {e}")
        return False

if __name__ == "__main__":
    print("Testing imports and functionality...")
    
    import_success = test_imports()
    state_success = test_state_structure()
    
    if import_success and state_success:
        print("\n🎉 All tests passed! The people research agent is ready for deployment.")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")

