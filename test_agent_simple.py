#!/usr/bin/env python3
"""
Simple test script for the LangGraph Decision-Making Agent
Tests basic functionality without requiring API keys
"""

import os
from typing import Annotated, Sequence, TypedDict
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import ToolNode

# Mock model for testing without API keys
class MockChatModel:
    def __init__(self):
        self.tools = []
    
    def bind_tools(self, tools):
        self.tools = tools
        return self
    
    def invoke(self, messages):
        # Simple logic to determine if we should call tools based on message content
        last_message = messages[-1].content.lower()
        
        if "weather" in last_message:
            # Mock tool call for weather
            return AIMessage(
                content="I'll check the weather for you.",
                tool_calls=[{
                    "name": "get_weather",
                    "args": {"location": "New York"},
                    "id": "call_1"
                }]
            )
        elif any(op in last_message for op in ["+", "-", "*", "/", "calculate", "math"]):
            # Mock tool call for math
            return AIMessage(
                content="I'll calculate that for you.",
                tool_calls=[{
                    "name": "calculate_math", 
                    "args": {"expression": "25 * 4 + 10"},
                    "id": "call_2"
                }]
            )
        else:
            # No tool call needed
            return AIMessage(content="Hello! I'm doing well, thank you for asking.")

# Define the agent state
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    iteration_count: int
    user_intent: str

# Define mock tools
@tool
def get_weather(location: str) -> str:
    """Get current weather information for a location."""
    return f"The weather in {location} is sunny with 72°F temperature."

@tool
def calculate_math(expression: str) -> str:
    """Perform mathematical calculations."""
    try:
        result = eval(expression)
        return f"The result of {expression} is {result}"
    except:
        return "Unable to calculate that expression."

# Create mock setup
tools = [get_weather, calculate_math]
tool_node = ToolNode(tools)
model = MockChatModel().bind_tools(tools)

def agent_node(state: AgentState):
    """Main agent node that processes user input and decides on actions."""
    messages = state["messages"]
    iteration_count = state.get("iteration_count", 0)
    
    # Add system message for first iteration
    if iteration_count == 0:
        system_msg = SystemMessage(content="""You are a helpful assistant. 
        You have access to weather, math, and knowledge search tools.
        Use tools when needed, but provide direct answers for simple questions.
        Keep responses concise and helpful.""")
        messages = [system_msg] + messages
    
    # Get model response
    response = model.invoke(messages)
    
    # Update iteration count
    new_iteration = iteration_count + 1
    
    return {
        "messages": [response],
        "iteration_count": new_iteration
    }

def should_continue(state: AgentState):
    """Determine if the agent should continue to tools or end the conversation."""
    messages = state["messages"]
    last_message = messages[-1]
    
    # Check if the last message has tool calls
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tools"
    else:
        return "end"

def create_test_agent():
    """Creates a test agent with tool capabilities."""
    # Create the workflow
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tool_node)
    
    # Add basic edges
    workflow.add_edge(START, "agent")
    workflow.add_edge("tools", "agent")
    
    # Add conditional routing from agent
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "end": END
        }
    )
    
    # Add memory checkpointer
    checkpointer = InMemorySaver()
    
    # Compile the graph
    app = workflow.compile(checkpointer=checkpointer)
    
    return app

def test_agent_import():
    """Test that the agent can be created successfully"""
    try:
        app = create_test_agent()
        print("✅ Test agent created successfully")
        print(f"   Agent type: {type(app)}")
        return app
    except Exception as e:
        print(f"❌ Failed to create test agent: {e}")
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
            print(f"   Response: {final_message.content}")
            
            # Check if tools were called (they shouldn't be for a greeting)
            tool_calls_in_conversation = False
            for message in result["messages"]:
                if hasattr(message, 'tool_calls') and message.tool_calls:
                    tool_calls_in_conversation = True
                    break
            
            if tool_calls_in_conversation:
                print(f"⚠️  Unexpected tool calls for simple query")
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
            weather_tool_used = False
            
            for message in result["messages"]:
                if hasattr(message, 'tool_calls') and message.tool_calls:
                    tool_calls_found = True
                    print(f"✅ Tool calls detected: {len(message.tool_calls)}")
                    for tool_call in message.tool_calls:
                        tool_name = tool_call.get('name', 'unknown')
                        print(f"   Tool: {tool_name}")
                        if tool_name == 'get_weather':
                            weather_tool_used = True
            
            final_message = result["messages"][-1]
            print(f"✅ Weather query completed")
            print(f"   Final response: {final_message.content}")
            
            if not tool_calls_found:
                print("⚠️  No tool calls found - routing may not be working")
            elif weather_tool_used:
                print("✅ Weather tool was used correctly")
            
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
            math_tool_used = False
            
            for message in result["messages"]:
                if hasattr(message, 'tool_calls') and message.tool_calls:
                    tool_calls_found = True
                    print(f"✅ Tool calls detected: {len(message.tool_calls)}")
                    for tool_call in message.tool_calls:
                        tool_name = tool_call.get('name', 'unknown')
                        print(f"   Tool: {tool_name}")
                        if tool_name == 'calculate_math':
                            math_tool_used = True
            
            final_message = result["messages"][-1]
            print(f"✅ Math query completed")
            print(f"   Final response: {final_message.content}")
            
            if not tool_calls_found:
                print("⚠️  No tool calls found - routing may not be working")
            elif math_tool_used:
                print("✅ Math tool was used correctly")
            
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
        
        print(f"✅ Graph structure:")
        print(f"   Nodes: {nodes}")
        
        # Check that we have the expected nodes
        expected_nodes = ['__start__', 'agent', 'tools', '__end__']
        missing_nodes = [node for node in expected_nodes if node not in nodes]
        
        if missing_nodes:
            print(f"⚠️  Missing expected nodes: {missing_nodes}")
        else:
            print("✅ All expected nodes present")
        
        # Check for conditional edges by looking at the graph structure
        edges_info = []
        for edge in graph.edges:
            edges_info.append(f"{edge.source} -> {edge.target}")
        
        print(f"   Edges: {edges_info}")
        
        # Look for conditional routing from agent
        agent_edges = [edge for edge in edges_info if edge.startswith('agent ->')]
        if len(agent_edges) > 1 or any('conditional' in str(edge).lower() for edge in graph.edges):
            print("✅ Conditional routing detected from agent node")
        else:
            print("⚠️  No conditional routing found from agent node")
        
        return True
        
    except Exception as e:
        print(f"❌ Routing logic test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting LangGraph Agent Tests (Mock Version)")
    print("=" * 60)
    
    # Test 1: Create test agent
    app = test_agent_import()
    if not app:
        print("\n❌ Cannot proceed with tests - agent creation failed")
        return
    
    # Test 2: Simple query (no tools)
    test_simple_query(app)
    
    # Test 3: Weather query (should use tools)
    test_weather_query(app)
    
    # Test 4: Math query (should use tools)
    test_math_query(app)
    
    # Test 5: Routing logic
    test_routing_logic(app)
    
    print("\n" + "=" * 60)
    print("🏁 Agent testing completed!")
    print("\nThis test uses mock components to verify routing logic")
    print("without requiring API keys. The routing functionality")
    print("should work the same way with the real agent.")

if __name__ == "__main__":
    main()


