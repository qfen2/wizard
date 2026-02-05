"""
中间件管理器 - 用于注册、管理和组合 LangChain Agent 中间件。

提供统一的接口来管理多个中间件，支持中间件的注册、移除、启用和禁用。
"""

from typing import Any, Callable, Dict, List, Optional, Type
from langchain.agents.middleware import AgentMiddleware
from langchain.agents.middleware.types import ModelRequest, ModelResponse, ToolCallRequest


class MiddlewareManager:
    """中间件管理器，用于统一管理多个中间件实例。"""

    def __init__(self):
        """初始化中间件管理器。"""
        self._middlewares: Dict[str, AgentMiddleware] = {}
        self._enabled_middleware: Dict[str, bool] = {}

    def register(self, name: str, middleware: AgentMiddleware, enabled: bool = True) -> None:
        """
        注册中间件。

        Args:
            name: 中间件唯一标识名称
            middleware: 中间件实例
            enabled: 是否启用该中间件，默认为 True
        """
        self._middlewares[name] = middleware
        self._enabled_middleware[name] = enabled

    def unregister(self, name: str) -> bool:
        """
        注销中间件。

        Args:
            name: 要注销的中间件名称

        Returns:
            是否成功注销
        """
        if name in self._middlewares:
            del self._middlewares[name]
            del self._enabled_middleware[name]
            return True
        return False

    def enable(self, name: str) -> bool:
        """
        启用指定中间件。

        Args:
            name: 中间件名称

        Returns:
            是否成功启用
        """
        if name in self._middlewares:
            self._enabled_middleware[name] = True
            return True
        return False

    def disable(self, name: str) -> bool:
        """
        禁用指定中间件。

        Args:
            name: 中间件名称

        Returns:
            是否成功禁用
        """
        if name in self._middlewares:
            self._enabled_middleware[name] = False
            return True
        return False

    def is_enabled(self, name: str) -> bool:
        """
        检查中间件是否启用。

        Args:
            name: 中间件名称

        Returns:
            是否启用
        """
        return self._enabled_middleware.get(name, False)

    def get_enabled_middlewares(self) -> List[AgentMiddleware]:
        """
        获取所有已启用的中间件列表。

        Returns:
            已启用的中间件列表
        """
        return [
            self._middlewares[name]
            for name, enabled in self._enabled_middleware.items()
            if enabled
        ]

    def get_all_middlewares(self) -> Dict[str, AgentMiddleware]:
        """
        获取所有已注册的中间件。

        Returns:
            所有中间件的字典 {name: middleware}
        """
        return self._middlewares.copy()

    def get_middleware(self, name: str) -> Optional[AgentMiddleware]:
        """
        获取指定名称的中间件。

        Args:
            name: 中间件名称

        Returns:
            中间件实例，如果不存在则返回 None
        """
        return self._middlewares.get(name)


class CompositeMiddleware(AgentMiddleware):
    """
    组合中间件 - 将多个中间件组合成一个中间件。

    按注册顺序依次执行所有中间件。
    """

    def __init__(self, manager: MiddlewareManager):
        """
        初始化组合中间件。

        Args:
            manager: 中间件管理器
        """
        self.manager = manager

    def wrap_model_call(self, request: ModelRequest, handler) -> Any:
        """组合所有启用的中间件的 model_call 钩子。"""
        enabled_middlewares = self.manager.get_enabled_middlewares()

        def composite_handler(req: ModelRequest) -> Any:
            """递归应用所有中间件。"""
            if not enabled_middlewares:
                return handler(req)

            # 取出第一个中间件
            middleware = enabled_middlewares[0]
            remaining = enabled_middlewares[1:]

            # 为剩余中间件创建新的组合处理器
            def next_handler(r: ModelRequest) -> Any:
                # 临时替换管理器以使用剩余中间件
                temp_manager = MiddlewareManager()
                for mw in remaining:
                    temp_manager.register(type(mw).__name__, mw, enabled=True)
                composite = CompositeMiddleware(temp_manager)
                return composite.wrap_model_call(r, handler)

            return middleware.wrap_model_call(req, next_handler)

        return composite_handler(request)


class LoggingMiddleware(AgentMiddleware):
    """
    日志中间件 - 记录模型调用和工具调用信息。

    用于调试和监控 Agent 行为。
    """

    def __init__(self, verbose: bool = True):
        """
        初始化日志中间件。

        Args:
            verbose: 是否输出详细日志
        """
        self.verbose = verbose

    def wrap_model_call(self, request: ModelRequest, handler) -> ModelResponse:
        """记录模型调用前后的信息。"""
        if self.verbose:
            print(f"[Middleware] Model call started with {len(request.state.get('messages', []))} messages")

        response = handler(request)

        if self.verbose:
            print(f"[Middleware] Model call completed")

        return response

    def wrap_tool_call(self, request: ToolCallRequest, handler) -> Any:
        """记录工具调用信息。"""
        tool_name = request.tool_call.get("name", "unknown")

        if self.verbose:
            print(f"[Middleware] Tool call: {tool_name}")

        result = handler(request)

        if self.verbose:
            print(f"[Middleware] Tool call completed: {tool_name}")

        return result


class TimingMiddleware(AgentMiddleware):
    """
    计时中间件 - 测量模型调用和工具调用的执行时间。

    用于性能分析和优化。
    """

    def __init__(self):
        """初始化计时中间件。"""
        import time
        self.time_module = time
        self.model_times: List[float] = []
        self.tool_times: Dict[str, List[float]] = {}

    def wrap_model_call(self, request: ModelRequest, handler) -> ModelResponse:
        """测量模型调用时间。"""
        start_time = self.time_module.time()
        response = handler(request)
        end_time = self.time_module.time()

        elapsed = end_time - start_time
        self.model_times.append(elapsed)
        print(f"[Timing] Model call took {elapsed:.3f}s")

        return response

    def wrap_tool_call(self, request: ToolCallRequest, handler) -> Any:
        """测量工具调用时间。"""
        tool_name = request.tool_call.get("name", "unknown")

        start_time = self.time_module.time()
        result = handler(request)
        end_time = self.time_module.time()

        elapsed = end_time - start_time

        if tool_name not in self.tool_times:
            self.tool_times[tool_name] = []
        self.tool_times[tool_name].append(elapsed)

        print(f"[Timing] Tool '{tool_name}' took {elapsed:.3f}s")

        return result

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取计时统计信息。

        Returns:
            统计信息字典
        """
        import statistics

        stats = {}

        if self.model_times:
            stats["model_calls"] = len(self.model_times)
            stats["model_avg_time"] = statistics.mean(self.model_times)
            stats["model_max_time"] = max(self.model_times)
            stats["model_min_time"] = min(self.model_times)
            stats["model_total_time"] = sum(self.model_times)

        stats["tools"] = {}
        for tool_name, times in self.tool_times.items():
            stats["tools"][tool_name] = {
                "calls": len(times),
                "avg_time": statistics.mean(times),
                "max_time": max(times),
                "min_time": min(times),
                "total_time": sum(times),
            }

        return stats


def create_default_middleware_manager() -> MiddlewareManager:
    """
    创建包含常用默认中间件的管理器实例。

    Returns:
        配置好的中间件管理器
    """
    manager = MiddlewareManager()

    # 注册默认中间件
    manager.register("logging", LoggingMiddleware(verbose=False))
    manager.register("timing", TimingMiddleware(), enabled=False)

    return manager