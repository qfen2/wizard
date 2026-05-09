# -*- coding: utf-8 -*-
"""Automatic product segmentation."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Dict

from PIL import Image

try:
    from rembg import remove as rembg_remove
except Exception:  # pragma: no cover - handled at runtime
    rembg_remove = None

from .utils import ensure_dir


class AutoProductSegmenter:
    """
    自动抠图模块。

    输出：
    - foreground_path: 透明背景商品前景图
    - mask_path: 商品 mask，白色=商品，黑色=背景
    """

    def __init__(self, temp_dir: str = "temp_product_assets"):
        self.temp_dir = ensure_dir(temp_dir)

    def segment(self, image_path: str, temp_dir: str | None = None) -> Dict[str, str]:
        if rembg_remove is None:
            raise ImportError("缺少 rembg。请执行：pip install rembg")

        image_file = Path(image_path)
        if not image_file.exists():
            raise FileNotFoundError(f"商品原图不存在：{image_path}")

        out_dir = ensure_dir(temp_dir or self.temp_dir)
        stem = image_file.stem
        foreground_path = str(out_dir / f"{stem}_foreground_{uuid.uuid4().hex}.png")
        mask_path = str(out_dir / f"{stem}_mask_{uuid.uuid4().hex}.png")

        with open(image_file, "rb") as f:
            input_bytes = f.read()

        output_bytes = rembg_remove(input_bytes)

        with open(foreground_path, "wb") as f:
            f.write(output_bytes)

        fg = Image.open(foreground_path).convert("RGBA")
        alpha = fg.getchannel("A")
        mask = alpha.point(lambda p: 255 if p > 10 else 0).convert("L")
        mask.save(mask_path)

        return {
            "foreground_path": foreground_path,
            "mask_path": mask_path,
        }
