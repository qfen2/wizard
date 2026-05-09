from image_graph_tool_v1 import LangGraphImageTool
# 图片分析
tool = LangGraphImageTool()

analysis = tool.analyze_one(
    image_path="source_product.png",
    question="""
请分析这张商品图：
1. 主体是什么
2. 适合做哪些电商图片
3. 当前图片有哪些问题
4. 如果要生成广告图，prompt 应该怎么写
    """.strip(),
)

print(analysis)