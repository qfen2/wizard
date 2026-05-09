# Dynamic Product Scene Tool

把 `dynamic_product_scene/` 文件夹拷贝到你的现有项目中即可使用。

## 依赖

```bash
pip install -U openai langgraph langchain-core pydantic pillow rembg
```

## 调用示例

```python
from dynamic_product_scene import DynamicProductSceneTool

scene_tool = DynamicProductSceneTool(
    planner_model="gpt-4.1",
    image_model="gpt-image-2",
    output_dir="generated_images",
    temp_dir="temp_product_assets",
)

state = scene_tool.generate_usage_scenes(
    image_path="wrench.png",
    user_request=(
        "基于这张扳手商品原图，生成4张不同使用场景图。"
        "适合电商详情页和广告展示。扳手可以根据不同场景自然变大、变小、改变位置、轻微旋转，"
        "但扳手结构必须尽量保持原图一致，不要变成其他工具。"
    ),
    scene_count=4,
    size="1024x1024",
    quality="high",
    enable_verify=False,
)

print(state["summary"])
for item in state.get("results", []):
    print(item.get("scene_name"), item.get("image_path"), item.get("layout"))
```

## 说明

- `DynamicProductSceneTool` 是对外工具入口。
- `DynamicProductSceneGraph` 是内部 LangGraph 工作流实现。
- 用户不需要手动传缩放、位置、旋转参数；这些由 LLM 在 `planner.py` 中动态规划。
- `compositor.py` 只负责执行 LLM 的规划结果，避免让图片模型直接重绘工具/五金主体导致变形。
