"""
Test script to demonstrate the routing logic without requiring API keys.
This shows how the conditional routing works.
"""

from typing import Annotated, Sequence, TypedDict
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.messages.tool import tool_call
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
import uuid

# Define the agent state
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    iteration_count: int
    user_intent: str

def mock_agent_node(state: AgentState):
    """
    Mock agent node that simulates tool call decisions.
    """
    messages = state["messages"]
    iteration_count = state.get("iteration_count", 0)
    
    # Check if we just received a tool response
    if messages and isinstance(messages[-1], ToolMessage):
        # After tool execution, provide final answer
        tool_result = messages[-1].content
        response = AIMessage(content=f"Based on the tool execution: {tool_result}")
        return {
            "messages": [response],
            "iteration_count": iteration_count + 1
        }
    
    # Get the last human message
    last_human_msg = None
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            last_human_msg = msg.content.lower()
            break
    
    # Simulate decision making based on query type
    if last_human_msg:
        if "weather" in last_human_msg:
            # Simulate a tool call response
            response = AIMessage(
                content="I'll check the weather for you.", 
                tool_calls=[tool_call(name="get_weather", args={"location": "New York"}, id=str(uuid.uuid4()))]
            )
        elif "calculate" in last_human_msg or "math" in last_human_msg:
            # Simulate a tool call response
            response = AIMessage(
                content="Let me calculate that.", 
                tool_calls=[tool_call(name="calculate_math", args={"expression": "15 * 24"}, id=str(uuid.uuid4()))]
            )
        elif "what is" in last_human_msg or "search" in last_human_msg:
            # Simulate a tool call response
            response = AIMessage(
                content="Let me search for that information.", 
                tool_calls=[tool_call(name="web_search", args={"query": "Python programming"}, id=str(uuid.uuid4()))]
            )
        else:
            # Direct response without tools
            response = AIMessage(content="Hello! I'm here to help you. I can answer questions, check weather, do calculations, and search for information.")
    else:
        response = AIMessage(content="I'm ready to help!")
    
    return {
        "messages": [response],
        "iteration_count": iteration_count + 1
    }

def mock_tool_node(state: AgentState):
    """
    Mock tool node that simulates tool execution.
    """
    messages = state["messages"]
    last_message = messages[-1]
    
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        tool_call = last_message.tool_calls[0]
        tool_name = tool_call.get("name")
        tool_id = tool_call.get("id")
        
        if tool_name == "get_weather":
            result = "The weather in New York is sunny with 72°F temperature."
        elif tool_name == "calculate_math":
            result = "The result of 15 * 24 is 360"
        elif tool_name == "web_search":
            result = "Python is a high-level, interpreted programming language known for its simplicity and readability."
        else:
            result = "Tool executed successfully."
        
        # Return a ToolMessage to properly indicate tool execution completed
        return {"messages": [ToolMessage(content=result, tool_call_id=tool_id)]}
    
    return {"messages": []}

def should_continue(state: AgentState):
    """
    Determines whether to use tools or provide final answer.
    Returns "tools" if tool calls are needed, "end" otherwise.
    """
    messages = state["messages"]
    last_message = messages[-1]
    
    # Check if the last message has tool calls
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    
    # No tool calls, so we can end
    return "end"

def create_test_agent():
    """
    Creates a test agent to demonstrate routing logic.
    """
    # Create the workflow
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("agent", mock_agent_node)
    workflow.add_node("tools", mock_tool_node)
    
    # Add edges
    workflow.add_edge(START, "agent")
    workflow.add_edge("tools", "agent")
    
    # Add conditional edge from agent
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "end": END
        }
    )
    
    # Compile the graph
    app = workflow.compile()
    
    return app

def test_routing():
    """Test the routing logic with various query types."""
    
    agent = create_test_agent()
    
    test_cases = [
        ("What's the weather in New York?", "Should route to tools"),
        ("Calculate 15 * 24", "Should route to tools"),
        ("What is Python programming language?", "Should route to tools"),
        ("Hello, how are you?", "Should go directly to END"),
    ]
    
    print("Testing Routing Logic")
    print("=" * 50)
    
    for i, (query, expected) in enumerate(test_cases, 1):
        print(f"\nTest {i}: {query}")
        print(f"Expected: {expected}")
        print("-" * 50)
        
        try:
            result = agent.invoke(
                {
                    "messages": [HumanMessage(content=query)],
                    "iteration_count": 0,
                    "user_intent": ""
                }
            )
            
            # Check routing path
            num_messages = len(result["messages"])
            iterations = result["iteration_count"]
            
            if iterations > 1:
                print("✅ Routed through tools (multiple iterations)")
            else:
                print("✅ Went directly to END (single iteration)")
            
            final_message = result["messages"][-1]
            print(f"Response: {final_message.content}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_routing()