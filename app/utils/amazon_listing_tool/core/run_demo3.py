from image_graph_tool import LangGraphImageTool
# 让 LangGraph 自动规划一组商品图
tool = LangGraphImageTool()

state = tool.invoke(
    user_request="""
给便携式宠物饮水瓶生成一组跨境电商图片，
包括 Amazon 主图、户外生活方式图、产品细节图、社媒广告图。
整体风格真实、明亮、干净，适合广告投放。
    """.strip(),
    size="1024x1024",
    quality="high",
)

print("intent:", state.get("intent"))
print("tasks:", state.get("tasks"))
print("summary:", state.get("summary"))

for item in state.get("results", []):
    print(item.get("task_name"), item.get("image_path"), item.get("success"))