# -*- coding: utf-8 -*-
"""LLM product analysis and dynamic scene/layout planning."""

from __future__ import annotations

from typing import List

from openai import OpenAI

from .schemas import MultiScenePlan, ProductAnalysis, ScenePlan
from .utils import extract_json, image_to_data_url


class ScenePlanner:
    """
    大模型规划模块。

    负责：
    1. 分析商品类型和保真等级；
    2. 规划多种使用场景；
    3. 自动决定每个场景中的商品大小、位置和轻微旋转角度。
    """

    def __init__(self, client: OpenAI, planner_model: str = "gpt-4.1"):
        self.client = client
        self.planner_model = planner_model

    def plan(self, image_path: str, user_request: str, scene_count: int = 4) -> MultiScenePlan:
        image_url = image_to_data_url(image_path)

        prompt = f"""
你是电商商品场景图导演、商业摄影构图师、工具/五金类商品视觉质检专家。

用户上传了一张商品原图。请你分析商品，并规划 {scene_count} 张不同使用场景图。

用户需求：
{user_request}

核心目标：
1. 生成不同使用场景，不是只换背景。
2. 商品可以在不同场景中自然变大、变小、改变位置、轻微旋转。
3. 用户不会手动指定缩放、位置、角度；这些由你根据场景自动规划。
4. 如果商品是工具、五金、机械、电子配件，必须选择 pixel 或 strict 保真策略。
5. 场景优先做“电商可控的轻使用场景/上下文使用场景”，不要强行规划复杂手握、遮挡、精密接触动作。
6. 背景 prompt 必须要求：不要生成同款主商品；要留出自然空间用于后期贴入商品。
7. target_width_ratio 取 0.25~0.90；工具类通常 0.45~0.80。
8. center_x_ratio / center_y_ratio 取 0~1。
9. rotation_degrees 工具类建议 -25~25，必要时可到 -35~35。
10. 场景要真实、商业摄影、电商详情页/广告可用。

请严格输出 JSON，不要解释，不要 Markdown。格式：
{{
  "product": {{
    "product_name": "adjustable wrench",
    "category": "tool",
    "preserve_level": "pixel",
    "key_structure_points": ["adjustable jaw", "worm gear", "handle hole", "metal outline"],
    "risk_points": ["jaw shape may change", "worm gear may disappear", "handle hole may change"]
  }},
  "scenes": [
    {{
      "name": "workbench_repair_scene",
      "scene_prompt": "A realistic wooden workbench repair scene with screws, bolts, and wood pieces nearby, warm workshop lighting, an empty open area reserved for placing the main product in the foreground, no adjustable wrench or duplicate main tool in the background, commercial ecommerce photography",
      "usage_context": "The product appears as the main repair tool near fasteners on a workbench.",
      "target_width_ratio": 0.68,
      "center_x_ratio": 0.58,
      "center_y_ratio": 0.62,
      "rotation_degrees": -12,
      "depth_layer": "foreground",
      "visual_role": "primary",
      "shadow_strength": "medium",
      "preserve_level": "pixel"
    }}
  ]
}}
        """.strip()

        response = self.client.responses.create(
            model=self.planner_model,
            input=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt},
                        {"type": "input_image", "image_url": image_url},
                    ],
                }
            ],
        )

        data = extract_json(response.output_text)
        return MultiScenePlan(**data)

    @staticmethod
    def fallback_tool_plan(scene_count: int = 4) -> MultiScenePlan:
        """Fallback plan when LLM JSON planning fails."""
        product = ProductAnalysis(
            product_name="tool product",
            category="tool",
            preserve_level="pixel",
            key_structure_points=["tool outline", "functional head", "handle", "visible holes or adjustment parts"],
            risk_points=["tool may be transformed into another tool", "functional head may change"],
        )
        scenes: List[ScenePlan] = [
            ScenePlan(
                name="workbench_repair_scene",
                scene_prompt="A realistic wooden workbench repair scene with bolts, nuts, wood pieces, warm workshop lighting, an empty area reserved for the main product in the foreground, no duplicate hero tool, ecommerce photography",
                usage_context="The tool appears as the main repair tool on a workbench.",
                target_width_ratio=0.68,
                center_x_ratio=0.58,
                center_y_ratio=0.63,
                rotation_degrees=-12,
                depth_layer="foreground",
                visual_role="primary",
                shadow_strength="medium",
                preserve_level="pixel",
            ),
            ScenePlan(
                name="plumbing_repair_scene",
                scene_prompt="A realistic plumbing repair scene near metal pipes and fittings, clean workshop or utility room surface, an empty space reserved for placing the main product, no duplicate hero tool, commercial lighting",
                usage_context="The tool is placed near pipe fittings as if ready for tightening.",
                target_width_ratio=0.55,
                center_x_ratio=0.42,
                center_y_ratio=0.66,
                rotation_degrees=10,
                depth_layer="foreground",
                visual_role="primary",
                shadow_strength="medium",
                preserve_level="pixel",
            ),
            ScenePlan(
                name="garage_automotive_scene",
                scene_prompt="A realistic automotive garage repair scene with engine parts, metal surface, subtle oil-free clean commercial styling, an empty foreground area for the main product, no duplicate hero tool",
                usage_context="The tool appears on a garage work surface near automotive parts.",
                target_width_ratio=0.48,
                center_x_ratio=0.68,
                center_y_ratio=0.58,
                rotation_degrees=-8,
                depth_layer="midground",
                visual_role="primary",
                shadow_strength="strong",
                preserve_level="pixel",
            ),
            ScenePlan(
                name="bicycle_repair_scene",
                scene_prompt="A realistic bicycle maintenance scene near a bike wheel axle and small fasteners, clean home garage background, an empty area reserved for placing the main product, no duplicate hero tool, ecommerce photography",
                usage_context="The tool is placed near a bicycle repair area.",
                target_width_ratio=0.52,
                center_x_ratio=0.50,
                center_y_ratio=0.70,
                rotation_degrees=15,
                depth_layer="foreground",
                visual_role="primary",
                shadow_strength="soft",
                preserve_level="pixel",
            ),
        ]
        return MultiScenePlan(product=product, scenes=scenes[:scene_count])
