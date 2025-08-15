#!/usr/bin/env python3
"""
Test script for the reflection function to ensure it processes research notes correctly
and returns expected structured output.
"""

import os
import sys
from unittest.mock import Mock, patch
from typing import Dict, Any

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_reflection_function():
    """Test the reflection function with mock data to validate structure and behavior."""
    
    print("=" * 60)
    print("Testing Reflection Function")
    print("=" * 60)
    
    try:
        # Import required modules
        from src.agent.graph import reflection, ReflectionOutput
        from src.agent.state import OverallState
        from langchain_core.runnables import RunnableConfig
        
        print("✅ Successfully imported reflection function and dependencies")
        
        # Create mock state with sample research notes
        mock_state = OverallState(
            person={"email": "john.doe@example.com", "name": "John Doe"},
            user_notes="Research John Doe's professional background",
            search_queries=["John Doe software engineer", "John Doe Google"],
            completed_notes=[
                "John Doe is a Senior Software Engineer at Google with 8 years of experience.",
                "Previously worked at Microsoft for 3 years and Amazon for 2 years.",
                "Specializes in machine learning and distributed systems.",
                "Started career at a startup called TechCorp in 2016."
            ],
            extraction_schema={"years_experience": "int", "current_company": "str"}
        )
        
        # Create mock config
        mock_config = RunnableConfig(configurable={})
        
        print("✅ Created mock state and config")
        
        # Create mock ReflectionOutput for testing
        mock_reflection_result = ReflectionOutput(
            years_experience=8,
            current_company="Google",
            role="Senior Software Engineer",
            prior_companies=["Microsoft", "Amazon", "TechCorp"],
            satisfaction_score=0.9,
            missing_info=["Education background", "Specific projects"],
            needs_more_research=False,
            reasoning="Core professional information is well documented with clear career progression."
        )
        
        print("✅ Created mock reflection output")
        
        # Mock the LLM call to return our test data
        with patch('src.agent.graph.claude_3_5_sonnet') as mock_llm:
            # Mock the structured LLM
            mock_structured_llm = Mock()
            mock_structured_llm.invoke.return_value = mock_reflection_result
            mock_llm.with_structured_output.return_value = mock_structured_llm
            
            # Call the reflection function
            result = reflection(mock_state, mock_config)
            
            print("✅ Successfully called reflection function")
            
            # Validate the result structure
            expected_keys = {
                "years_experience", "current_company", "role", "prior_companies",
                "satisfaction_score", "missing_info", "needs_more_research", "reasoning"
            }
            
            result_keys = set(result.keys())
            
            if result_keys == expected_keys:
                print("✅ Result contains all expected keys")
            else:
                missing_keys = expected_keys - result_keys
                extra_keys = result_keys - expected_keys
                if missing_keys:
                    print(f"❌ Missing keys: {missing_keys}")
                if extra_keys:
                    print(f"❌ Extra keys: {extra_keys}")
                return False
            
            # Validate data types and values
            validations = [
                ("years_experience", result["years_experience"], int, 8),
                ("current_company", result["current_company"], str, "Google"),
                ("role", result["role"], str, "Senior Software Engineer"),
                ("prior_companies", result["prior_companies"], list, ["Microsoft", "Amazon", "TechCorp"]),
                ("satisfaction_score", result["satisfaction_score"], float, 0.9),
                ("missing_info", result["missing_info"], list, ["Education background", "Specific projects"]),
                ("needs_more_research", result["needs_more_research"], bool, False),
                ("reasoning", result["reasoning"], str, "Core professional information is well documented with clear career progression.")
            ]
            
            for field_name, actual_value, expected_type, expected_value in validations:
                if not isinstance(actual_value, expected_type):
                    print(f"❌ {field_name}: Expected type {expected_type.__name__}, got {type(actual_value).__name__}")
                    return False
                
                if actual_value != expected_value:
                    print(f"❌ {field_name}: Expected {expected_value}, got {actual_value}")
                    return False
                
                print(f"✅ {field_name}: Correct type and value")
            
            # Validate that the LLM was called with proper prompt formatting
            mock_llm.with_structured_output.assert_called_once_with(ReflectionOutput)
            mock_structured_llm.invoke.assert_called_once()
            
            # Get the prompt that was passed to the LLM
            call_args = mock_structured_llm.invoke.call_args[0]
            prompt_used = call_args[0]
            
            # Validate that the prompt contains the research notes
            if "John Doe is a Senior Software Engineer" in prompt_used:
                print("✅ Prompt correctly includes research notes")
            else:
                print("❌ Prompt does not include expected research notes")
                return False
            
            print("\n" + "=" * 60)
            print("🎉 ALL REFLECTION FUNCTION TESTS PASSED!")
            print("✅ Function structure is correct")
            print("✅ Return values have expected types and values")
            print("✅ LLM integration works properly")
            print("✅ Prompt formatting includes research notes")
            print("=" * 60)
            
            return True
            
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_reflection_output_model():
    """Test the ReflectionOutput Pydantic model validation."""
    
    print("\n" + "=" * 60)
    print("Testing ReflectionOutput Model")
    print("=" * 60)
    
    try:
        from src.agent.graph import ReflectionOutput
        
        # Test valid data
        valid_data = {
            "years_experience": 5,
            "current_company": "TechCorp",
            "role": "Software Engineer",
            "prior_companies": ["StartupA", "BigCorp"],
            "satisfaction_score": 0.8,
            "missing_info": ["Education"],
            "needs_more_research": True,
            "reasoning": "Need more information about education background."
        }
        
        reflection_output = ReflectionOutput(**valid_data)
        print("✅ ReflectionOutput model accepts valid data")
        
        # Test satisfaction_score validation (should be between 0.0 and 1.0)
        try:
            invalid_score = ReflectionOutput(
                years_experience=5,
                current_company="TechCorp",
                role="Engineer",
                prior_companies=[],
                satisfaction_score=1.5,  # Invalid: > 1.0
                missing_info=[],
                needs_more_research=False,
                reasoning="Test"
            )
            print("❌ Model should reject satisfaction_score > 1.0")
            return False
        except Exception:
            print("✅ Model correctly rejects satisfaction_score > 1.0")
        
        # Test default values
        minimal_data = {
            "satisfaction_score": 0.5,
            "needs_more_research": True,
            "reasoning": "Test reasoning"
        }
        
        minimal_output = ReflectionOutput(**minimal_data)
        
        if minimal_output.prior_companies == []:
            print("✅ prior_companies defaults to empty list")
        else:
            print("❌ prior_companies should default to empty list")
            return False
            
        if minimal_output.missing_info == []:
            print("✅ missing_info defaults to empty list")
        else:
            print("❌ missing_info should default to empty list")
            return False
        
        print("\n✅ ReflectionOutput model validation tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ ReflectionOutput model test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Starting Reflection Function Test Suite...")
    
    # Run tests
    test1_passed = test_reflection_function()
    test2_passed = test_reflection_output_model()
    
    print("\n" + "=" * 60)
    print("FINAL TEST RESULTS")
    print("=" * 60)
    
    if test1_passed and test2_passed:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Reflection function works correctly")
        print("✅ ReflectionOutput model validates properly")
        print("✅ Ready for production use")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED!")
        if not test1_passed:
            print("❌ Reflection function test failed")
        if not test2_passed:
            print("❌ ReflectionOutput model test failed")
        sys.exit(1)
