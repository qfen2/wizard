from image_graph_tool_v1 import LangGraphImageTool
# 直接文生图
tool = LangGraphImageTool()

result = tool.generate_one(
    prompt="""
生成一张高端电商商品图：
产品是一只黑色不锈钢保温杯，
纯白背景，专业棚拍光线，柔和阴影，
构图简洁，材质清晰，高级感强，
不要文字，不要 logo，不要水印。
    """.strip(),
    size="1024x1024",
    quality="high",
)

print(result)