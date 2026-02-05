"""
中间件管理器使用示例

展示如何在实际场景中使用 MiddlewareManager 来管理 Agent 中间件。
"""

from typing import Any, Dict, Optional
from langchain.agents import create_agent
from langchain.agents.middleware import AgentMiddleware
from langchain.agents.middleware.types import ModelRequest, ModelResponse, ToolCallRequest
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

import config
from app.utils.langchain_langgraph.common_tools.middleware_manager import (
    MiddlewareManager,
    CompositeMiddleware,
    LoggingMiddleware,
    TimingMiddleware,
    create_default_middleware_manager
)
from app.utils.langchain_langgraph.common_tools.standard_tools import get_account_info
from app.utils.langchain_langgraph.errors.handle_error import handle_tool_errors
from app.utils.langchain_langgraph.common_tools.model_selector import create_dynamic_selector

# 配置模型
llm_modelscope_cfg = config.LLM['modelscope']

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

# 自定义中间件示例：权限验证中间件
class PermissionMiddleware(AgentMiddleware):
    """权限验证中间件 - 在执行前检查用户权限。"""

    def __init__(self, allowed_permissions: list[str]):
        """
        初始化权限中间件。

        Args:
            allowed_permissions: 允许的操作列表
        """
        self.allowed_permissions = allowed_permissions

    def wrap_model_call(self, request: ModelRequest, handler) -> ModelResponse:
        """在模型调用前检查权限。"""
        context = request.state.get("context", {})
        user_role = context.get("role", "guest")

        if user_role == "admin":
            # 管理员拥有所有权限
            return handler(request)

        print(f"[Permission] Checking permissions for user: {user_role}")

        # 可以在这里添加更复杂的权限检查逻辑
        return handler(request)


# 自定义中间件示例：请求计数中间件
class CounterMiddleware(AgentMiddleware):
    """请求计数中间件 - 统计请求次数。"""

    def __init__(self):
        """初始化计数中间件。"""
        self.request_count = 0
        self.tool_call_count = 0

    def wrap_model_call(self, request: ModelRequest, handler) -> ModelResponse:
        """统计模型调用次数。"""
        self.request_count += 1
        print(f"[Counter] Total requests: {self.request_count}")

        return handler(request)

    def wrap_tool_call(self, request: ToolCallRequest, handler) -> Any:
        """统计工具调用次数。"""
        self.tool_call_count += 1
        print(f"[Counter] Total tool calls: {self.tool_call_count}")

        return handler(request)

    def get_stats(self) -> Dict[str, int]:
        """获取统计信息。"""
        return {
            "requests": self.request_count,
            "tool_calls": self.tool_call_count
        }


# ==================== 示例 1: 基础使用 ====================
def example_1_basic_usage():
    """示例 1: 基础使用 - 创建管理器并注册中间件"""
    print("\n" + "="*60)
    print("示例 1: 基础使用")
    print("="*60)

    # 创建中间件管理器
    manager = MiddlewareManager()

    # 注册中间件
    manager.register("logging", LoggingMiddleware(verbose=True))
    manager.register("counter", CounterMiddleware())

    # 检查中间件状态
    print(f"Logging 中间件启用: {manager.is_enabled('logging')}")
    print(f"Counter 中间件启用: {manager.is_enabled('counter')}")

    # 获取已启用的中间件
    enabled = manager.get_enabled_middlewares()
    print(f"已启用的中间件数量: {len(enabled)}")


# ==================== 示例 2: 动态启用/禁用中间件 ====================
def example_2_dynamic_control():
    """示例 2: 动态启用/禁用中间件"""
    print("\n" + "="*60)
    print("示例 2: 动态启用/禁用中间件")
    print("="*60)

    # 使用默认管理器
    manager = create_default_middleware_manager()

    print(f"初始状态 - Logging 启用: {manager.is_enabled('logging')}")
    print(f"初始状态 - Timing 启用: {manager.is_enabled('timing')}")

    # 动态启用 timing 中间件
    manager.enable("timing")
    print(f"启用后 - Timing 启用: {manager.is_enabled('timing')}")

    # 禁用 logging 中间件
    manager.disable("logging")
    print(f"禁用后 - Logging 启用: {manager.is_enabled('logging')}")


# ==================== 示例 3: 创建 Agent 并使用中间件 ====================
def example_3_create_agent_with_middleware():
    """示例 3: 创建 Agent 并使用中间件管理器"""
    print("\n" + "="*60)
    print("示例 3: 创建 Agent 并使用中间件管理器")
    print("="*60)

    # 创建中间件管理器
    manager = MiddlewareManager()

    # 注册多个中间件
    manager.register("logging", LoggingMiddleware(verbose=True))
    manager.register("counter", CounterMiddleware())
    manager.register("permission", PermissionMiddleware(allowed_permissions=["read", "write"]))

    # 创建组合中间件
    composite = CompositeMiddleware(manager)

    # 创建 Agent，使用组合中间件
    agent = create_agent(
        model=llm,
        tools=[get_account_info],
        system_prompt="You are a helpful assistant.",
        middleware=[handle_tool_errors, composite]
    )

    print("Agent 创建成功，包含以下中间件:")
    for name in manager.get_all_middlewares().keys():
        print(f"  - {name} (启用: {manager.is_enabled(name)})")


