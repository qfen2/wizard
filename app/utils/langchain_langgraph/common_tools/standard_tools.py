import csv
from pathlib import Path

from langchain_core.tools import tool
import os
from dataclasses import dataclass
from typing import TypedDict, List, Callable

from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from langgraph.graph.message import REMOVE_ALL_MESSAGES
from pydantic import BaseModel, Field
from typing import Literal
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage, SystemMessage, ToolMessage, RemoveMessage
from langchain_openai import ChatOpenAI
from langchain.tools import tool, ToolRuntime
from langgraph.types import Command

USER_DATABASE = {
    "user123": {
        "name": "Alice Johnson",
        "account_type": "Premium",
        "balance": 5000,
        "email": "alice@example.com"
    },
    "user456": {
        "name": "Bob Smith",
        "account_type": "Standard",
        "balance": 1200,
        "email": "bob@example.com"
    }
}

# definition
class WeatherInput(BaseModel):
    """Input for weather queries."""
    location: str = Field(description="City name or coordinates")
    units: Literal["celsius", "fahrenheit"] = Field(
        default="celsius",
        description="Temperature unit preference"
    )
    include_forecast: bool = Field(
        default=False,
        description="Include 5-day forecast"
    )

@dataclass
class UserContext:
    user_id: str

@tool
def search_database(query: str, limit: int = 10) -> str:
    """Search the customer database for records matching the query.

    Args:
        query: Search terms to look for
        limit: Maximum number of results to return
    """
    return f"Found {limit} results for '{query}'"

@tool("web_search")  # Custom name
def search(query: str) -> str:
    """Search the web for information."""
    return f"Results for: {query}"


@tool("calculator", description="Performs arithmetic calculations. Use this for any math problems.")
def calc(expression: str) -> str:
    """Evaluate mathematical expressions."""
    return str(eval(expression))


@tool(args_schema=WeatherInput)
def get_weather(location: str, units: str = "celsius", include_forecast: bool = False) -> str:
    """Get current weather and optional forecast."""
    temp = 22 if units == "celsius" else 72
    result = f"Current weather in {location}: {temp} degrees {units[0].upper()}"
    if include_forecast:
        result += "\nNext 5 days: Sunny"
    return result

# Access the current conversation state
@tool
def summarize_conversation(
    runtime: ToolRuntime
) -> str:
    """Summarize the conversation so far."""
    messages = runtime.state["messages"]

    human_msgs = sum(1 for m in messages if m.__class__.__name__ == "HumanMessage")
    ai_msgs = sum(1 for m in messages if m.__class__.__name__ == "AIMessage")
    tool_msgs = sum(1 for m in messages if m.__class__.__name__ == "ToolMessage")

    return f"Conversation has {human_msgs} user messages, {ai_msgs} AI responses, and {tool_msgs} tool results"

# Access custom state fields
@tool
def get_user_preference(
    pref_name: str,
    runtime: ToolRuntime  # ToolRuntime parameter is not visible to the model
) -> str:
    """Get a user preference value."""
    preferences = runtime.state.get("user_preferences", {})
    return preferences.get(pref_name, "Not set")

# Update the conversation history by removing all messages
@tool
def clear_conversation() -> Command:
    """Clear the conversation history."""

    return Command(
        update={
            "messages": [RemoveMessage(id=REMOVE_ALL_MESSAGES)],
        }
    )

# Update the user_name in the agent state
@tool
def update_user_name(
    new_name: str,
    runtime: ToolRuntime
) -> Command:
    """Update the user's name."""
    return Command(update={"user_name": new_name})

@tool
def get_account_info(runtime: ToolRuntime[UserContext]) -> str:
    """Get the current user's account information."""
    user_id = runtime.context.user_id

    if user_id in USER_DATABASE:
        user = USER_DATABASE[user_id]
        return f"Account holder: {user['name']}\nType: {user['account_type']}\nBalance: ${user['balance']}"
    return "User not found"

@tool
def search(query: str):
    """在网上搜索信息。"""
    return f"搜索结果：关于 {query} 的信息..."

@tool(description='Send Email')
def send_email():
    """Send an email"""
    # 如果这个函数被执行了，说明拦截失败了或者你已经点击了批准
    # print(f"\n--- 🚀 正在发送邮件到 {recipient} ---")
    print("内容: {content}\n")
    return "邮件发送成功！"

@tool
def delete_database(db_name: str):
    """删除指定的数据库。"""
    print(f"\n--- ⚠️ 数据库 {db_name} 已删除！ ---")
    return "数据库删除成功。"


# 配置文件存放的根目录（防止路径穿越攻击，只允许读取该目录下的文件）
SAFE_BASE_DIR = os.path.abspath("./user_uploads")
from pypdf import PdfReader

@tool
def read_file_content(file_name: str, runtime: ToolRuntime) -> str:
    """
    直接从本地存储中读取指定文件的详细内容。
    支持的格式包括：.csv (表格数据), .pdf (文档), .txt/.md (文本)。

    参数:
    - file_name: 文件名（必须包含后缀，如 'budget.xlsx'，'manual.txt'）
    """
    # 1. 构建安全路径，防止恶意用户读取系统文件
    file_path = os.path.abspath(os.path.join(SAFE_BASE_DIR, file_name))
    if not file_path.startswith(SAFE_BASE_DIR):
        return f"错误：权限拒绝。无法访问目录外的文件。"

    if not os.path.exists(file_path):
        return f"错误：文件 '{file_name}' 不存在。请检查文件名是否正确。"

    # 2. 根据后缀名采取不同的读取策略
    suffix = Path(file_path).suffix.lower()

    try:
        # --- 处理 CSV 文件 ---
        if suffix == ".csv":
            content = []
            with open(file_path, mode='r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                for row in reader:
                    content.append(",".join(row))
            return f"--- CSV 文件 {file_name} 的内容 ---\n" + "\n".join(content)

        # --- 处理 PDF 文件 ---
        elif suffix == ".pdf":
            reader = PdfReader(file_path)
            text = ""
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text += f"\n[第 {i + 1} 页]\n{page_text}"
            return f"--- PDF 文件 {file_name} 的解析内容 ---\n{text}"

        # --- 处理 纯文本 文件 (txt, md, json) ---
        elif suffix in [".txt", ".md", ".json", ".log"]:
            with open(file_path, mode='r', encoding='utf-8') as f:
                text = f.read()
            return f"--- 文本文件 {file_name} 的内容 ---\n{text}"

        else:
            return f"错误：目前不支持读取 {suffix} 格式的文件。"

    except Exception as e:
        return f"读取文件 '{file_name}' 时发生错误: {str(e)}"