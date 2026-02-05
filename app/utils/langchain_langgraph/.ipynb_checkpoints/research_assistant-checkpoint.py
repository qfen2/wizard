# coding: utf-8
"""
多智能体协作研究助手系统

这是一个使用 LangChain 和 LangGraph 实现的复杂案例，展示了：
1. 多智能体协作（搜索、分析、写作、审核）
2. 状态管理和流程控制
3. 工具调用和条件分支
4. 循环和迭代优化
"""

import operator
from typing import Annotated, List, Literal, TypedDict
from datetime import datetime
import config

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode


# ==================== 状态定义 ====================
class ResearchState(TypedDict):
    """研究助手的状态定义"""
    # 消息历史
    messages: Annotated[List, operator.add]
    
    # 研究主题
    research_topic: str
    
    # 搜索到的信息
    search_results: List[str]
    
    # 分析结果
    analysis: str
    
    # 草稿报告
    draft_report: str
    
    # 审核意见
    review_feedback: str
    
    # 最终报告
    final_report: str
    
    # 当前阶段
    current_stage: Literal["search", "analyze", "write", "review", "finalize", "done"]
    
    # 迭代次数
    iteration_count: int
    
    # 最大迭代次数
    max_iterations: int


# ==================== 工具定义 ====================
@tool
def calculate_statistics(text: str) -> str:
    """计算文本的统计信息（字数、段落数等）"""
    words = len(text.split())
    paragraphs = len([p for p in text.split('\n\n') if p.strip()])
    sentences = len([s for s in text.split('.') if s.strip()])
    
    return f"统计信息：字数={words}, 段落数={paragraphs}, 句子数={sentences}"


@tool
def format_markdown(text: str) -> str:
    """将文本格式化为 Markdown 格式"""
    lines = text.split('\n')
    formatted = []
    for line in lines:
        if line.strip():
            if not line.startswith('#'):
                formatted.append(line)
            else:
                formatted.append(line)
        else:
            formatted.append('')
    return '\n'.join(formatted)


# ==================== 节点函数 ====================
def search_node(state: ResearchState) -> ResearchState:
    """搜索节点：使用搜索工具收集信息"""
    print(f"\n[搜索阶段] 正在搜索主题: {state['research_topic']}")
    
    # 初始化搜索工具
    search_tool = TavilySearchResults(max_results=5)
    
    # 执行搜索
    try:
        results = search_tool.invoke({"query": state['research_topic']})
        search_data = []
        for result in results:
            if isinstance(result, dict):
                search_data.append(result.get('content', str(result)))
            else:
                search_data.append(str(result))
        
        state['search_results'] = search_data
        state['messages'].append(
            AIMessage(content=f"已搜索到 {len(search_data)} 条相关信息")
        )
        state['current_stage'] = "analyze"
        print(f"[搜索阶段] 完成，找到 {len(search_data)} 条结果")
    except Exception as e:
        print(f"[搜索阶段] 错误: {e}")
        state['search_results'] = [f"搜索时出现错误: {str(e)}"]
        state['current_stage'] = "analyze"
    
    return state


def analyze_node(state: ResearchState) -> ResearchState:
    """分析节点：分析搜索到的信息"""
    print(f"\n[分析阶段] 正在分析收集到的信息...")
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
    
    # 构建分析提示
    search_content = "\n\n".join(state['search_results'][:3])  # 取前3条结果
    
    prompt = f"""你是一位专业的研究分析师。请分析以下关于"{state['research_topic']}"的信息：

{search_content}

请提供：
1. 关键发现和要点
2. 主要趋势和模式
3. 重要数据和事实
4. 潜在的问题或争议

请用中文回答，保持客观和专业。"""
    
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        analysis = response.content if hasattr(response, 'content') else str(response)
        
        state['analysis'] = analysis
        state['messages'].append(
            AIMessage(content=f"分析完成：{analysis[:100]}...")
        )
        state['current_stage'] = "write"
        print(f"[分析阶段] 完成")
    except Exception as e:
        print(f"[分析阶段] 错误: {e}")
        state['analysis'] = f"分析时出现错误: {str(e)}"
        state['current_stage'] = "write"
    
    return state


