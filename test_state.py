#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/daytona/task_2/src')

try:
    from agent.state import InputState, OverallState, OutputState, Person
    print("✓ All state classes imported successfully")
    
    # Test OutputState has required fields
    output_state = OutputState()
    assert hasattr(output_state, 'years_experience')
    assert hasattr(output_state, 'current_company')
    assert hasattr(output_state, 'role')
    assert hasattr(output_state, 'prior_companies')
    assert hasattr(output_state, 'completed_notes')
    assert hasattr(output_state, 'reflection_reasoning')
    print("✓ OutputState has all required fields")
    
    # Test OverallState has extraction_schema
    overall_state = OverallState(person=Person(email="test@example.com"))
    assert hasattr(overall_state, 'extraction_schema')
    assert 'years_experience' in overall_state.extraction_schema
    assert 'current_company' in overall_state.extraction_schema
    assert 'role' in overall_state.extraction_schema
    assert 'prior_companies' in overall_state.extraction_schema
    print("✓ OverallState has extraction_schema with all required keys")
    
    print("\nAll state definitions are correctly implemented!")
    
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)
except AssertionError as e:
    print(f"Assertion error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"Unexpected error: {e}")
    sys.exit(1)
