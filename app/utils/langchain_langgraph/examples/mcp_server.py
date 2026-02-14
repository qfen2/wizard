# 文件名: server.py
from fastmcp import FastMCP

# 定义一个名为 "BusinessIntel" 的服务器
mcp = FastMCP("BusinessIntel")

# 模拟一些内部数据
INTERNAL_DATA = {
    "mission.txt": "我们的目标是在2026年占据 AI Agent 市场的 30% 份额。",
    "revenue_2025.csv": "Month,Revenue\nJan,100k\nFeb,150k\nMar,300k",
    "secret_sauce.md": "# 核心算法\n利用 MCP 协议打通所有 SaaS 数据孤岛。"
}

# 1. 定义资源：让外部可以通过 URI 访问这些数据
# 这里的 "memo://{filename}" 是我们自定义的资源 URI 格式
@mcp.resource("memo://{filename}")
def get_company_memo(filename: str) -> str:
    """获取公司内部备忘录或数据文件"""
    content = INTERNAL_DATA.get(filename)
    if content:
        return content
    raise ValueError(f"文件 {filename} 不存在")

if __name__ == "__main__":
    # 使用 stdio 模式运行，这是最简单的本地通信方式
    mcp.run(transport="stdio")