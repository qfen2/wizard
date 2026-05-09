# -*- coding: utf-8 -*-
"""Shared utilities for dynamic product scene generation."""

from __future__ import annotations

import base64
import json
import re
from pathlib import Path
from typing import Any, Dict

from PIL import Image, ImageEnhance


# Pillow compatibility:
# Pillow >= 9.1 exposes resampling constants under Image.Resampling.
# Older versions may still expose Image.LANCZOS / Image.BICUBIC directly.
try:  # pragma: no cover - depends on Pillow version
    RESAMPLE_LANCZOS = Image.Resampling.LANCZOS
    RESAMPLE_BICUBIC = Image.Resampling.BICUBIC
except AttributeError:  # pragma: no cover - depends on Pillow version
    RESAMPLE_LANCZOS = getattr(Image, "LANCZOS", Image.BICUBIC)
    RESAMPLE_BICUBIC = getattr(Image, "BICUBIC", Image.BILINEAR)


def ensure_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def clamp_float(value: Any, low: float, high: float, default: float) -> float:
    try:
        v = float(value)
    except Exception:
        v = default
    return max(low, min(v, high))


def extract_json(text: str) -> Dict[str, Any]:
    """Extract a JSON object from plain text or a ```json fenced response."""
    text = (text or "").strip()
    text = re.sub(r"^```(?:json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end >= 0:
        text = text[start : end + 1]
    return json.loads(text)


def image_to_data_url(image_path: str) -> str:
    ext = Path(image_path).suffix.lower().replace(".", "")
    if ext == "jpg":
        ext = "jpeg"
    if ext not in {"png", "jpeg", "webp"}:
        ext = "png"
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    return f"data:image/{ext};base64,{b64}"


def save_b64_image(b64_json: str, output_path: str) -> str:
    Path(output_path).write_bytes(base64.b64decode(b64_json))
    return output_path


def trim_transparent_padding(image: Image.Image) -> Image.Image:
    image = image.convert("RGBA")
    alpha = image.getchannel("A")
    bbox = alpha.getbbox()
    return image.crop(bbox) if bbox else image


def light_finish(image: Image.Image) -> Image.Image:
    """Mild whole-image finishing; changes tonality slightly, not geometry."""
    rgb = image.convert("RGB")
    rgb = ImageEnhance.Contrast(rgb).enhance(1.03)
    rgb = ImageEnhance.Sharpness(rgb).enhance(1.02)
    return rgb.convert("RGBA")
