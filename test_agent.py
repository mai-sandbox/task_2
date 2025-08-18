#!/usr/bin/env python3
"""Test script for the people researcher agent."""

import asyncio
import os
from pprint import pprint
from src.agent.graph import graph
from src.agent.state import Person

async def test_agent():
    """Test the people researcher agent."""
    
    # Create a test person
    test_person = Person(
        email="test@example.com",
        name="John Doe",
        company="Example Corp",
        role="Software Engineer"
    )
    
    # Create input state
    input_state = {
        "person": test_person,
        "user_notes": "Looking for work experience and education background"
    }
    
    print("Testing People Researcher Agent")
    print("=" * 50)
    print(f"Searching for: {test_person.name}")
    print(f"Email: {test_person.email}")
    print(f"Company: {test_person.company}")
    print(f"Role: {test_person.role}")
    print("=" * 50)
    
    try:
        # Check if TAVILY_API_KEY is set
        if not os.getenv("TAVILY_API_KEY"):
            print("\nWarning: TAVILY_API_KEY not set. The agent will fail when trying to search.")
            print("Please set TAVILY_API_KEY environment variable to test the full functionality.")
            print("\nTesting graph compilation and structure...")
            
            # At least test that the graph compiles and has the right structure
            print(f"Graph nodes: {list(graph.nodes.keys())}")
            print("\nGraph compiled successfully!")
            print("\nExpected flow:")
            print("1. generate_queries -> Generate search queries")
            print("2. research_person -> Execute web searches")
            print("3. reflection -> Extract structured info and assess completeness")
            print("4. (Optional) Loop back to generate_queries if info is incomplete")
            print("5. finalize -> Prepare final output")
            return
            
        # Run the agent
        result = await graph.ainvoke(input_state)
        
        print("\nAgent completed successfully!")
        print("\nStructured Information Extracted:")
        print("-" * 40)
        pprint(result.get("structured_info"))
        
        print("\nCompleteness Assessment:")
        print("-" * 40)
        print(result.get("completeness_assessment"))
        
        print("\nRaw Notes (first 500 chars):")
        print("-" * 40)
        raw_notes = result.get("raw_notes", "")
        print(raw_notes[:500] + "..." if len(raw_notes) > 500 else raw_notes)
        
    except Exception as e:
        print(f"\nError running agent: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_agent())