#!/usr/bin/env python3
"""
Test script for the LangGraph Decision-Making Agent
Tests routing logic and tool accessibility
"""

import os
from langchain_core.messages import HumanMessage

def test_agent_import():
    """Test that the agent can be imported successfully"""
    try:
        # Set dummy API keys to avoid import errors
        import os
        os.environ.setdefault('OPENAI_API_KEY', 'dummy-key-for-testing')
        os.environ.setdefault('TAVILY_API_KEY', 'dummy-key-for-testing')
        
        from agent import app
        print("✅ Agent imported successfully")
        print(f"   Agent type: {type(app)}")
        return app
    except Exception as e:
        print(f"❌ Failed to import agent: {e}")
        return None

def test_simple_query(app):
    """Test a simple conversational query that shouldn't need tools"""
    print("\n🧪 Testing simple conversational query...")
    try:
        initial_state = {
            "messages": [HumanMessage("Hello! How are you today?")],
            "iteration_count": 0,
            "user_intent": "greeting"
        }
        
        config = {"configurable": {"thread_id": "test_thread_1"}}
        result = app.invoke(initial_state, config)
        
        if result and "messages" in result:
            final_message = result["messages"][-1]
            print(f"✅ Simple query successful")
            print(f"   Response: {final_message.content[:100]}...")
            
            # Check if tools were called (they shouldn't be for a greeting)
            if hasattr(final_message, 'tool_calls') and final_message.tool_calls:
                print(f"⚠️  Unexpected tool calls for simple query: {len(final_message.tool_calls)}")
            else:
                print("✅ No tool calls (as expected for greeting)")
            
            return True
        else:
            print("❌ No response received")
            return False
            
    except Exception as e:
        print(f"❌ Simple query failed: {e}")
        return False

def test_weather_query(app):
    """Test a weather query that should trigger the weather tool"""
    print("\n🌤️  Testing weather query...")
    try:
        initial_state = {
            "messages": [HumanMessage("What's the weather like in New York?")],
            "iteration_count": 0,
            "user_intent": "weather_request"
        }
        
        config = {"configurable": {"thread_id": "test_thread_2"}}
        result = app.invoke(initial_state, config)
        
        if result and "messages" in result:
            # Look for tool calls in the conversation
            tool_calls_found = False
            for message in result["messages"]:
                if hasattr(message, 'tool_calls') and message.tool_calls:
                    tool_calls_found = True
                    print(f"✅ Tool calls detected: {len(message.tool_calls)}")
                    for tool_call in message.tool_calls:
                        print(f"   Tool: {tool_call.get('name', 'unknown')}")
                    break
            
            final_message = result["messages"][-1]
            print(f"✅ Weather query completed")
            print(f"   Final response: {final_message.content[:100]}...")
            
            if not tool_calls_found:
                print("⚠️  No tool calls found - routing may not be working")
            
            return True
        else:
            print("❌ No response received")
            return False
            
    except Exception as e:
        print(f"❌ Weather query failed: {e}")
        return False

def test_math_query(app):
    """Test a math query that should trigger the math tool"""
    print("\n🔢 Testing math query...")
    try:
        initial_state = {
            "messages": [HumanMessage("What is 25 * 4 + 10?")],
            "iteration_count": 0,
            "user_intent": "math_calculation"
        }
        
        result = app.invoke(initial_state)
        
        if result and "messages" in result:
            # Look for tool calls in the conversation
            tool_calls_found = False
            for message in result["messages"]:
                if hasattr(message, 'tool_calls') and message.tool_calls:
                    tool_calls_found = True
                    print(f"✅ Tool calls detected: {len(message.tool_calls)}")
                    for tool_call in message.tool_calls:
                        print(f"   Tool: {tool_call.get('name', 'unknown')}")
                    break
            
            final_message = result["messages"][-1]
            print(f"✅ Math query completed")
            print(f"   Final response: {final_message.content[:100]}...")
            
            if not tool_calls_found:
                print("⚠️  No tool calls found - routing may not be working")
            
            return True
        else:
            print("❌ No response received")
            return False
            
    except Exception as e:
        print(f"❌ Math query failed: {e}")
        return False

def test_routing_logic(app):
    """Test the routing logic by examining the graph structure"""
    print("\n🔀 Testing routing logic...")
    try:
        # Check if the graph has the expected structure
        graph = app.get_graph()
        nodes = list(graph.nodes.keys())
        edges = [(edge.source, edge.target) for edge in graph.edges]
        
        print(f"✅ Graph structure:")
        print(f"   Nodes: {nodes}")
        print(f"   Edges: {edges}")
        
        # Check for conditional edges
        has_conditional = any("agent" in str(edge) for edge in graph.edges if hasattr(edge, 'condition'))
        if has_conditional:
            print("✅ Conditional routing detected")
        else:
            print("⚠️  No conditional routing found")
        
        return True
        
    except Exception as e:
        print(f"❌ Routing logic test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting LangGraph Agent Tests")
    print("=" * 50)
    
    # Test 1: Import agent
    app = test_agent_import()
    if not app:
        print("\n❌ Cannot proceed with tests - agent import failed")
        return
    
    # Test 2: Simple query (no tools)
    test_simple_query(app)
    
    # Test 3: Weather query (should use tools)
    test_weather_query(app)
    
    # Test 4: Math query (should use tools)
    test_math_query(app)
    
    # Test 5: Routing logic
    test_routing_logic(app)
    
    print("\n" + "=" * 50)
    print("🏁 Agent testing completed!")
    print("\nNote: Some tests may show warnings if API keys are not configured,")
    print("but the routing logic and import functionality should work.")

if __name__ == "__main__":
    main()



