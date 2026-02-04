import os
from typing import TypedDict, Literal, List, Annotated
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages

# 1. SETUP TOOLS
tools = [TavilySearchResults(max_results=3)]

# 2. SETUP BRAIN (OpenAI GPT-4o)
llm = ChatOpenAI(model="gpt-4o", temperature=0).bind_tools(tools)

# 3. SYSTEM PROMPT (Simplified)
SYSTEM_PROMPT = """
You are an expert SEO Auditor. 
Your goal is to provide a helpful, data-driven audit of the user's website.

INSTRUCTIONS:
1. Always start by searching for the user's website to see how it appears in results.
2. Look for the homepage title, meta description, and top keywords.
3. Report your findings in this format:

   🚨 **Critical Issues** (Technical problems or missing tags)
   ⚠️ **Warnings** (Content gaps)
   ✅ **Good News** (What is working)
   🚀 **Next Steps** (Actionable advice)

Do not make up information. If you cannot see specific technical details (like page speed), just analyze the visible content and search presence.
"""

# 4. DEFINE STATE
class AgentState(TypedDict):
    messages: Annotated[List[HumanMessage], add_messages]

# 5. DEFINE NODES
def seo_node(state: AgentState):
    messages = state["messages"]
    sys_msg = SystemMessage(content=SYSTEM_PROMPT)
    response = llm.invoke([sys_msg] + messages)
    return {"messages": [response]}

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