def write_node(state: ResearchState) -> ResearchState:
    """写作节点：基于分析结果撰写报告草稿"""
    print(f"\n[写作阶段] 正在撰写报告草稿...")
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
    
    prompt = f"""你是一位专业的研究报告撰写者。请基于以下分析结果，撰写一份关于"{state['research_topic']}"的研究报告。

分析结果：
{state['analysis']}

要求：
1. 报告应包含：引言、主要发现、详细分析、结论
2. 使用清晰的结构和逻辑
3. 引用关键数据和事实
4. 保持专业和客观的语调
5. 报告长度应在500-800字之间

请用中文撰写完整的报告。"""
    
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        draft = response.content if hasattr(response, 'content') else str(response)
        
        state['draft_report'] = draft
        state['messages'].append(
            AIMessage(content=f"草稿已完成，长度: {len(draft)} 字符")
        )
        state['current_stage'] = "review"
        print(f"[写作阶段] 完成，草稿长度: {len(draft)} 字符")
    except Exception as e:
        print(f"[写作阶段] 错误: {e}")
        state['draft_report'] = f"撰写时出现错误: {str(e)}"
        state['current_stage'] = "review"
    
    return state


def review_node(state: ResearchState) -> ResearchState:
    """审核节点：审核报告草稿并提供反馈"""
    print(f"\n[审核阶段] 正在审核报告草稿...")
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.5)
    
    prompt = f"""你是一位严格的报告审核专家。请审核以下关于"{state['research_topic']}"的研究报告草稿：

{state['draft_report']}

请提供详细的审核反馈，包括：
1. 内容准确性评估
2. 结构和逻辑性评价
3. 需要改进的地方
4. 是否达到专业标准

如果报告质量良好（评分8/10以上），请说"通过审核"。
如果需要改进，请提供具体的修改建议。

请用中文回答。"""
    
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        feedback = response.content if hasattr(response, 'content') else str(response)
        
        state['review_feedback'] = feedback
        state['messages'].append(
            AIMessage(content=f"审核完成：{feedback[:100]}...")
        )
        
        # 判断是否需要修改
        if "通过审核" in feedback or "评分" in feedback:
            # 检查评分（简单判断）
            if any(keyword in feedback.lower() for keyword in ["8", "9", "10", "优秀", "很好", "通过"]):
                state['current_stage'] = "finalize"
            else:
                state['current_stage'] = "write"  # 需要重新写作
                state['iteration_count'] += 1
        else:
            state['current_stage'] = "write"
            state['iteration_count'] += 1
        
        print(f"[审核阶段] 完成，反馈: {feedback[:50]}...")
    except Exception as e:
        print(f"[审核阶段] 错误: {e}")
        state['review_feedback'] = f"审核时出现错误: {str(e)}"
        state['current_stage'] = "finalize"
    
    return state


def finalize_node(state: ResearchState) -> ResearchState:
    """最终化节点：生成最终报告"""
    print(f"\n[最终化阶段] 正在生成最终报告...")
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
    
    prompt = f"""请基于以下内容，生成一份完整、专业的最终研究报告：

    主题：{state['research_topic']}
    
    草稿报告：
    {state['draft_report']}
    
    审核反馈：
    {state['review_feedback']}
    
    请整合所有信息，生成一份格式规范、内容完整的最终研究报告。
    报告应包含：
    - 标题
    - 摘要
    - 引言
    - 主要发现
    - 详细分析
    - 结论
    - 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    
    请用中文撰写，使用 Markdown 格式。"""
    
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        final_report = response.content if hasattr(response, 'content') else str(response)
        
        state['final_report'] = final_report
        state['messages'].append(
            AIMessage(content="最终报告已生成完成")
        )
        state['current_stage'] = "done"
        print(f"[最终化阶段] 完成，最终报告长度: {len(final_report)} 字符")
    except Exception as e:
        print(f"[最终化阶段] 错误: {e}")
        state['final_report'] = state['draft_report']  # 使用草稿作为最终报告
        state['current_stage'] = "done"
    
    return state


