#!/usr/bin/env python3
"""Test script to verify Person model access fixes work correctly."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Set dummy environment variables to avoid API key errors
os.environ.setdefault('ANTHROPIC_API_KEY', 'dummy-key')
os.environ.setdefault('TAVILY_API_KEY', 'dummy-key')

def test_person_model_access():
    """Test that Person model attribute access works correctly."""
    try:
        from agent.state import Person, OverallState
        from agent.graph import generate_queries
        from agent.configuration import Configuration
        
        print("✅ Successfully imported Person model and generate_queries function")
        
        # Test 1: Person with all fields
        person_full = Person(
            email="test@example.com",
            name="John Doe",
            company="Test Corp",
            linkedin="https://linkedin.com/in/johndoe",
            role="Software Engineer"
        )
        
        state_full = OverallState(person=person_full)
        print("✅ Created Person with all fields successfully")
        
        # Test 2: Person with only required field (email)
        person_minimal = Person(email="minimal@example.com")
        state_minimal = OverallState(person=person_minimal)
        print("✅ Created Person with minimal fields successfully")
        
        # Test 3: Verify attribute access works (this would have failed before the fix)
        try:
            email = state_full.person.email
            name = state_full.person.name if hasattr(state_full.person, 'name') and state_full.person.name else None
            company = state_full.person.company if hasattr(state_full.person, 'company') and state_full.person.company else None
            linkedin = state_full.person.linkedin if hasattr(state_full.person, 'linkedin') and state_full.person.linkedin else None
            role = state_full.person.role if hasattr(state_full.person, 'role') and state_full.person.role else None
            
            print(f"✅ Attribute access works: email={email}, name={name}, company={company}")
            
        except AttributeError as e:
            print(f"❌ Attribute access failed: {e}")
            return False
            
        # Test 4: Verify minimal person works with hasattr checks
        try:
            email_min = state_minimal.person.email
            name_min = state_minimal.person.name if hasattr(state_minimal.person, 'name') and state_minimal.person.name else None
            
            print(f"✅ Minimal person attribute access works: email={email_min}, name={name_min}")
            
        except AttributeError as e:
            print(f"❌ Minimal person attribute access failed: {e}")
            return False
            
        print("\n🎉 All Person model access tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

def test_imports():
    """Test that all imports work correctly."""
    try:
        # Test all critical imports
        from agent.state import Person, PersonProfile, ReflectionDecision, InputState, OverallState, OutputState
        from agent.configuration import Configuration
        from agent.prompts import QUERY_WRITER_PROMPT, INFO_PROMPT, REFLECTION_PROMPT
        from agent.utils import deduplicate_and_format_sources, format_all_notes
        from agent.graph import graph, generate_queries, research_person, reflection
        
        print("✅ All imports successful")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during imports: {e}")
        return False

if __name__ == "__main__":
    print("Running final syntax and import verification...\n")
    
    # Test imports
    print("1. Testing imports...")
    import_success = test_imports()
    
    # Test Person model access
    print("\n2. Testing Person model access fixes...")
    person_success = test_person_model_access()
    
    # Final result
    if import_success and person_success:
        print("\n🎉 All verification tests passed! The Person model access fixes work correctly.")
        sys.exit(0)
    else:
        print("\n❌ Some verification tests failed.")
        sys.exit(1)
