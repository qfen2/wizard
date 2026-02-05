import operator
from typing import List, Literal, TypedDict, Annotated, Optional
from pydantic import BaseModel, Field

from langchain_openai import ChatOpenAI
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import BaseMessage
from langchain_core.tools import BaseTool

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver


# ============================================================
# 1. 配置层
# ============================================================

class ResearchAgentConfig(BaseModel):
    """配置类：定义 Agent 的行为边界和依赖"""

    # 核心依赖
    llm: BaseChatModel = Field(description="使用的 LLM 模型实例")
    search_tool: BaseTool = Field(description="使用的搜索工具实例")

    # 运行参数
    max_iterations: int = Field(default=3, description="最大自我迭代次数")
    temperature: float = Field(default=0.0, description="LLM 生成温度")

    # 提示词模板 (允许外部自定义，否则使用默认)
    writer_system_prompt: str = "你是一个专业的研究助理。"
    critic_system_prompt: str = "你是一个严格的编辑。"


# ============================================================
# 2. 内部状态层
# ============================================================

class _InternalState(TypedDict):
    """内部状态图结构，不对外暴露细节"""
    topic: str
    search_query: str
    research_data: str
    draft_content: str
    critique_feedback: str
    iteration_count: int
    messages: Annotated[List[BaseMessage], operator.add]


# ============================================================
# 3. 核心逻辑类
# ============================================================

class AutoResearchAgent:
    """
    自主研究助理 Agent。

    封装了 LangGraph 的构建逻辑，对外提供简单的 run 接口。
    """

    def __init__(self, config: ResearchAgentConfig):
        self.config = config
        self.graph = self._build_graph()
        # 可选：添加 Checkpoint 以支持内存/持久化
        self.memory = MemorySaver()

    def _get_nodes(self):
        """定义图的所有节点"""

        def researcher(state: _InternalState):
            print(f"🔍 [Node: Researcher] 搜索中: {state['search_query']}")
            res = self.config.search_tool.invoke(state["search_query"])
            # 简单的数据清洗
            formatted = "\n".join([f"{r.get('title', '')}: {r.get('content', '')}" for r in res])
            return {"research_data": formatted}

        def writer(state: _InternalState):
            print(f"✍️  [Node: Writer] 撰写中 (第 {state['iteration_count']} 版)...")

            prompt = ChatPromptTemplate.from_messages([
                ("system", self.config.writer_system_prompt),
                ("human", "主题: {topic}\n现有草稿:\n{existing_draft}\n新资料:\n{research_data}\n\n请整合并更新草稿。")
            ])

            chain = prompt | self.config.llm | StrOutputParser()
            response = chain.invoke({
                "topic": state["topic"],
                "existing_draft": state.get("draft_content", "暂无草稿"),
                "research_data": state["research_data"]
            })
            return {"draft_content": response}

        def critic(state: _InternalState):
            print(f"🔍 [Node: Critic] 审查中...")

            prompt = ChatPromptTemplate.from_messages([
                ("system", self.config.critic_system_prompt),
                ("human", "草稿:\n{draft_content}\n\n如果完美，回复 'PASS'。如果不完美，回复 'CONTINUE: <建议的搜索词>'。")
            ])

            chain = prompt | self.config.llm | StrOutputParser()
            feedback = chain.invoke({"draft_content": state["draft_content"]})

            if "PASS" in feedback:
                return {"critique_feedback": "PASS"}

            # 提取新的搜索指令
            new_query = feedback.replace("CONTINUE:", "").strip()
            if not new_query: new_query = state["topic"] + " 更多细节"

            print(f"⚠️  审查意见: 需要补充 '{new_query}'")
            return {
                "critique_feedback": "CONTINUE",
                "search_query": new_query
            }

        return researcher, writer, critic

    def _should_continue(self, state: _InternalState) -> Literal["researcher", END]:
        """边的条件逻辑：决定是循环还是结束"""
        if state.get("critique_feedback") == "PASS":
            print("✅ 审查通过，流程结束。")
            return END

        if state["iteration_count"] >= self.config.max_iterations:
            print(f"🛑 达到最大迭代次数 ({self.config.max_iterations})，强制结束。")
            return END

        return "researcher"

    def _build_graph(self) -> StateGraph:
        """构建 LangGraph 有向图"""
        workflow = StateGraph(_InternalState)

        researcher, writer, critic = self._get_nodes()

        # 添加节点
        workflow.add_node("researcher", researcher)
        workflow.add_node("writer", writer)
        workflow.add_node("critic", critic)

        # 设置入口
        workflow.set_entry_point("researcher")

        # 定义边
        workflow.add_edge("researcher", "writer")
        workflow.add_edge("writer", "critic")

        # 条件边（循环）
        workflow.add_conditional_edges(
            "critic",
            self._should_continue,
            {
                "researcher": "researcher",
                END: END
            }
        )

        # 编译 (带 Checkpoint 支持的话可以用 workflow.compile(checkpointer=self.memory))
        return workflow.compile(checkpointer=self.memory)

    def run(
            self,
            topic: str,
            initial_query: Optional[str] = None,
            thread_id: str = "default_session"
    ) -> str:
        """
        对外暴露的运行接口。

        Args:
            topic: 研究主题
            initial_query: 初始搜索词（可选，默认为 topic）
            thread_id: 会话 ID，用于记忆保存

        Returns:
            str: 最终生成的报告
        """
        if not initial_query:
            initial_query = topic

        config = RunnableConfig(configurable={"thread_id": thread_id})

        initial_state: _InternalState = {
            "topic": topic,
            "search_query": initial_query,
            "research_data": "",
            "draft_content": "",
            "critique_feedback": "",
            "iteration_count": 1,
            "messages": []
        }

        print(f"🚀 开始任务: {topic}")

        # 执行图
        final_state = self.graph.invoke(initial_state, config)

        return final_state.get("draft_content", "生成失败")


# ============================================================
# 4. 使用示例
# ============================================================

if __name__ == "__main__":
    from langchain_community.tools.tavily_search import TavilySearchResults
    import os

    # 1. 准备配置
    # 注意：这里可以轻松替换为其他 LLM (如 Anthropic, Ollama) 或其他 Tool
    config = ResearchAgentConfig(
        llm=ChatOpenAI(model="gpt-4o", temperature=0),
        search_tool=TavilySearchResults(max_results=3),
        max_iterations=3,
        writer_system_prompt="你是一个科技博主，风格要幽默风趣。"
    )

    # 2. 实例化 Agent
    agent = AutoResearchAgent(config)

    # 3. 执行
    report = agent.run(topic="量子计算在 2024 年的突破")

    print("\n" + "=" * 30 + " 最终报告 " + "=" * 30)
    print(report)