def should_continue(state: ResearchState) -> Literal["write", "finalize", "end"]:
    """条件判断函数：决定下一步流程"""
    if state['current_stage'] == "done":
        return "end"
    elif state['current_stage'] == "review":
        if state['iteration_count'] >= state['max_iterations']:
            return "finalize"  # 达到最大迭代次数，直接最终化
        return "write"  # 需要修改，返回写作阶段
    elif state['current_stage'] == "write" and state['iteration_count'] > 0:
        return "write"  # 继续修改
    else:
        return "finalize"  # 其他情况进入最终化


# ==================== 图构建 ====================
def create_research_graph():
    """创建研究助手的工作流图"""
    workflow = StateGraph(ResearchState)
    
    # 添加节点
    workflow.add_node("search", search_node)
    workflow.add_node("analyze", analyze_node)
    workflow.add_node("write", write_node)
    workflow.add_node("review", review_node)
    workflow.add_node("finalize", finalize_node)
    
    # 设置入口点
    workflow.set_entry_point("search")
    
    # 添加边
    workflow.add_edge("search", "analyze")
    workflow.add_edge("analyze", "write")
    workflow.add_edge("write", "review")
    
    # 条件边：根据审核结果决定下一步
    workflow.add_conditional_edges(
        "review",
        should_continue,
        {
            "write": "write",      # 需要修改，返回写作
            "finalize": "finalize", # 通过审核，进入最终化
            "end": END              # 完成
        }
    )
    
    workflow.add_edge("finalize", END)
    
    # 编译图（带检查点）
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)
    
    return app


# ==================== 主类 ====================
class ResearchAssistant:
    """研究助手主类"""
    
    def __init__(self, max_iterations: int = 3):
        """
        初始化研究助手
        
        Args:
            max_iterations: 最大迭代修改次数
        """
        self.max_iterations = max_iterations
        self.graph = create_research_graph()
    
    def research(self, topic: str, config: dict = None) -> dict:
        """
        执行研究任务
        
        Args:
            topic: 研究主题
            config: 配置参数（可选）
            
        Returns:
            包含研究结果的字典
        """
        # 初始化状态
        initial_state = {
            "messages": [SystemMessage(content="你是一位专业的研究助手")],
            "research_topic": topic,
            "search_results": [],
            "analysis": "",
            "draft_report": "",
            "review_feedback": "",
            "final_report": "",
            "current_stage": "search",
            "iteration_count": 0,
            "max_iterations": self.max_iterations,
        }
        
        # 运行图
        config = config or {"configurable": {"thread_id": "1"}}
        
        print(f"\n{'='*60}")
        print(f"开始研究任务: {topic}")
        print(f"{'='*60}\n")
        
        final_state = None
        for event in self.graph.stream(initial_state, config):
            # 打印每个节点的输出
            for node_name, node_output in event.items():
                if node_name != "__end__":
                    print(f"\n>>> 节点 '{node_name}' 执行完成")
            final_state = node_output if node_name != "__end__" else final_state
        
        print(f"\n{'='*60}")
        print("研究任务完成！")
        print(f"{'='*60}\n")
        
        return {
            "topic": topic,
            "final_report": final_state.get("final_report", ""),
            "draft_report": final_state.get("draft_report", ""),
            "analysis": final_state.get("analysis", ""),
            "search_results": final_state.get("search_results", []),
            "review_feedback": final_state.get("review_feedback", ""),
            "iteration_count": final_state.get("iteration_count", 0),
            "messages": final_state.get("messages", []),
        }
    
    def get_report(self, topic: str) -> str:
        """
        获取研究报告（简化接口）
        
        Args:
            topic: 研究主题
            
        Returns:
            最终研究报告文本
        """
        result = self.research(topic)
        return result.get("final_report", "")


# ==================== 使用示例 ====================
if __name__ == "__main__":
    # 注意：需要设置 OPENAI_API_KEY 环境变量
    # 如果需要使用 Tavily 搜索，还需要设置 TAVILY_API_KEY
    
    assistant = ResearchAssistant(max_iterations=2)
    
    # 执行研究
    result = assistant.research("人工智能在医疗领域的应用")
    
    # 打印结果
    print("\n" + "="*60)
    print("最终研究报告")
    print("="*60)
    print(result["final_report"])
    print("\n" + "="*60)
    print(f"迭代次数: {result['iteration_count']}")
    print("="*60)
