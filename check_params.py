#!/usr/bin/env python3
"""Check correct parameter names for ChatAnthropic and StateGraph."""

import inspect
from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph

print("ChatAnthropic parameters:")
sig = inspect.signature(ChatAnthropic.__init__)
for param_name, param in sig.parameters.items():
    if param_name != 'self':
        print(f"  - {param_name}: {param.annotation if param.annotation != inspect.Parameter.empty else 'Any'}")

print("\nStateGraph parameters:")
sig = inspect.signature(StateGraph.__init__)
for param_name, param in sig.parameters.items():
    if param_name != 'self':
        print(f"  - {param_name}: {param.annotation if param.annotation != inspect.Parameter.empty else 'Any'}")
