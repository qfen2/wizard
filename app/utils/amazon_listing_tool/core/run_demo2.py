from image_graph_tool import LangGraphImageTool
# 基于已有图片进行编辑
tool = LangGraphImageTool()

result = tool.edit_one(
    image_path="source_product.png",
    prompt="""
请保留原图商品主体的外观、颜色、材质和形状，
将图片改造成现代厨房使用场景图。
背景为北欧风厨房台面，自然光，干净高级，
整体具有商业摄影质感，适合电商详情页。
不要文字、水印、二维码或 logo。
    """.strip(),
)

print(result)