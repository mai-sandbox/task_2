# LangGraph Agent Routing Logic

## Overview
This agent implements conditional routing to intelligently decide when to use tools versus providing direct responses.

## How Routing Works

### 1. Agent Node
The agent node (`agent_node`) processes user input and decides whether tools are needed:
- Analyzes the user's query
- If tools are needed, adds `tool_calls` to the response
- If no tools needed, provides a direct response

### 2. Routing Decision (`should_continue`)
After the agent node executes, the `should_continue` function determines the next step:
- **Returns "tools"**: If the agent's response contains `tool_calls`
- **Returns "end"**: If no tool calls are present (direct response)

### 3. Tool Execution Flow
When tools are invoked:
1. Agent generates response with `tool_calls` → Routes to "tools"
2. Tool node executes the requested tool(s)
3. Flow returns to agent node
4. Agent processes tool results and generates final response
5. Routes to "end" (no more tool calls)

### 4. Direct Response Flow
For simple queries that don't need tools:
1. Agent generates direct response (no `tool_calls`)
2. Routes directly to "end"

## Configuration

The routing is configured in `create_agent()`:

```python
# Add conditional edge from agent
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "tools": "tools",  # Route to tools if tool_calls present
        "end": END         # Route to END if no tool_calls
    }
)
```

## Example Queries

### Queries that use tools:
- "What's the weather in New York?" → Uses weather tool
- "Calculate 15 * 24" → Uses math tool
- "What is Python?" → Uses search tool

### Queries that go directly to END:
- "Hello, how are you?"
- "Thank you!"
- Simple conversational queries

## Testing

Run `test_routing.py` to see the routing logic in action without needing API keys.