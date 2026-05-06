import os
import sys
from dotenv import load_dotenv

# 导入自定义模块
from core.schemas import WorkflowStateSchema
from core.engine_adapter_v1 import ComfyClient
from core.vision_analyzer import VisualBrain
from core.fusion_pipeline import LinkFoxReplicator

# 加载环境变量 (建议在 .env 文件中存储 API Keys)
load_dotenv()


def main():
    # 1. 基础配置管理
    CONFIG = {
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", "sk-xxxx"),
        "COMFY_SERVER_URL": os.getenv("COMFY_SERVER_URL", "http://127.0.0.1:8188"),
        "WORKFLOW_JSON_PATH": "./assets/fusion_workflow_v1.json"
    }

    # 2. 检查基础环境
    if not os.path.exists(CONFIG["WORKFLOW_JSON_PATH"]):
        print(f"❌ 错误: 找不到 ComfyUI 工作流配置文件: {CONFIG['WORKFLOW_JSON_PATH']}")
        sys.exit(1)

    print("🚀 正在初始化 FoxFusion-AI 引擎...")

    # 3. 模块实例化
    # 初始化手脚（适配器）、大脑（分析器）
    engine_adapter = ComfyClient(host=CONFIG["COMFY_SERVER_URL"])
    vision_analyzer = VisualBrain(api_key=CONFIG["OPENAI_API_KEY"])

    # 4. 构建业务流水线 (Pipeline)
    pipeline_orchestrator = LinkFoxReplicator(
        engine_adapter=engine_adapter,
        vision_analyzer=vision_analyzer,
        workflow_json_path=CONFIG["WORKFLOW_JSON_PATH"]
    )

    # 编译 LangGraph 实例
    fox_fusion_app = pipeline_orchestrator.build_graph()

    # 5. 准备测试输入数据
    # 请确保这两个文件路径是真实的
    test_input: WorkflowStateSchema = {
        "product_image_path": "./data/raw_product_1688.jpg",
        "competitor_ref_path": "https://example.com/competitor_ad_style.jpg",
        "uploaded_product_name": None,
        "scene_prompt": None,
        "comfy_prompt_id": None,
        "final_image_url": None,
        "status": "Starting Pipeline",
        "error": None
    }

    print(f"📸 正在处理商品: {test_input['product_image_path']}")
    print(f"🎨 参考风格图: {test_input['competitor_ref_path']}")

    # 6. 执行工作流
    try:
        final_state = fox_fusion_app.invoke(test_input)

        # 7. 处理最终输出
        if final_state.get("error"):
            print(f"❌ 工作流执行失败: {final_state['error']}")
        else:
            print("\n" + "=" * 30)
            print("✨ 任务成功完成！")
            print(f"🔗 生成的场景图下载地址: {final_state['final_image_url']}")
            print(f"📝 AI 生成的关键词: {final_state['scene_prompt']}")
            print("=" * 30)

    except Exception as e:
        print(f"💥 运行过程中发生未预期的崩溃: {str(e)}")


if __name__ == "__main__":
    main()