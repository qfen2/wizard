import operator
from typing import Annotated, List, TypedDict, Literal
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.agents import create_agent
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

# 1. 定义 Agent 状态
class AgentState(TypedDict):
    # 使用 Annotated 和 add_messages 自动合并对话流
    messages: Annotated[List, operator.add]
    draft: str
    critique: str
    revision_count: int

# 初始化模型
llm = ChatOpenAI(model="gpt-4o", temperature=0)
search_tool = TavilySearchResults(max_results=3)