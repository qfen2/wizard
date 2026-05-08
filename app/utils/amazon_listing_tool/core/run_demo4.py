from image_graph_tool import LangGraphImageTool
# 基于已有商品图做多需求改造
tool = LangGraphImageTool()

state = tool.invoke(
    user_request="""
基于这张商品图，帮我做 4 个版本：
1. Amazon 白底主图
2. 家居生活方式场景图
3. 高级广告图
4. 圣诞促销氛围图

要求保留商品主体的外观和材质，提升商业摄影质感。
    """.strip(),
    image_path="source_product.png",
    size="1024x1024",
    quality="high",
)

for item in state["results"]:
    print(item)