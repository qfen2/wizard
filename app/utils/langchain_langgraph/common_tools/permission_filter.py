from langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from typing import Callable

# 工具过滤
@wrap_model_call
def filter_tools(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse],
) -> ModelResponse:
    """Filter tools based on user permissions."""
    user_role = request.runtime.context.user_role

    if user_role == "admin":
        # Admins get all tools
        tools = request.tools
    else:
        # Regular users get read-only tools
        tools = [t for t in request.tools if t.name.startswith("read_")]

    return handler(request.override(tools=tools))