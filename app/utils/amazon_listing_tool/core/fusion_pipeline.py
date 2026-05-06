import json

from langgraph.graph import StateGraph, END
from typing import TypedDict

from app.utils.amazon_listing_tool.core.engine_adapter_v1 import ComfyClient
from app.utils.amazon_listing_tool.core.vision_analyzer import VisualBrain


class FusionState(TypedDict):
    product_path: str  # 1688原图
    competitor_url: str  # 竞品参考图
    final_prompt: str  # GPT生成的描述
    comfy_img_id: str  # Comfy内部文件名
    output_url: str  # 最终图结果


class LinkFoxReplicator:
    """LINKfox 复刻编排器"""

    def __init__(self, engine_adapter:ComfyClient, vision_analyzer:VisualBrain, workflow_json_path: str):
        self.comfy = engine_adapter
        self.brain = vision_analyzer
        with open(workflow_json_path, "r") as f:
            self.base_workflow = json.load(f)

    def _node_analyze_style(self, state: FusionState):
        """节点 1: 视觉分析"""
        prompt = self.brain.extract_scene_prompt(state['competitor_url'])
        return {"final_prompt": prompt}

    def _node_execute_fusion(self, state: FusionState):
        """节点 2: 像素锁定与 ControlNet 融合生图"""
        # 1. 上传图片
        img_id = self.comfy.upload_image(state['product_path'])

        # 2. 注入动态参数到 Comfy 工作流
        # 注意：这里的 ID ("6", "10") 需与你导出的 ComfyUI API JSON 对应
        wf = self.base_workflow.copy()
        wf["6"]["inputs"]["text"] = state["final_prompt"]  # 提示词
        wf["10"]["inputs"]["image"] = img_id  # 锁定商品像素
        # wf["15"]["inputs"]["image"] = img_id           # ControlNet 边界约束

        # 3. 执行并获取结果
        p_id = self.comfy.run_workflow(wf)
        url = self.comfy.poll_result(p_id)
        return {"output_url": url}

    def build_graph(self):
        """构建图结构"""
        builder = StateGraph(FusionState) # type: ignore
        builder.add_node("analyze", self._node_analyze_style) # type: ignore
        builder.add_node("fusion", self._node_execute_fusion) # type: ignore

        builder.set_entry_point("analyze")
        builder.add_edge("analyze", "fusion")
        builder.add_edge("fusion", END)
        return builder.compile()


# ==========================================
# 运行入口
# ==========================================
if __name__ == "__main__":
    print(f"✅ 生成完成！电商场景融合图位于: `output_url`")