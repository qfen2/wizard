# coding: utf-8
"""
Agent 工厂模块

负责初始化和配置 LangChain Agent，提供统一的 Agent 创建接口。
"""

from typing import Callable, Optional

from langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse, PIIMiddleware, \
    HumanInTheLoopMiddleware
from langchain.agents.structured_output import ToolStrategy, ProviderStrategy
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command
from pydantic import BaseModel

import config
from app.utils.langchain_langgraph.common_tools.dynamic_tools import CustomMiddleware
from app.utils.langchain_langgraph.common_tools.model_selector import create_dynamic_selector
from app.utils.langchain_langgraph.common_tools.standard_tools import get_account_info, UserContext, send_email, search, \
    delete_database
from app.utils.langchain_langgraph.errors.handle_error import handle_tool_errors


class ContactInfo(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None


def create_models():
    """
    创建基础模型和高级模型实例
    
    Returns:
        tuple: (基础模型, 高级模型)
    """
    llm_modelscope_cfg = config.LLM['modelscope']

    # 基础模型：用于简单任务
    basic_llm = ChatOpenAI(
        model=llm_modelscope_cfg['model_name'],
        api_key=llm_modelscope_cfg['api_key'],
        base_url=llm_modelscope_cfg['base_url'],
        temperature=0
    )

    # 高级模型：用于复杂任务（温度更高，更有创造性）
    advanced_llm = ChatOpenAI(
        model=llm_modelscope_cfg['model_name'],
        api_key=llm_modelscope_cfg['api_key'],
        base_url=llm_modelscope_cfg['base_url'],
        temperature=1
    )

    return basic_llm, advanced_llm


def create_account_agent():
    """
    创建账户查询 Agent
    
    该 Agent 配置了：
    - 动态模型选择（根据对话复杂度切换模型）
    - 错误处理中间件
    - 用户账户信息查询工具
    
    Returns:
        Agent: 配置好的 Agent 实例
    """
    # 创建模型实例
    basic_llm, advanced_llm = create_models()

    # 系统提示词
    # SYSTEM_PROMPT = """You are an expert weather forecaster, who speaks in puns.
    #
    # You have access to two tools:
    #
    # - get_weather_for_location: use this to get the weather for a specific location
    # - get_user_location: use this to get the user's location
    #
    # If a user asks you for the weather, make sure you know the location. If you can tell from the question that they mean wherever they are, use the get_user_location tool to find their location.
    #
    # You must respond in JSON format.
    # """

    SYSTEM_PROMPT = '''You are an AI assistant. 
     - send_email : 发送邮件
    '''

    # 创建 Agent
    agent = create_agent(
        model=basic_llm,
        tools=[send_email, search, delete_database],
        context_schema=UserContext,  # type: ignore
        system_prompt=SYSTEM_PROMPT,
        checkpointer=InMemorySaver(),
        response_format=ToolStrategy(ContactInfo),  # 结构化输出，如果结果无法支持其格式化，则没有structured_response
        # response_format=ProviderStrategy(ContactInfo), # 仅主流高端模型 (OpenAI, Gemini, etc.)，直接在 Message 中生成结构化文本
        middleware=[
            PIIMiddleware(
                "email",
                strategy="mask",
                apply_to_input=True,
            ),
            # Mask credit cards in user input
            PIIMiddleware(
                "credit_card",
                strategy="mask",
                apply_to_input=True,
            ),
            HumanInTheLoopMiddleware(
                interrupt_on={
                    # Require approval for sensitive operations
                    "send_email": True,
                    "delete_database": True,
                    # Auto-approve safe operations
                    "search": False,
                }
            ),
            handle_tool_errors,
            create_dynamic_selector(basic_llm, advanced_llm, threshold=8),
            CustomMiddleware(),  # 使用中间件来定义自定义状态，当你的自定义状态需要被特定中间件钩子和工具访问时。
        ]
    )

    return agent


@wrap_model_call
def filter_tools(
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
) -> ModelResponse:
    """Filter tools based on user permissions."""
    # TODO: 实现工具过滤逻辑
    return handler(request)


# ==================== 使用示例 ====================

if __name__ == "__main__":
    # 创建 Agent
    agent = create_account_agent()
    config = {"configurable": {"thread_id": "14k234j1h3k4h132jh412k3j"}}

    # 调用 Agent
    result = agent.invoke(
        # {"messages": [{"role": "user", "content": "我的邮箱是 john@doe.com，信用卡卡号是 1111-2222-3333-4444"}],
        {"messages": [{"role": "user", "content": "调用send_email工具发送邮件"}],
         "user_preferences": {"style": "technical", "verbosity": "detailed"}, },
        # 使用中间件来定义自定义状态，当你的自定义状态需要被特定中间件钩子和工具访问时。
        context=UserContext(user_id="user123"),
        config=config,
    )

    print("Agent 响应:")
    result1 = agent.invoke(Command(resume={
                "decisions": [
                    {
                        "type": "approve"  # 对应你截图中的 allowed_decisions: ['approve']
                    }
                ]
            }),
        config=config,
    )
    print(result)
    # 结构化输出结果
    print(result["structured_response"])

    # 流式传输
    # for chunk in agent.stream({
    #     "messages": [{"role": "user", "content": "我的邮箱是 john@doe.com，卡号是 1111-2222-3333-4444"}]
    # }, stream_mode="values"):
    #     # Each chunk contains the full state at that point
    #     print('*'*100)
    #     latest_message = chunk["messages"][-1]
    #     if latest_message.content:
    #         print(f"Agent: {latest_message.content}")
    #     elif latest_message.tool_calls:
    #         print(f"Calling tools: {[tc['name'] for tc in latest_message.tool_calls]}")
