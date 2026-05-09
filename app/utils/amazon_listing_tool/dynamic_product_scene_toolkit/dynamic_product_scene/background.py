# -*- coding: utf-8 -*-
"""Background generation module."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any, Dict

from openai import OpenAI

from .utils import ensure_dir, save_b64_image


class BackgroundGenerator:
    """Generate scene backgrounds without drawing the hero product."""

    def __init__(self, client: OpenAI, image_model: str = "gpt-image-2"):
        self.client = client
        self.image_model = image_model

    def generate(
        self,
        scene: Dict[str, Any],
        output_dir: str,
        size: str = "1024x1024",
        quality: str = "high",
    ) -> Dict[str, Any]:
        out_dir = ensure_dir(output_dir)
        scene_name = scene.get("name", "scene")
        bg_path = str(out_dir / f"bg_{scene_name}_{uuid.uuid4().hex}.png")

        layout_hint = (
            f"Reserve a natural open placement area around normalized center "
            f"({scene.get('center_x_ratio')}, {scene.get('center_y_ratio')}) "
            f"with approximate product width ratio {scene.get('target_width_ratio')}."
        )

        prompt = f"""
Create a realistic commercial product usage-scene background.

Scene requirement:
{scene.get('scene_prompt', '')}

Layout hint:
{layout_hint}

Important rules:
- Do NOT generate the main product itself.
- Do NOT generate an adjustable wrench, duplicate same product, or similar hero tool in the reserved area.
- Background can include contextual objects such as bolts, pipes, wood, workshop benches, bicycle parts, garage elements, or industrial surfaces, if appropriate.
- Leave a believable empty area where the actual product foreground will be composited later.
- Make lighting, surface, and perspective realistic for ecommerce photography.
- No text, no watermark, no logo.
        """.strip()

        res = self.client.images.generate(
            model=self.image_model,
            prompt=prompt,
            size=size,
            quality=quality,
            n=1,
        )
        save_b64_image(res.data[0].b64_json, bg_path)

        return {
            "scene_name": scene_name,
            "background_path": bg_path,
            "prompt": prompt,
        }
