"""
Test script to demonstrate the enhanced people research agent with reflection capabilities.

This script shows how the agent would work in practice, though it requires API keys to run fully.
"""

from src.agent.state import Person, InputState, OverallState
from src.agent.configuration import Configuration


def main():
    """Demonstrate the agent setup and expected flow."""
    
    # Example person to research
    person = Person(
        email="john.doe@example.com",
        name="John Doe",
        company="Tech Corp",
        role="Senior Software Engineer"
    )
    
    # Example input state
    input_state = InputState(
        person=person,
        user_notes={"additional_info": "Looking for information about their AI/ML experience"}
    )
    
    # Example overall state (this would be created internally by the graph)
    overall_state = OverallState(
        person=person,
        user_notes="Looking for information about their AI/ML experience"
    )
    
    print("Enhanced People Research Agent with Reflection")
    print("=" * 50)
    print(f"Person to research: {person.name}")
    print(f"Email: {person.email}")
    print(f"Current company: {person.company}")
    print(f"Current role: {person.role}")
    print()
    
    print("Extraction Schema:")
    for key, description in overall_state.extraction_schema.items():
        print(f"  - {key}: {description}")
    print()
    
    print("Graph Flow:")
    print("1. generate_queries: Create search queries based on person info")
    print("2. research_person: Execute web searches and extract information")
    print("3. reflection: Analyze completeness and quality of research")
    print("4. Decision: Continue research if unsatisfactory, or end if complete")
    print()
    
    print("The reflection step will:")
    print("- Extract structured information focusing on experience and roles")
    print("- Assess completeness and quality of the research")
    print("- Decide whether additional research is needed")
    print("- Provide reasoning for the decision")
    print()
    
    print("To run the agent, you need:")
    print("- TAVILY_API_KEY environment variable")
    print("- ANTHROPIC_API_KEY environment variable")
    print()
    print("Then you can import and use the graph:")
    print("from src.agent.graph import graph")
    print("result = await graph.ainvoke(input_state)")


if __name__ == "__main__":
    main()