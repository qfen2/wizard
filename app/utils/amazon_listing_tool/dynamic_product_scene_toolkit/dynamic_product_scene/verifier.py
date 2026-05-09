# -*- coding: utf-8 -*-
"""Optional visual consistency verifier."""

from __future__ import annotations

from typing import Any, Dict

from openai import OpenAI

from .utils import extract_json, image_to_data_url


class ProductConsistencyVerifier:
    """Compare original product with final scene product for structural consistency."""

    def __init__(self, client: OpenAI, planner_model: str = "gpt-4.1"):
        self.client = client
        self.planner_model = planner_model

    def verify(self, original_image_path: str, final_image_path: str) -> Dict[str, Any]:
        prompt = """
Compare the product in the original image with the product composited in the final scene image.
Focus on tool/hardware structural consistency: jaw shape, holes, handles, metal outline, visible parts, and whether it became a different tool.
Return strict JSON only:
{
  "is_same_product": true,
  "structure_score": 0.0,
  "issues": ["..."]
}
Use structure_score from 0 to 1, where 1 means the product structure is highly consistent.
        """.strip()

        response = self.client.responses.create(
            model=self.planner_model,
            input=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt},
                        {"type": "input_image", "image_url": image_to_data_url(original_image_path)},
                        {"type": "input_image", "image_url": image_to_data_url(final_image_path)},
                    ],
                }
            ],
        )
        try:
            return extract_json(response.output_text)
        except Exception:
            return {"raw": response.output_text}