# ==================== 示例 4: 运行时修改中间件配置 ====================
def example_4_runtime_configuration():
    """示例 4: 运行时修改中间件配置"""
    print("\n" + "="*60)
    print("示例 4: 运行时修改中间件配置")
    print("="*60)

    # 创建中间件管理器
    manager = MiddlewareManager()
    counter_middleware = CounterMiddleware()

    # 注册中间件
    manager.register("counter", counter_middleware, enabled=True)
    manager.register("logging", LoggingMiddleware(verbose=False), enabled=False)

    # 创建 Agent
    composite = CompositeMiddleware(manager)
    agent = create_agent(
        model=llm,
        tools=[get_account_info],
        system_prompt="You are a helpful assistant.",
        middleware=[handle_tool_errors, composite]
    )

    # 第一次调用（Counter 启用）
    print("\n第一次调用:")
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "What's my current balance?"}]},
        context={"user_id": "user123"}
    )

    # 禁用 Counter，启用 Logging
    print("\n修改中间件配置...")
    manager.disable("counter")
    manager.enable("logging")

    # 第二次调用（Logging 启用）
    print("\n第二次调用:")
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "What's my current balance?"}]},
        context={"user_id": "user123"}
    )

    # 获取统计信息
    print(f"\n统计信息: {counter_middleware.get_stats()}")


# ==================== 示例 5: 获取计时统计 ====================
def example_5_timing_statistics():
    """示例 5: 使用计时中间件获取性能统计"""
    print("\n" + "="*60)
    print("示例 5: 使用计时中间件获取性能统计")
    print("="*60)

    # 创建中间件管理器
    manager = MiddlewareManager()
    timing = TimingMiddleware()

    # 注册中间件
    manager.register("timing", timing, enabled=True)
    manager.register("logging", LoggingMiddleware(verbose=False), enabled=True)

    # 创建 Agent
    composite = CompositeMiddleware(manager)
    agent = create_agent(
        model=llm,
        tools=[get_account_info],
        system_prompt="You are a helpful assistant.",
        middleware=[handle_tool_errors, composite]
    )

    # 执行多次调用
    print("执行 3 次调用...")
    for i in range(3):
        print(f"\n调用 {i+1}:")
        result = agent.invoke(
            {"messages": [{"role": "user", "content": "What's my current balance?"}]},
            context={"user_id": "user123"}
        )

    # 获取统计信息
    print("\n" + "="*60)
    print("性能统计:")
    print("="*60)
    stats = timing.get_statistics()
    for key, value in stats.items():
        if key == "tools":
            print(f"\n工具统计:")
            for tool_name, tool_stats in value.items():
                print(f"  {tool_name}:")
                for stat_name, stat_value in tool_stats.items():
                    print(f"    {stat_name}: {stat_value:.3f}" if isinstance(stat_value, float) else f"    {stat_name}: {stat_value}")
        else:
            print(f"{key}: {value:.3f}" if isinstance(value, float) else f"{key}: {value}")


# ==================== 示例 6: 组合多种中间件 ====================
def example_6_complex_middleware_stack():
    """示例 6: 组合多种中间件构建复杂的处理链"""
    print("\n" + "="*60)
    print("示例 6: 组合多种中间件构建复杂的处理链")
    print("="*60)

    # 创建中间件管理器
    manager = MiddlewareManager()

    # 注册多个中间件（按执行顺序）
    manager.register("permission", PermissionMiddleware(allowed_permissions=["read", "write"]))
    manager.register("logging", LoggingMiddleware(verbose=True))
    manager.register("counter", CounterMiddleware())
    manager.register("timing", TimingMiddleware())

    print("中间件链（按执行顺序）:")
    for i, name in enumerate(manager.get_all_middlewares().keys(), 1):
        print(f"  {i}. {name}")

    # 创建 Agent
    composite = CompositeMiddleware(manager)
    agent = create_agent(
        model=llm,
        tools=[get_account_info],
        system_prompt="You are a helpful assistant.",
        middleware=[handle_tool_errors, composite]
    )

    print("\n执行调用...")
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "What's my current balance?"}]},
        context={"user_id": "user123", "role": "admin"}
    )


# ==================== 主函数 ====================
if __name__ == "__main__":
    # 运行所有示例
    example_1_basic_usage()
    example_2_dynamic_control()
    example_3_create_agent_with_middleware()
    example_4_runtime_configuration()
    example_5_timing_statistics()
    example_6_complex_middleware_stack()

    print("\n" + "="*60)
    print("所有示例运行完成！")
    print("="*60)