# coding: utf-8
"""
LangChain 和 LangGraph 复杂案例实现

本模块包含使用最新版本的 LangChain 和 LangGraph 实现的复杂多智能体协作系统。
"""

from .research_assistant import ResearchAssistant, ResearchState

__all__ = [
    "ResearchAssistant",
    "ResearchState",
]
