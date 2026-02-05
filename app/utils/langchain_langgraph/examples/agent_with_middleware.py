import os
from dataclasses import dataclass
from typing import TypedDict, List, Callable

from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from langgraph.graph.message import REMOVE_ALL_MESSAGES
from pydantic import BaseModel, Field
from typing import Literal
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage, SystemMessage, ToolMessage, RemoveMessage
from langchain_openai import ChatOpenAI
from langchain.tools import tool, ToolRuntime
from langgraph.types import Command

import config
from app.utils.langchain_langgraph.common_tools.model_selector import create_dynamic_selector
from app.utils.langchain_langgraph.common_tools.standard_tools import get_account_info, UserContext
from app.utils.langchain_langgraph.errors.handle_error import handle_tool_errors

llm_modelscope_cfg = config.LLM['modelscope']

# 3. 初始化模型 (连接到 ModelScope)
# 建议使用 Qwen2.5 系列，它们在工具调用（Tool Calling）上表现非常出色
llm = ChatOpenAI(
    model=llm_modelscope_cfg['model_name'],
    api_key=llm_modelscope_cfg['api_key'],
    base_url=llm_modelscope_cfg['base_url'],
    temperature=0
)

advanced_llm = ChatOpenAI(
    model=llm_modelscope_cfg['model_name'],
    api_key=llm_modelscope_cfg['api_key'],
    base_url=llm_modelscope_cfg['base_url'],
    temperature=1
)

SYSTEM_PROMPT = """You are an expert weather forecaster, who speaks in puns.

You have access to two tools:

- get_weather_for_location: use this to get the weather for a specific location
- get_user_location: use this to get the user's location

If a user asks you for the weather, make sure you know the location. If you can tell from the question that they mean wherever they are, use the get_user_location tool to find their location."""

# print(search.name)  # web_search


@wrap_model_call
def filter_tools(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse],
) -> ModelResponse:
    """Filter tools based on user permissions."""

agent = create_agent(
    model=llm,
    tools=[get_account_info],
    context_schema=UserContext, # type: ignore
    system_prompt=SYSTEM_PROMPT,
    middleware=[handle_tool_errors, create_dynamic_selector(llm, advanced_llm, 8)]
)

result = agent.invoke(
    {"messages": [{"role": "user", "content": "What's my current balance?"}]},
    context=UserContext(user_id="user123")
)
result = agent.invoke(
    {"messages": [{"role": "user", "content": "What's my current balance?"}]},
)

print(result)