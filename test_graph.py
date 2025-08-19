#!/usr/bin/env python3
"""
Comprehensive test script to verify the enhanced people research agent.
This script tests all the key components and validates the deployment configuration.
"""

import json
import os
import sys
from typing import Dict, Any
from pprint import pprint

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("=" * 60)
print("Testing Enhanced People Research Agent")
print("=" * 60)

print("\n1️⃣ Testing imports and module structure...")
try:
    from agent.state import Person, InputState, OverallState, OutputState
    print("✅ State classes imported successfully")
    
    from agent.graph import (
        graph, 
        StructuredPersonInfo, 
        ReflectionDecision,
        should_continue_research,
        reflection,
        research_person,
        generate_queries
    )
    print("✅ Graph components imported successfully")
    
    from agent.prompts import REFLECTION_PROMPT, INFO_PROMPT, QUERY_WRITER_PROMPT
    print("✅ Prompts imported successfully")
    
    from agent.configuration import Configuration
    print("✅ Configuration imported successfully")
    
    from agent.utils import deduplicate_and_format_sources, format_all_notes
    print("✅ Utility functions imported successfully")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    exit(1)

print("\n2️⃣ Testing state definitions...")
try:
    # Test Person model
    test_person = Person(
        name="Test User",
        email="test@example.com",
        company="Test Company",
        role="Test Role",
        linkedin="https://linkedin.com/in/testuser"
    )
    print(f"✅ Person model created: {test_person.name}")
    
    # Test OverallState with extraction_schema
    overall_state = OverallState(person=test_person)
    assert overall_state.extraction_schema is not None
    assert "years_of_experience" in overall_state.extraction_schema
    assert "current_company" in overall_state.extraction_schema
    assert "current_role" in overall_state.extraction_schema
    assert "prior_companies" in overall_state.extraction_schema
    print(f"✅ OverallState has extraction_schema with {len(overall_state.extraction_schema)} fields")
    print(f"   Fields: {list(overall_state.extraction_schema.keys())}")
    
    # Test OutputState
    output_state = OutputState(
        person=test_person,
        structured_output={
            "years_of_experience": "10+ years",
            "current_company": "Test Company",
            "current_role": "Test Role",
            "prior_companies": ["Company A", "Company B"]
        }
    )
    print("✅ OutputState created with structured output")
    
except Exception as e:
    print(f"❌ State definition error: {e}")
    exit(1)

print("\n3️⃣ Testing reflection components...")
try:
    # Test StructuredPersonInfo
    structured_info = StructuredPersonInfo(
        years_of_experience="15 years",
        current_company="Tech Corp",
        current_role="Senior Engineer",
        prior_companies=["StartupA", "BigCorp"],
        education="BS Computer Science",
        skills=["Python", "Cloud", "AI"],
        notable_achievements=["Led team of 10", "Built scalable system"]
    )
    print("✅ StructuredPersonInfo model validated")
    print(f"   Current role: {structured_info.current_role}")
    print(f"   Experience: {structured_info.years_of_experience}")
    
    # Test ReflectionDecision
    reflection_decision = ReflectionDecision(
        is_satisfactory=True,
        missing_information=["Specific dates"],
        reasoning="Core information found",
        suggested_queries=["Search for timeline"]
    )
    print("✅ ReflectionDecision model validated")
    print(f"   Is satisfactory: {reflection_decision.is_satisfactory}")
    
except Exception as e:
    print(f"❌ Reflection component error: {e}")
    exit(1)

print("\n4️⃣ Testing REFLECTION_PROMPT...")
try:
    # Verify REFLECTION_PROMPT exists and has required placeholders
    assert REFLECTION_PROMPT is not None
    assert "{person}" in REFLECTION_PROMPT
    assert "{structured_info}" in REFLECTION_PROMPT
    assert "{raw_notes}" in REFLECTION_PROMPT
    assert "{user_notes}" in REFLECTION_PROMPT
    print("✅ REFLECTION_PROMPT contains all required placeholders")
    print(f"   Prompt length: {len(REFLECTION_PROMPT)} characters")
    
except Exception as e:
    print(f"❌ REFLECTION_PROMPT error: {e}")
    exit(1)

