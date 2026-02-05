import os
from typing import TypedDict, List

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage, SystemMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent, ToolRuntime  # LangChain 1.x 官方推荐的 Agent 创建器
from langgraph.types import Command
from dataclasses import dataclass
import config

# 1. 配置 ModelScope 凭证
MODELSCOPE_API_KEY = "你的_MODELSCOPE_SDK_TOKEN"
MODELSCOPE_BASE_URL = "https://api-inference.modelscope.cn/v1"


class AgentState(TypedDict):
    messages: List[BaseMessage]


# 2. 定义工具
# 使用 @tool 装饰器能自动将函数文档转化为模型可理解的工具描述
@tool
def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always rainy in {city}!"


# tools = [get_weather]

llm_modelscope_cfg = config.LLM['modelscope']

# 3. 初始化模型 (连接到 ModelScope)
# 建议使用 Qwen2.5 系列，它们在工具调用（Tool Calling）上表现非常出色
llm = ChatOpenAI(
    model=llm_modelscope_cfg['model_name'],
    api_key=llm_modelscope_cfg['api_key'],
    base_url=llm_modelscope_cfg['base_url'],
    temperature=0
)

# 4. 创建 Agent
# 这对应了你示例代码中的 create_agent，底层由 LangGraph 驱动
# agent = create_agent(
#     model=llm,
#     tools=tools,
# )

# 5. 运行 Agent
# 注意：create_react_agent 的输入输出遵循标准的消息格式
inputs = {
    "messages": [
        SystemMessage(content="你是一个助手"),
        HumanMessage(content="旧金山天气？"),
        # AI 决定调用工具 (由模型生成)
        # AIMessage(
        #     content="",
        #     tool_calls=[{
        #         "name": "get_weather",
        #         "args": {"city": "San Francisco"},
        #         "id": "call_12345"  # 这个 ID 很重要
        #     }]
        # ),
        # 工具返回的结果
        # ToolMessage(
        #     content="It's always rainy in San Francisco!",
        #     tool_call_id="call_12345"  # 必须与上面的 ID 对应
        # )
    ]
}
# result = agent.invoke(inputs, config={"configurable": {"thread_id": "user_session_001"}})  # type: ignore
#
# # 打印最后一条回复
# print(result["messages"][-1].content)


# 1. 定义上下文结构
@dataclass
class Context:
    """自定义运行时上下文架构。"""
    user_id: str

# 2. 定义工具
@tool
def get_weather_for_location(city: str) -> str:
    """获取指定城市的实时天气。"""
    return f"It's always sunny in {city}!"

@tool
def get_user_location(runtime: ToolRuntime[Context]) -> str:
    """根据用户 ID 检索其地理位置。
    注意：runtime 参数由系统自动注入，模型不会看到这个参数。
    """
    # 从运行时上下文中提取 user_id
    user_id = runtime.context.user_id
    # 模拟数据库查询逻辑
    return "Florida" if user_id == "1" else "SF"

# 4. 创建 Agent
# 关键点：指定 context_schema，这让 Agent 知道如何处理 ToolRuntime
tools = [get_weather_for_location, get_user_location]

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant. Always output your response in JSON format."),
    ("placeholder", "{messages}"),
])


# We use a dataclass here, but Pydantic models are also supported.
@dataclass
class ResponseFormat:
    """Response schema for the agent."""
    # A punny response (always required)
    punny_response: str
    # Any interesting information about the weather if available
    weather_conditions: str | None = None


agent = create_agent(
    model=llm,
    tools=tools,
    context_schema=Context, # type: ignore
    response_format=ResponseFormat,
)

# 2. 将结构化输出绑定到模型
# 此时 LLM 就像被"戴上了紧箍咒"，输出必须符合 ResponseFormat 结构

# 3. 在 Agent 执行或链中调用
input = {"messages": [("user", "What's the weather like in Florida?")]}
result = agent.invoke(input, context=Context(user_id="2"))

# 4. 像对象一样直接访问属性
print(f"Humor: {result}")