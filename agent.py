import os
from typing import TypedDict, Literal, List, Annotated
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages # <--- CRITICAL FIX

# 1. SETUP TOOLS
tools = [TavilySearchResults(max_results=3)]

# 2. SETUP BRAIN (OpenAI GPT-4o)
llm = ChatOpenAI(model="gpt-4o", temperature=0).bind_tools(tools)

# 3. SYSTEM PROMPT
# I updated this to say "search for" instead of "visit" to prevent 400 Errors
SYSTEM_PROMPT = """
You are an expert Technical SEO Auditor and Strategist. 
Your goal is to analyze the user's website and provide a strict, data-driven audit.

### CRITICAL INSTRUCTION:
You MUST use the 'tavily_search_results_json' tool to search for the user's website (e.g., "site:kflexpack.com") to analyze its content, headers, and meta tags before answering.

### OUTPUT FORMAT:
Organize your response into these exact sections:

1. 🚨 **Critical Issues (Fix Immediately)**
   - List technical errors (broken H1s, missing meta tags, slow speed indicators).
   - Be specific (quote the actual text from the site).

2. ⚠️ **Warnings (Improvements)**
   - Content gaps, thin pages, or generic descriptions.

3. ✅ **The Good News**
   - What they are doing right.

4. 🚀 **Next Steps**
   - 3 bullet points of immediate action.

Refuse to give generic advice. Only report on what you actually see in the search results.
"""

# 4. DEFINE STATE (Fixed with 'add_messages')
class AgentState(TypedDict):
    # This prevents the "Invalid Parameter" error by appending messages instead of overwriting them
    messages: Annotated[List[HumanMessage], add_messages]

# 5. DEFINE NODES
def seo_node(state: AgentState):
    messages = state["messages"]
    sys_msg = SystemMessage(content=SYSTEM_PROMPT)
    # We allow the LLM to see the system prompt + conversation
    response = llm.invoke([sys_msg] + messages)
    return {"messages": [response]}

# Use the official ToolNode
tool_node = ToolNode(tools)

# 6. ROUTING LOGIC
def router(state: AgentState):
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    return END

# 7. BUILD THE GRAPH
workflow = StateGraph(AgentState)
workflow.add_node("seo_agent", seo_node)
workflow.add_node("tools", tool_node)

workflow.set_entry_point("seo_agent")
workflow.add_conditional_edges("seo_agent", router)
workflow.add_edge("tools", "seo_agent")

graph = workflow.compile()
