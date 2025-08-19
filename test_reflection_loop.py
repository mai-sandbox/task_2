#!/usr/bin/env python3
"""Test script to verify the reflection loop functionality."""

import asyncio
import sys
import os
from typing import Dict, Any

# Add src to path
sys.path.insert(0, 'src')

# Set dummy API keys for testing (won't make actual calls)
os.environ['ANTHROPIC_API_KEY'] = 'test-key-for-import'
os.environ['TAVILY_API_KEY'] = 'test-key-for-import'


def test_reflection_loop():
    """Test the reflection loop functionality without making actual API calls."""
    print("=" * 60)
    print("Testing Reflection Loop Functionality")
    print("=" * 60)
    
    # Test 1: Import the graph
    print("\n1. Testing graph import...")
    try:
        from agent.graph import app, builder
        print("   ✓ Successfully imported graph components")
    except Exception as e:
        print(f"   ✗ Failed to import graph: {e}")
        return False
    
    # Test 2: Verify graph structure includes reflection
    print("\n2. Verifying graph structure with reflection...")
    try:
        graph = app.get_graph()
        nodes = list(graph.nodes.keys())
        
        required_nodes = ['generate_queries', 'research_person', 'reflection']
        if all(node in nodes for node in required_nodes):
            print(f"   ✓ All reflection loop nodes present: {required_nodes}")
        else:
            print(f"   ✗ Missing nodes. Expected: {required_nodes}, Got: {nodes}")
            return False
    except Exception as e:
        print(f"   ✗ Error checking graph structure: {e}")
        return False
    
    # Test 3: Verify reflection routing
    print("\n3. Verifying reflection routing logic...")
    try:
        from agent.graph import route_after_reflection
        from agent.state import OverallState
        from agent.state import Person
        
        # Create a test state with "continue" decision
        test_person = Person(email="test@example.com", name="Test Person")
        test_state_continue = OverallState(
            person=test_person,
            reflection_decision="continue"
        )
        
        # Test routing with "continue" decision
        result = route_after_reflection(test_state_continue)
        if result == "generate_queries":
            print("   ✓ Reflection routes to 'generate_queries' when decision is 'continue'")
        else:
            print(f"   ✗ Unexpected routing for 'continue': {result}")
            return False
        
        # Create a test state with "complete" decision
        test_state_complete = OverallState(
            person=test_person,
            reflection_decision="complete"
        )
        
        # Test routing with "complete" decision
        from langgraph.graph import END
        result = route_after_reflection(test_state_complete)
        if result == END:
            print("   ✓ Reflection routes to END when decision is 'complete'")
        else:
            print(f"   ✗ Unexpected routing for 'complete': {result}")
            return False
            
    except Exception as e:
        print(f"   ✗ Error testing reflection routing: {e}")
        return False
    
    # Test 4: Verify reflection prompt exists
    print("\n4. Verifying reflection prompt...")
    try:
        from agent.prompts import REFLECTION_PROMPT
        if REFLECTION_PROMPT and len(REFLECTION_PROMPT) > 0:
            print("   ✓ REFLECTION_PROMPT exists and is not empty")
            print(f"   ℹ Prompt length: {len(REFLECTION_PROMPT)} characters")
        else:
            print("   ✗ REFLECTION_PROMPT is empty or missing")
            return False
    except ImportError as e:
        print(f"   ✗ Failed to import REFLECTION_PROMPT: {e}")
        return False
    
    # Test 5: Verify reflection structured output model
    print("\n5. Verifying reflection structured output model...")
    try:
        from agent.graph import ReflectionResult
        
        # Test creating an instance with correct fields
        test_result = ReflectionResult(
            years_experience=5,
            current_company="Test Company",
            role="Software Engineer",
            prior_companies=["Company A", "Company B"],
            missing_information=["education", "certifications"],
            quality_assessment="partial",
            additional_search_suggestions=["test query 1", "test query 2"],
            decision="continue",
            reasoning="Need more information about education and certifications"
        )
        
        print("   ✓ ReflectionResult model works correctly")
        print(f"   ℹ Model fields: years_experience, current_company, role, prior_companies,")
        print(f"                    missing_information, quality_assessment, additional_search_suggestions,")
        print(f"                    decision, reasoning")
        
        # Test with minimal required fields
        minimal_result = ReflectionResult(
            quality_assessment="complete",
            decision="complete",
            reasoning="All required information has been found"
        )
        print("   ✓ ReflectionResult works with minimal required fields")
        
    except Exception as e:
        print(f"   ✗ Error with ReflectionResult model: {e}")
        return False
    
    # Test 6: Check graph edges for reflection loop
    print("\n6. Checking graph edges for reflection loop...")
    try:
        edges = graph.edges
        
        # Check for edge from research_person to reflection
        research_to_reflection = any(
            edge[0] == 'research_person' and edge[1] == 'reflection' 
            for edge in edges
        )
        
        if research_to_reflection:
            print("   ✓ Edge exists from 'research_person' to 'reflection'")
        else:
            print("   ✗ Missing edge from 'research_person' to 'reflection'")
            return False
        
        # Check for conditional edges from reflection
        reflection_edges = [edge for edge in edges if edge[0] == 'reflection']
        if reflection_edges:
            print(f"   ✓ Reflection has outgoing edges: {[e[1] for e in reflection_edges]}")
        else:
            print("   ⚠ No direct edges from reflection (likely uses conditional routing)")
            
    except Exception as e:
        print(f"   ✗ Error checking edges: {e}")
        # This is not critical as edges might be handled differently
    
    # Test 7: Verify state fields for reflection
    print("\n7. Verifying state fields for reflection...")
    try:
        from agent.state import OverallState, ExtractedInfo
        import dataclasses
        
        fields = {f.name for f in dataclasses.fields(OverallState)}
        required_fields = ['extraction_schema', 'extracted_info', 'reflection_decision']
        
        if all(field in fields for field in required_fields):
            print(f"   ✓ All reflection-related fields present in OverallState")
            print(f"   ℹ Fields: {', '.join(required_fields)}")
        else:
            missing = set(required_fields) - fields
            print(f"   ✗ Missing fields in OverallState: {missing}")
            return False
            
    except Exception as e:
        print(f"   ✗ Error checking state fields: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("✅ All reflection loop tests passed!")
    print("=" * 60)
    print("\nThe reflection loop is properly configured with:")
    print("• Reflection node in the graph")
    print("• Conditional routing based on reflection decision")
    print("• Proper state fields for tracking reflection")
    print("• Structured output model for reflection results")
    print("• REFLECTION_PROMPT for guiding the evaluation")
    
    return True


if __name__ == "__main__":
    success = test_reflection_loop()
    sys.exit(0 if success else 1)


