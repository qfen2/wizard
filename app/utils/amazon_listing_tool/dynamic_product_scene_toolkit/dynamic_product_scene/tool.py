# -*- coding: utf-8 -*-
"""Public tool facade for integration into an existing application."""

from __future__ import annotations

from typing import Optional

from .graph import DynamicProductSceneGraph
from .schemas import ImageWorkflowState


class DynamicProductSceneTool:
    """
    Existing-project friendly facade.

    Use this class when the package is copied into another project as a utility module.
    It hides the internal LangGraph naming and exposes a simple tool-style API.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        planner_model: str = "gpt-4.1",
        image_model: str = "gpt-image-2",
        output_dir: str = "generated_images",
        temp_dir: str = "temp_product_assets",
    ):
        self.graph = DynamicProductSceneGraph(
            api_key=api_key,
            planner_model=planner_model,
            image_model=image_model,
            output_dir=output_dir,
            temp_dir=temp_dir,
        )

    def generate_usage_scenes(
        self,
        image_path: str,
        user_request: str = "生成该商品在不同使用场景中的电商详情页图片。",
        scene_count: int = 4,
        size: str = "1024x1024",
        quality: str = "high",
        output_dir: Optional[str] = None,
        temp_dir: Optional[str] = None,
        enable_verify: bool = False,
        user_id: str = "",
        request_id: Optional[str] = None,
    ) -> ImageWorkflowState:
        """
        Generate multiple usage-scene images from one product image.

        The user does not need to provide scale, position, or rotation.
        The LLM plans those values dynamically, and the compositor executes them.
        """
        return self.graph.invoke(
            image_path=image_path,
            user_request=user_request,
            scene_count=scene_count,
            size=size,
            quality=quality,
            output_dir=output_dir,
            temp_dir=temp_dir,
            enable_verify=enable_verify,
            user_id=user_id,
            request_id=request_id,
        )

    def invoke(self, *args, **kwargs) -> ImageWorkflowState:
        """
        Alias for compatibility with LangGraph-style callers.
        """
        return self.generate_usage_scenes(*args, **kwargs)

    def build_langchain_tools(self):
        """Optional LangChain Tool wrappers for Agent / ToolNode integration."""
        return self.graph.build_langchain_tools()
