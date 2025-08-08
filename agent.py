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


web_search = TavilySearch(max_results=3)
tools = [get_weather, calculate_math, web_search]
tool_node = ToolNode(tools)
model = ChatOpenAI(model="gpt-4o-mini", temperature=0).bind_tools(tools)

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

def should_continue(state: AgentState):
    """
    Conditional routing function that determines whether to continue to tools or end.
    
    Checks if the last message in the agent state contains tool_calls.
    Returns 'tools' if tool calls are present, otherwise returns '__end__'.
    """
    messages = state["messages"]
    last_message = messages[-1]
    
    # Check if the last message has tool calls
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return 'tools'
    else:
        return '__end__'

def create_agent():
    """
    Creates an intelligent agent with tool capabilities.
    """
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
            'tools': 'tools',
            '__end__': END
        }
    )
    
    # Add memory checkpointer
    checkpointer = InMemorySaver()
    
    # Compile the graph
    app = workflow.compile(checkpointer=checkpointer)
    
    return app

app = create_agent()

def test_agent():
    """Test the agent with various query types."""
    
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
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Missing OPENAI_API_KEY environment variable")
        exit(1)
    
    if not os.getenv("TAVILY_API_KEY"):
        print("❌ Missing TAVILY_API_KEY environment variable")
        exit(1)
    
    test_agent()

