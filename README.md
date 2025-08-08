# task_2
Fixing Conditional Routing

I have a LangGraph agent that has tools available but the workflow isn't routing correctly. The agent needs conditional logic to decide when to use tools versus when to provide a final answer directly.

Currently, the agent goes straight from the agent node to END, which means it never uses its available tools even when they would be helpful.

Please add conditional routing logic so the agent can use tools when the agent decides tool calls are needed

The agent should be able to handle queries that need weather information, math calculations, or knowledge searches, as well as simple conversational queries that don't need tools.