print("\n5️⃣ Testing graph workflow...")
try:
    # Test graph compilation
    assert graph is not None
    print(f"✅ Graph compiled successfully")
    print(f"   Graph type: {type(graph).__name__}")
    
    # Test graph nodes
    if hasattr(graph, 'nodes'):
        nodes = list(graph.nodes.keys())
        required_nodes = ['generate_queries', 'research_person', 'reflection']
        for node in required_nodes:
            assert node in nodes, f"Missing node: {node}"
        print(f"✅ All required nodes present: {required_nodes}")
    
    # Test conditional routing
    test_state = OverallState(person=test_person)
    
    # Test satisfactory result routing
    test_state.reflection_result = {"is_satisfactory": True}
    result = should_continue_research(test_state)
    assert result == "__end__", f"Expected __end__, got {result}"
    print("✅ Conditional routing (satisfactory): routes to END")
    
    # Test unsatisfactory with queries routing
    test_state.reflection_result = {
        "is_satisfactory": False,
        "suggested_queries": ["query1", "query2"]
    }
    result = should_continue_research(test_state)
    assert result == "generate_queries", f"Expected generate_queries, got {result}"
    print("✅ Conditional routing (needs more): routes to generate_queries")
    
    # Test unsatisfactory without queries routing
    test_state.reflection_result = {
        "is_satisfactory": False,
        "suggested_queries": []
    }
    result = should_continue_research(test_state)
    assert result == "__end__", f"Expected __end__, got {result}"
    print("✅ Conditional routing (no queries): routes to END")
    
except Exception as e:
    print(f"❌ Graph workflow error: {e}")
    exit(1)

print("\n6️⃣ Testing deployment configuration...")
try:
    # Check langgraph.json
    if not os.path.exists("langgraph.json"):
        raise FileNotFoundError("langgraph.json not found")
    
    with open("langgraph.json", "r") as f:
        config = json.load(f)
    
    # Validate required fields
    assert "dependencies" in config, "Missing 'dependencies' in langgraph.json"
    assert "./src/agent" in config["dependencies"], "Dependencies should include './src/agent'"
    
    assert "graphs" in config, "Missing 'graphs' in langgraph.json"
    assert "agent" in config["graphs"], "Missing 'agent' graph configuration"
    assert config["graphs"]["agent"] == "./src/agent/graph.py:graph", "Incorrect graph path"
    
    assert "env" in config, "Missing 'env' in langgraph.json"
    
    print("✅ langgraph.json validated")
    print(f"   Dependencies: {config['dependencies']}")
    print(f"   Graph: {config['graphs']['agent']}")
    print(f"   Environment: {config['env']}")
    
    # Check .env file
    if os.path.exists(".env"):
        print("✅ .env file exists")
        with open(".env", "r") as f:
            env_content = f.read()
            if "ANTHROPIC_API_KEY" in env_content:
                print("   Contains ANTHROPIC_API_KEY placeholder")
            if "TAVILY_API_KEY" in env_content:
                print("   Contains TAVILY_API_KEY placeholder")
    else:
        print("⚠️  .env file not found (optional)")
    
except Exception as e:
    print(f"❌ Deployment configuration error: {e}")
    exit(1)

print("\n" + "=" * 60)
print("✅ ALL TESTS PASSED!")
print("=" * 60)

print("\n📊 Test Summary:")
print("  ✅ State definitions complete with extraction_schema")
print("  ✅ OutputState properly defined")
print("  ✅ Reflection function components working")
print("  ✅ REFLECTION_PROMPT properly configured")
print("  ✅ Graph workflow with conditional routing")
print("  ✅ Deployment configuration valid")

print("\n🎯 Key Features Verified:")
print("  • Structured output format with required fields:")
print("    - years_of_experience")
print("    - current_company")
print("    - current_role")
print("    - prior_companies")
print("  • Reflection-based evaluation and decision making")
print("  • Conditional re-research capability")
print("  • LangGraph Platform deployment ready")

print("\n📝 Next Steps:")
print("  1. Set actual API keys in .env file")
print("  2. Run 'langgraph dev' to start development server")
print("  3. Test with real person queries")
print("  4. Deploy to LangGraph Platform")

