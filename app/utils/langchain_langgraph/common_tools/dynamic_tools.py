from typing import Any

from langchain.tools import tool
from langchain.agents import create_agent
from langchain.agents.middleware import AgentMiddleware, ModelRequest
from langchain.agents.middleware.types import ToolCallRequest, AgentState
from langchain_core.messages import SystemMessage


# A tool that will be added dynamically at runtime， 按需加载，渐进式披露
@tool
def calculate_tip(bill_amount: float, tip_percentage: float = 20.0) -> str:
    """Calculate the tip amount for a bill."""
    tip = bill_amount * (tip_percentage / 100)
    return f"Tip: ${tip:.2f}, Total: ${bill_amount + tip:.2f}"


class DynamicToolMiddleware(AgentMiddleware):
    """Middleware that registers and handles dynamic tools."""

    def wrap_model_call(self, request: ModelRequest, handler):
        # Add dynamic tool to the request
        # This could be loaded from an MCP server, database, etc.
        updated = request.override(tools=[*request.tools, calculate_tip])
        return handler(updated)

    def wrap_tool_call(self, request: ToolCallRequest, handler):
        # Handle execution of the dynamic tool
        if request.tool_call["name"] == "calculate_tip":
            return handler(request.override(tool=calculate_tip))  # type: ignore
        return handler(request)


# 使用中间件来定义自定义状态，当你的自定义状态需要被特定中间件钩子和工具访问时。
class CustomState(AgentState):
    user_preferences: dict


class CustomMiddleware(AgentMiddleware):
    state_schema = CustomState

    # tools = [tool1, tool2]

    def before_model(self, state: CustomState, runtime) -> dict[str, Any] | None:
        '''
        Args:
            state: 当前 Agent 的完整状态，包括你定义的 user_preferences
            runtime: 提供对执行环境的访问（如配置、元数据等）。

        Returns:

        '''
        prefs = state.get("user_preferences", {})
        style = prefs.get("style", "casual")
        verbosity = prefs.get("verbosity", "brief")

        # 2. 构造动态系统提示词
        instruction = f"Please provide a {style} explanation. Be {verbosity}."

        # 3. 将指令注入到消息列表的最前面（或者作为更新返回）
        # 注意：这里我们通过返回字典来更新 state 中的 messages
        current_messages = state["messages"]

        # 检查是否已经注入过，避免重复
        if not any(isinstance(m, SystemMessage) and "style" in m.content for m in current_messages):
            new_system_message = SystemMessage(content=f"[System Instruction] {instruction}")
            return {"messages": [new_system_message] + current_messages}

        return None
