# -*- coding: utf-8 -*-
"""Product foreground composition module."""

from __future__ import annotations

from typing import Any, Dict

from PIL import Image, ImageFilter

from .utils import (
    RESAMPLE_BICUBIC,
    RESAMPLE_LANCZOS,
    clamp_float,
    light_finish,
    trim_transparent_padding,
)


class ProductCompositor:
    """
    Compose segmented product foreground into generated backgrounds.

    商品缩放 / 移动 / 轻微旋转来自 LLM 规划结果；程序只负责精确执行。
    """

    def compose(
        self,
        background_path: str,
        foreground_path: str,
        scene: Dict[str, Any],
        output_path: str,
    ) -> str:
        bg = Image.open(background_path).convert("RGBA")
        fg = Image.open(foreground_path).convert("RGBA")
        fg = trim_transparent_padding(fg)

        bg_w, bg_h = bg.size
        fg_w, fg_h = fg.size

        target_width_ratio = clamp_float(scene.get("target_width_ratio"), 0.20, 0.90, 0.65)
        target_w = max(1, int(bg_w * target_width_ratio))
        scale = target_w / max(fg_w, 1)
        target_h = max(1, int(fg_h * scale))
        fg = fg.resize((target_w, target_h), RESAMPLE_LANCZOS)

        rotation = clamp_float(scene.get("rotation_degrees"), -35, 35, 0)
        fg = fg.rotate(rotation, expand=True, resample=RESAMPLE_BICUBIC)

        center_x_ratio = clamp_float(scene.get("center_x_ratio"), 0.0, 1.0, 0.5)
        center_y_ratio = clamp_float(scene.get("center_y_ratio"), 0.0, 1.0, 0.6)
        center_x = int(bg_w * center_x_ratio)
        center_y = int(bg_h * center_y_ratio)

        x = center_x - fg.width // 2
        y = center_y - fg.height // 2

        # Keep at least part of the product inside the frame.
        x = max(-fg.width // 3, min(x, bg_w - fg.width * 2 // 3))
        y = max(-fg.height // 3, min(y, bg_h - fg.height * 2 // 3))

        composed = self._add_shadow(
            canvas=bg,
            product_layer=fg,
            x=x,
            y=y,
            shadow_strength=scene.get("shadow_strength", "medium"),
        )
        composed.paste(fg, (x, y), fg)
        composed = light_finish(composed)
        composed.save(output_path)
        return output_path

    @staticmethod
    def _add_shadow(
        canvas: Image.Image,
        product_layer: Image.Image,
        x: int,
        y: int,
        shadow_strength: str = "medium",
    ) -> Image.Image:
        if shadow_strength == "soft":
            opacity, blur, offset = 65, 18, (8, 10)
        elif shadow_strength == "strong":
            opacity, blur, offset = 130, 26, (16, 20)
        else:
            opacity, blur, offset = 95, 22, (12, 15)

        alpha = product_layer.getchannel("A")
        shadow = Image.new("RGBA", product_layer.size, (0, 0, 0, opacity))
        shadow.putalpha(alpha)
        shadow = shadow.filter(ImageFilter.GaussianBlur(blur))

        shadow_canvas = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        shadow_canvas.paste(shadow, (x + offset[0], y + offset[1]), shadow)
        return Image.alpha_composite(canvas, shadow_canvas)
