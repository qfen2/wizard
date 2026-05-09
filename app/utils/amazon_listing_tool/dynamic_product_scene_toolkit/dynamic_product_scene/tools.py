# -*- coding: utf-8 -*-
"""Optional LangChain tool wrappers."""

from __future__ import annotations

import json
from typing import Any

from langchain_core.tools import tool as langchain_tool


def build_langchain_tools(graph_tool: Any):
    """
    Build optional LangChain Tools.

    当前核心流程是 LangGraph 自定义节点，不依赖 ToolNode。
    这个函数只用于后续把该工作流挂到 Agent / ToolNode 时使用。
    """

    @langchain_tool
    def generate_product_usage_scenes(
        image_path: str,
        user_request: str = "生成该商品在不同使用场景中的电商详情页图片。",
        scene_count: int = 4,
    ) -> str:
        """Generate multiple product usage-scene images from one product image."""
        state = graph_tool.invoke(
            image_path=image_path,
            user_request=user_request,
            scene_count=scene_count,
        )
        return json.dumps(
            {
                "summary": state.get("summary"),
                "results": state.get("results", []),
                "product_analysis": state.get("product_analysis"),
            },
            ensure_ascii=False,
        )

    return [generate_product_usage_scenes]
