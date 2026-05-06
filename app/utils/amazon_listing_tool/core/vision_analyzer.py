from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

class VisualBrain:
    """负责解析竞品风格并提取融合提示词"""
    def __init__(self, api_key: str):
        self.llm = ChatOpenAI(model="gpt-4o", api_key=api_key) # type: ignore

    def extract_scene_prompt(self, competitor_img_url: str) -> str:
        msg = HumanMessage(content=[
            {"type": "text", "text": "分析图中场景，提取背景描述、灯光、材质。输出为英文提示词，用于AI生图背景融合。"},
            {"type": "image_url", "image_url": {"url": competitor_img_url}}
        ])
        return self.llm.invoke([msg]).content