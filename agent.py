import os
from typing import TypedDict, Literal, List
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END

# 1. SETUP TOOLS
# We map the tools mentioned in your JSON files to real Python tools
tools = [TavilySearchResults(max_results=3)]

# 2. SETUP BRAIN (LLM)
# We bind the tools so the agent knows it can search the web
llm = ChatOpenAI(model="gpt-4o", temperature=0).bind_tools(tools)

# 3. LOAD YOUR PROMPTS
# We read the instructions from the AGENTS.md file you uploaded
def load_prompt():
    if os.path.exists("AGENTS.md"):
        with open("AGENTS.md", "r") as f:
            return f.read()
    return "You are a helpful SEO assistant."

SYSTEM_PROMPT = load_prompt()

# 4. DEFINE STATE
class AgentState(TypedDict):
    messages: List[HumanMessage]

# 5. DEFINE NODES
def seo_node(state: AgentState):
    """The Main SEO Strategist"""
    messages = state["messages"]
    # Add the system instructions to the conversation
    sys_msg = SystemMessage(content=SYSTEM_PROMPT)
    # Call the AI
    response = llm.invoke([sys_msg] + messages)
    return {"messages": [response]}

def tool_node(state: AgentState):
    """Executes search tools if asked"""
    last_message = state["messages"][-1]
    results = []
    if last_message.tool_calls:
        for tool_call in last_message.tool_calls:
            if tool_call["name"] == "tavily_search_results_json": # LangChain default name
                tool = TavilySearchResults()
                res = tool.invoke(tool_call["args"])
                results.append(HumanMessage(content=str(res)))
    return {"messages": results}

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
