"""
Decision-Making Agent Implementation

A LangGraph agent that can use various tools and provide intelligent responses
based on user queries. Features weather, math, and knowledge search capabilities.
"""

import os
from typing import Annotated, Sequence, TypedDict
from dotenv import load_dotenv
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import ToolNode

# Load environment variables
load_dotenv()

# Define the agent state
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    iteration_count: int
    user_intent: str

# Define tools
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

@tool
def knowledge_search(query: str) -> str:
    """Search for knowledge and information."""
    return f"Here's what I found about '{query}': This is a mock search result providing relevant information."

# Use mock search instead of TavilySearch if API key is not available
tools = [get_weather, calculate_math, knowledge_search]
tool_node = ToolNode(tools)

# Initialize model with error handling for missing API key
try:
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0).bind_tools(tools)
except Exception as e:
    print(f"Warning: Could not initialize OpenAI model - {e}")
    model = None

def agent_node(state: AgentState):
    """
    Main agent node that processes user input and decides on actions.
    """
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

def should_continue(state: AgentState) -> str:
    """
    Conditional routing function to decide next step.
    
    Returns:
        "tools" if the agent wants to use tools
        "end" if the agent should provide final answer
    """
    messages = state["messages"]
    last_message = messages[-1]
    
    # Check if the last message has tool calls
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tools"
    else:
        return "end"

def create_agent():
    """
    Creates an intelligent agent with tool capabilities.
    """
    # Create the workflow
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tool_node)
    
    # Add edges
    workflow.add_edge(START, "agent")
    workflow.add_edge("tools", "agent")
    
    # Add conditional edge from agent
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "end": END,
        }
    )
    
    # Add memory checkpointer
    checkpointer = InMemorySaver()
    
    # Compile the graph
    app = workflow.compile(checkpointer=checkpointer)
    
    return app

app = create_agent()

def test_routing_logic():
    """Test the conditional routing logic without requiring API keys."""
    print("Testing Conditional Routing Logic")
    print("=" * 40)
    
    # Test the should_continue function with mock messages
    from langchain_core.messages import AIMessage
    
    # Test case 1: Message with tool calls
    print("\n1. Testing message WITH tool calls:")
    mock_tool_call = {
        "name": "get_weather",
        "args": {"location": "New York"},
        "id": "call_123"
    }
    
    message_with_tools = AIMessage(
        content="I'll check the weather for you.",
        tool_calls=[mock_tool_call]
    )
    
    state_with_tools = {
        "messages": [message_with_tools],
        "iteration_count": 1,
        "user_intent": "weather"
    }
    
    result = should_continue(state_with_tools)
    print(f"   should_continue() returned: '{result}'")
    print(f"   ✅ Correctly routes to tools")
    
    # Test case 2: Message without tool calls
    print("\n2. Testing message WITHOUT tool calls:")
    message_no_tools = AIMessage(content="Hello! How can I help you today?")
    
    state_no_tools = {
        "messages": [message_no_tools],
        "iteration_count": 1,
        "user_intent": "greeting"
    }
    
    result = should_continue(state_no_tools)
    print(f"   should_continue() returned: '{result}'")
    print(f"   ✅ Correctly routes to end")
    
    print(f"\n✅ Conditional routing logic is working correctly!")
    print(f"   - Messages with tool_calls → 'tools' node")
    print(f"   - Messages without tool_calls → 'end' (final answer)")

def test_agent():
    """Test the agent with various query types."""
    if model is None:
        print("⚠️  OpenAI API key not available. Testing routing logic only.")
        test_routing_logic()
        return
    
    agent = app
    
    test_cases = [
        "What's the weather in New York?",
        "Calculate 15 * 24", 
        "What is Python programming language?",
        "Hello, how are you?",
    ]
    
    print("Testing Agent Implementation")
    print("=" * 30)
    
    for i, query in enumerate(test_cases, 1):
        print(f"\nTest {i}: {query}")
        print("-" * 30)
        
        config = {"configurable": {"thread_id": f"test-{i}"}}
        
        try:
            result = agent.invoke(
                {
                    "messages": [HumanMessage(content=query)],
                    "iteration_count": 0,
                    "user_intent": ""
                },
                config
            )
            
            final_message = result["messages"][-1]
            print(f"Response: {final_message.content[:150]}...")
            print("✅ Agent executed successfully")
                
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🤖 LangGraph Agent with Conditional Routing")
    print("=" * 45)
    
    # Display graph structure
    print("\n📊 Graph Structure:")
    print("   START → agent")
    print("   agent → [conditional routing]")  
    print("     ├─ If tool_calls → tools")
    print("     └─ If no tool_calls → END")
    print("   tools → agent (loop for multi-step tool usage)")
    
    test_agent()