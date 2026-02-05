"""
AI 大模型提示词工程工具模块。

设计目标：
- 统一构建发送给大模型的消息结构（如 ChatCompletion 的 messages）
- 通过模板和上下文渲染提示词，方便在不同业务中复用
- 提供一些常见场景（助手对话、代码评审、摘要、结构化抽取等）的基础模板

本模块不依赖具体厂商的 SDK，只负责生成「提示词与消息结构」，
上层可以在调用 openai / deepseek / 其他 LLM SDK 时直接使用。
"""

from __future__ import annotations

import os
import os.path as osp
from pathlib import Path

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

import requests
import yaml


# -----------------------------
# 基础数据结构
# -----------------------------


@dataclass
class PromptMessage:
    """
    表示一条对话消息，兼容大多数 Chat API 的入参结构。

    示例：
        PromptMessage(role="system", content="你是一名专业的 Python 后端工程师")
    """

    role: str
    content: str
    name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {"role": self.role, "content": self.content}
        if self.name:
            data["name"] = self.name
        return data


class PromptTemplate(object):
    """
    最简单的提示词模板类，基于 str.format 做占位符替换。

    示例：
        tpl = PromptTemplate(
            "请用{lang}解释下面的代码，突出关键点：\\n\\n{code}"
        )
        content = tpl.render({"lang": "中文", "code": "print('hello')"})
    """

    def __init__(self, template: str, name: Optional[str] = None) -> None:
        self.template = template
        self.name = name or ""

    def render(self, context: Dict[str, Any]) -> str:
        """
        使用上下文字典渲染提示词。

        - 缺少的 key 会原样保留占位符并抛出异常，方便在开发阶段尽早发现问题。
        """
        try:
            return self.template.format(**context)
        except KeyError as exc:
            missing = str(exc)
            raise KeyError(
                'Prompt template "{}" 缺少必须的占位符变量: {}'.format(
                    self.name or "<unnamed>", missing
                )
            )


def messages_to_dicts(messages: Iterable[PromptMessage]) -> List[Dict[str, Any]]:
    """
    将内部的 PromptMessage 列表转换为字典列表，便于直接传给 SDK。
    """
    return [m.to_dict() for m in messages]


# -----------------------------
# 构建通用消息的工具函数
# -----------------------------


def build_system_message(content: str) -> PromptMessage:
    """构建 system 消息。"""
    return PromptMessage(role="system", content=content)


def build_user_message(content: str) -> PromptMessage:
    """构建 user 消息。"""
    return PromptMessage(role="user", content=content)


def build_assistant_message(content: str) -> PromptMessage:
    """构建 assistant 消息（一般用于补充上下文历史）。"""
    return PromptMessage(role="assistant", content=content)


def build_conversation(
        system_prompt: str,
        user_prompt: str,
        history: Optional[Iterable[PromptMessage]] = None,
        max_history: int = 10,
) -> List[PromptMessage]:
    """
    按常见顺序构建一轮对话的完整消息列表。

    顺序约定为：
        [system] + 最近若干轮历史消息 + 当前 user

    - system_prompt: 当前会话的角色/风格设定
    - user_prompt: 当前用户问题
    - history: 之前轮次的 PromptMessage 列表（可包含 user/assistant）
    - max_history: 最多保留多少条历史消息（从尾部开始截取）
    """
    msgs: List[PromptMessage] = [build_system_message(system_prompt)]

    if history:
        history_list = list(history)
        if max_history > 0 and len(history_list) > max_history:
            history_list = history_list[-max_history:]
        msgs.extend(history_list)

    msgs.append(build_user_message(user_prompt))
    return msgs


# -----------------------------
# 常用场景模板
# -----------------------------


# 通用助手角色设定
DEFAULT_ASSISTANT_SYSTEM = (
    "你是一名专业、严谨且耐心的 AI 助手，擅长用清晰易懂的中文回答问题。"
    "在涉及代码时，请给出结构化的回答，并尽量提供可直接运行的示例。"
)

assistant_chat_template = PromptTemplate(
    template=(
        "下面是用户的问题，请你以专业中文给出详细、分步骤的解答，如果涉及代码请给出示例：\\n"
        "【用户问题】:\\n{query}"
    ),
    name="assistant_chat_template",
)

code_review_template = PromptTemplate(
    template=(
        "你是一名资深代码审查工程师，请从可读性、健壮性、性能、安全性等方面审查下面的代码。\\n"
        "请给出：\\n"
        "1. 总体评价\\n"
        "2. 发现的问题（按重要程度排序）\\n"
        "3. 可以改进的建议和参考实现思路\\n"
        "\\n"
        "【语言】:{lang}\\n"
        "【代码】:\\n{code}"
    ),
    name="code_review_template",
)

summarize_template = PromptTemplate(
    template=(
        "请用{lang}为下面的内容生成一个结构化摘要，要求：\\n"
        "- 先给出 1 句话的整体结论\\n"
        "- 然后分点列出 3~7 条关键信息\\n"
        "- 最后给出可能的后续行动建议（如果合适）\\n"
        "\\n"
        "【原文内容】:\\n{content}"
    ),
    name="summarize_template",
)

structured_extract_template = PromptTemplate(
    template=(
        "请从下面的文本中提取结构化信息，并使用 JSON 格式输出（只输出 JSON，不要多余说明）。\\n"
        "字段说明：\\n"
        "{schema_desc}\\n"
        "\\n"
        "【文本】:\\n{content}"
    ),
    name="structured_extract_template",
)


# -----------------------------
# 对外常用高层封装
# -----------------------------


