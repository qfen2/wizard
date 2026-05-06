from typing import TypedDict, Optional, List

class WorkflowStateSchema(TypedDict):
    """
    定义 FoxFusion 工作流的状态结构
    用于在 LangGraph 的各个节点之间传递数据
    """
    # --- 初始输入 ---
    product_image_path: str       # 本地待处理的1688商品原图路径
    competitor_ref_path: str      # 用于参考风格的竞品图路径 (URL或路径)

    # --- 中间处理数据 ---
    uploaded_product_name: Optional[str]  # 图片上传到 ComfyUI 后的内部文件名
    scene_prompt: Optional[str]           # GPT-4o 生成的场景描述关键词
    comfy_prompt_id: Optional[str]        # ComfyUI 任务队列的任务 ID

    # --- 输出结果 ---
    final_image_url: Optional[str]        # 最终生成的融合场景图地址

    # --- 流程控制 ---
    status: str                           # 当前节点状态描述
    error: Optional[str]                  # 如果发生错误，记录错误信息