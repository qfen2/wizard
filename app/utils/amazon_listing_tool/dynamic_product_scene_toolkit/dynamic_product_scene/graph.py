# -*- coding: utf-8 -*-
"""LangGraph orchestration for dynamic product usage-scene generation."""

from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from openai import OpenAI
from langgraph.graph import END, START, StateGraph

from .background import BackgroundGenerator
from .compositor import ProductCompositor
from .planner import ScenePlanner
from .schemas import ImageRuntimeContext, ImageWorkflowState
from .segmenter import AutoProductSegmenter
from .tools import build_langchain_tools
from .utils import clamp_float, ensure_dir
from .verifier import ProductConsistencyVerifier


class DynamicProductSceneGraph:
    """
    商品原图 → 多使用场景图的专项工作流。

    输入：一张商品原图。
    输出：多张不同使用场景图。

    分工：
    - LLM: 分析商品、规划场景、自动决定商品大小/位置/角度。
    - GPT Image: 生成没有主商品的背景场景。
    - 程序: 自动抠图、缩放、移动、旋转、合成，尽量保持商品结构。
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        planner_model: str = "gpt-4.1",
        image_model: str = "gpt-image-2",
        output_dir: str = "generated_images",
        temp_dir: str = "temp_product_assets",
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("请传入 api_key 或设置 OPENAI_API_KEY 环境变量。")

        self.client = OpenAI(api_key=self.api_key)
        self.planner_model = planner_model
        self.image_model = image_model
        self.output_dir = ensure_dir(output_dir)
        self.temp_dir = ensure_dir(temp_dir)

        self.segmenter = AutoProductSegmenter(temp_dir=str(self.temp_dir))
        self.planner = ScenePlanner(client=self.client, planner_model=self.planner_model)
        self.background_generator = BackgroundGenerator(client=self.client, image_model=self.image_model)
        self.compositor = ProductCompositor()
        self.verifier = ProductConsistencyVerifier(client=self.client, planner_model=self.planner_model)

        self.graph = self._build_graph()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def invoke(
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
        一次性执行完整流程。

        用户只需要传商品原图和自然语言需求。
        商品的缩放、位置、角度由 LLM 在 plan_scenes 节点自动规划。
        """
        image_path = str(image_path)
        if not Path(image_path).exists():
            raise FileNotFoundError(f"商品原图不存在：{image_path}")

        request_id = request_id or uuid.uuid4().hex

        init_state: ImageWorkflowState = {
            "user_request": user_request,
            "image_path": image_path,
            "backgrounds": [],
            "results": [],
            "verifications": [],
        }

        context: ImageRuntimeContext = {
            "user_id": user_id,
            "request_id": request_id,
            "output_dir": output_dir or str(self.output_dir),
            "temp_dir": temp_dir or str(self.temp_dir),
            "scene_count": scene_count,
            "size": size,
            "quality": quality,
            "enable_verify": enable_verify,
        }

        return self.graph.invoke(init_state, context=context)

    def build_langchain_tools(self):
        """Optional LangChain Tool wrappers for Agent / ToolNode integration."""
        return build_langchain_tools(self)

    # ------------------------------------------------------------------
    # Graph construction
    # ------------------------------------------------------------------

    def _build_graph(self):
        builder = StateGraph(ImageWorkflowState, context_schema=ImageRuntimeContext)

        builder.add_node("segment_product", self._segment_product_node)
        builder.add_node("plan_scenes", self._plan_scenes_node)
        builder.add_node("generate_backgrounds", self._generate_backgrounds_node)
        builder.add_node("compose_results", self._compose_results_node)
        builder.add_node("verify_results", self._verify_results_node)
        builder.add_node("summarize", self._summarize_node)

        builder.add_edge(START, "segment_product")
        builder.add_edge("segment_product", "plan_scenes")
        builder.add_edge("plan_scenes", "generate_backgrounds")
        builder.add_edge("generate_backgrounds", "compose_results")
        builder.add_edge("compose_results", "verify_results")
        builder.add_edge("verify_results", "summarize")
        builder.add_edge("summarize", END)

        return builder.compile()

    @staticmethod
    def _ctx(runtime: Any, key: str, default: Any = None) -> Any:
        """Compatible runtime.context getter for dict or object context."""
        ctx = getattr(runtime, "context", None)
        if ctx is None:
            return default
        if isinstance(ctx, dict):
            return ctx.get(key, default)
        return getattr(ctx, key, default)

    # ------------------------------------------------------------------
    # Node 1: product segmentation
    # ------------------------------------------------------------------

    def _segment_product_node(self, state: ImageWorkflowState, runtime: Any) -> ImageWorkflowState:
        try:
            temp_dir = self._ctx(runtime, "temp_dir", str(self.temp_dir))
            result = self.segmenter.segment(state["image_path"], temp_dir=temp_dir)
            return {
                **state,
                "foreground_path": result["foreground_path"],
                "mask_path": result["mask_path"],
            }
        except Exception as e:
            return {**state, "error": f"segment_product 失败：{e}"}

    # ------------------------------------------------------------------
    # Node 2: product analysis + scene/layout planning
    # ------------------------------------------------------------------

    def _plan_scenes_node(self, state: ImageWorkflowState, runtime: Any) -> ImageWorkflowState:
        if state.get("error"):
            return state

        scene_count = int(self._ctx(runtime, "scene_count", 4))
        try:
            plan = self.planner.plan(
                image_path=state["image_path"],
                user_request=state.get("user_request", "生成商品使用场景图。"),
                scene_count=scene_count,
            )
        except Exception:
            # Fallback prevents the whole workflow from collapsing if JSON planning fails.
            plan = self.planner.fallback_tool_plan(scene_count=scene_count)

        clean_scenes: List[Dict[str, Any]] = []
        for s in plan.scenes[:scene_count]:
            sd = s.model_dump()
            sd["target_width_ratio"] = clamp_float(sd.get("target_width_ratio"), 0.25, 0.90, 0.65)
            sd["center_x_ratio"] = clamp_float(sd.get("center_x_ratio"), 0.05, 0.95, 0.55)
            sd["center_y_ratio"] = clamp_float(sd.get("center_y_ratio"), 0.10, 0.92, 0.60)
            sd["rotation_degrees"] = clamp_float(sd.get("rotation_degrees"), -35, 35, 0)
            clean_scenes.append(sd)

        return {
            **state,
            "product_analysis": plan.product.model_dump(),
            "scene_plans": clean_scenes,
            "error": None,
        }

    # ------------------------------------------------------------------
    # Node 3: background generation
    # ------------------------------------------------------------------

    def _generate_backgrounds_node(self, state: ImageWorkflowState, runtime: Any) -> ImageWorkflowState:
        if state.get("error"):
            return state

        output_dir = str(ensure_dir(self._ctx(runtime, "output_dir", str(self.output_dir))))
        size = self._ctx(runtime, "size", "1024x1024")
        quality = self._ctx(runtime, "quality", "high")

        backgrounds: List[Dict[str, Any]] = []
        for idx, scene in enumerate(state.get("scene_plans", []), start=1):
            try:
                backgrounds.append(
                    self.background_generator.generate(
                        scene=scene,
                        output_dir=output_dir,
                        size=size,
                        quality=quality,
                    )
                )
            except Exception as e:
                backgrounds.append(
                    {
                        "scene_name": scene.get("name", f"scene_{idx}"),
                        "success": False,
                        "error": str(e),
                    }
                )

        return {**state, "backgrounds": backgrounds}

    # ------------------------------------------------------------------
    # Node 4: composition
    # ------------------------------------------------------------------

    def _compose_results_node(self, state: ImageWorkflowState, runtime: Any) -> ImageWorkflowState:
        if state.get("error"):
            return state

        output_dir = ensure_dir(self._ctx(runtime, "output_dir", str(self.output_dir)))
        foreground_path = state.get("foreground_path")
        if not foreground_path:
            return {**state, "error": "缺少 foreground_path，无法合成商品。"}

        results: List[Dict[str, Any]] = []
        for scene, bg in zip(state.get("scene_plans", []), state.get("backgrounds", [])):
            scene_name = scene.get("name", "scene")
            try:
                if not bg.get("background_path"):
                    raise ValueError(bg.get("error", "背景生成失败"))

                output_path = str(output_dir / f"final_{scene_name}_{uuid.uuid4().hex}.png")
                image_path = self.compositor.compose(
                    background_path=bg["background_path"],
                    foreground_path=foreground_path,
                    scene=scene,
                    output_path=output_path,
                )
                results.append(
                    {
                        "success": True,
                        "scene_name": scene_name,
                        "image_path": image_path,
                        "background_path": bg["background_path"],
                        "layout": {
                            "target_width_ratio": scene.get("target_width_ratio"),
                            "center_x_ratio": scene.get("center_x_ratio"),
                            "center_y_ratio": scene.get("center_y_ratio"),
                            "rotation_degrees": scene.get("rotation_degrees"),
                            "depth_layer": scene.get("depth_layer"),
                            "visual_role": scene.get("visual_role"),
                            "shadow_strength": scene.get("shadow_strength"),
                        },
                        "scene_prompt": scene.get("scene_prompt"),
                        "usage_context": scene.get("usage_context"),
                    }
                )
            except Exception as e:
                results.append({"success": False, "scene_name": scene_name, "error": str(e)})

        return {**state, "results": results}

    # ------------------------------------------------------------------
    # Node 5: optional visual verification
    # ------------------------------------------------------------------

    def _verify_results_node(self, state: ImageWorkflowState, runtime: Any) -> ImageWorkflowState:
        if state.get("error"):
            return state

        if not bool(self._ctx(runtime, "enable_verify", False)):
            return {**state, "verifications": []}

        verifications: List[Dict[str, Any]] = []
        source = state.get("image_path")
        for result in state.get("results", []):
            if not result.get("success") or not result.get("image_path"):
                continue
            try:
                check = self.verifier.verify(
                    original_image_path=source,
                    final_image_path=result["image_path"],
                )
                result["verification"] = check
                verifications.append({"scene_name": result.get("scene_name"), "verification": check})
            except Exception as e:
                verifications.append({"scene_name": result.get("scene_name"), "error": str(e)})

        return {**state, "verifications": verifications, "results": state.get("results", [])}

    # ------------------------------------------------------------------
    # Node 6: summarize
    # ------------------------------------------------------------------

    def _summarize_node(self, state: ImageWorkflowState) -> ImageWorkflowState:
        results = state.get("results", [])
        success_items = [r for r in results if r.get("success")]

        summary = {
            "success_count": len(success_items),
            "total": len(results),
            "image_paths": [r.get("image_path") for r in success_items if r.get("image_path")],
            "foreground_path": state.get("foreground_path"),
            "mask_path": state.get("mask_path"),
            "error": state.get("error"),
        }
        return {**state, "summary": summary}