def build_assistant_chat_messages(
        user_query: str,
        system_prompt: str = DEFAULT_ASSISTANT_SYSTEM,
        history: Optional[Iterable[PromptMessage]] = None,
) -> List[Dict[str, Any]]:
    """
    构建一个「通用助手对话」所需的 messages。

    - system_prompt: 可以自定义角色设定；不传则使用默认设定
    - user_query: 当前用户输入
    - history: 历史对话（可选）
    """
    rendered = assistant_chat_template.render({"query": user_query})
    msgs = build_conversation(
        system_prompt=system_prompt,
        user_prompt=rendered,
        history=history,
    )
    return messages_to_dicts(msgs)


def build_code_review_messages(
        code: str,
        lang: str = "中文",
        system_prompt: str = (
                "你是一名有 10 年经验的资深代码审查工程师，熟悉后端、Web 与数据库开发。"
        ),
) -> List[Dict[str, Any]]:
    """
    构建一轮代码审查所需的 messages。
    """
    rendered = code_review_template.render({"code": code, "lang": lang})
    msgs = [
        build_system_message(system_prompt),
        build_user_message(rendered),
    ]
    return messages_to_dicts(msgs)


def build_summarize_messages(
        content: str,
        lang: str = "中文",
        system_prompt: str = (
                "你是一名擅长信息归纳与总结的助手，输出内容要求简洁、结构清晰。"
        ),
) -> List[Dict[str, Any]]:
    """构建摘要类任务的 messages。"""
    rendered = summarize_template.render({"content": content, "lang": lang})
    msgs = [
        build_system_message(system_prompt),
        build_user_message(rendered),
    ]
    return messages_to_dicts(msgs)


def build_structured_extract_messages(
        content: str,
        schema_desc: str,
        system_prompt: str = (
                "你是一名信息抽取助手，需要严格按照要求从文本中提取字段并输出 JSON。"
        ),
) -> List[Dict[str, Any]]:
    """
    构建结构化抽取任务的 messages。
    """
    rendered = structured_extract_template.render(
        {"content": content, "schema_desc": schema_desc}
    )
    msgs = [
        build_system_message(system_prompt),
        build_user_message(rendered),
    ]
    return messages_to_dicts(msgs)


# -----------------------------
# DeepSeek API 封装
# -----------------------------


def _load_config_from_yaml() -> Dict[str, Any]:
    """
    从 conf/auto.yaml 读取配置。
    
    返回配置字典，如果文件不存在或读取失败则返回空字典。
    """
    config_file = Path(osp.join(osp.dirname(osp.dirname(osp.dirname(osp.abspath(__file__)))), "conf", "auto.yaml"))
    if not config_file.exists():
        return {}
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


def _get_deepseek_api_key() -> str:
    """
    获取 DeepSeek API Key，优先级：
    1. conf/auto.yaml 中的 deepseek_api_key 或 DEEPSEEK_API_KEY
    2. 环境变量 DEEPSEEK_API_KEY
    """
    # 先从配置文件读取
    config = _load_config_from_yaml()
    api_key = (
        config.get("llm", {}).get("deepseek").get("api_key")
        if isinstance(config.get("llm"), dict)
        else None
    )
    if api_key:
        return str(api_key)
    
    # 回退到环境变量
    return os.getenv("DEEPSEEK_API_KEY", "")


# DeepSeek API 配置
DEEPSEEK_API_KEY = _get_deepseek_api_key()
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"


def call_deepseek_chat(
        messages: List[Dict[str, Any]],
        model: str = "deepseek-chat",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
) -> Dict[str, Any]:
    """
    使用 DeepSeek Chat Completion 接口进行一次完整对话请求。

    参数：
    - messages: 已经是 dict 结构的消息列表（一般由 build_*_messages 生成）
    - model: 模型名称，默认 deepseek-chat
    - temperature: 采样温度
    - max_tokens: 可选，限制生成长度
    """
    if not DEEPSEEK_API_KEY:
        raise RuntimeError(
            "DEEPSEEK_API_KEY 未配置，请在 conf/auto.yaml 中设置 deepseek_api_key，"
            "或在环境变量中设置 DEEPSEEK_API_KEY。"
        )

    payload: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
    }

    resp = requests.post(DEEPSEEK_API_URL, json=payload, headers=headers, timeout=60)
    resp.raise_for_status()
    return resp.json()


def call_deepseek_simple_answer(user_query: str) -> str:
    """
    直接用 DeepSeek + 通用助手提示词，返回一段纯文本回答。
    """
    messages = build_assistant_chat_messages(user_query)
    data = call_deepseek_chat(messages)
    try:
        return data["choices"][0]["message"]["content"]
    except Exception:
        # 保底返回原始数据字符串，方便排查
        return str(data)


__all__ = [
    "PromptMessage",
    "PromptTemplate",
    "build_system_message",
    "build_user_message",
    "build_assistant_message",
    "messages_to_dicts",
    "build_conversation",
    "DEFAULT_ASSISTANT_SYSTEM",
    "assistant_chat_template",
    "code_review_template",
    "summarize_template",
    "structured_extract_template",
    "build_assistant_chat_messages",
    "build_code_review_messages",
    "build_summarize_messages",
    "build_structured_extract_messages",
    "DEEPSEEK_API_URL",
    "call_deepseek_chat",
    "call_deepseek_simple_answer",
]

if __name__ == "__main__":
    # 简单命令行测试：直接调用 DeepSeek 获取回答
    question = input("请输入要问 DeepSeek 的问题：")
    answer = call_deepseek_simple_answer(question)
    print("\nDeepSeek 回答：\n")
    print(answer)
