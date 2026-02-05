# LangChain & LangGraph 复杂案例实现

本目录包含使用最新版本的 LangChain 和 LangGraph 实现的复杂多智能体协作研究助手系统。

## 功能特性

这是一个展示 LangChain 和 LangGraph 强大功能的复杂案例，实现了：

1. **多智能体协作**：包含搜索、分析、写作、审核四个专业智能体
2. **状态管理**：使用 LangGraph 的状态图管理复杂的工作流状态
3. **条件分支**：根据审核结果智能决定是否需要修改报告
4. **循环迭代**：支持多轮修改优化，直到达到质量标准
5. **工具集成**：集成搜索工具（Tavily）和自定义工具

## 系统架构

### 工作流程

```
搜索 → 分析 → 写作 → 审核 → [修改] → 最终化 → 完成
                ↑         ↓
                └──────────┘
              (条件循环)
```

### 节点说明

1. **搜索节点 (search_node)**
   - 使用 Tavily 搜索工具收集相关信息
   - 收集多个搜索结果

2. **分析节点 (analyze_node)**
   - 分析搜索到的信息
   - 提取关键发现、趋势和重要数据

3. **写作节点 (write_node)**
   - 基于分析结果撰写研究报告草稿
   - 包含引言、发现、分析、结论等部分

4. **审核节点 (review_node)**
   - 审核报告质量
   - 提供改进建议
   - 决定是否需要修改

5. **最终化节点 (finalize_node)**
   - 生成最终格式化的研究报告
   - 整合所有信息和反馈

## 安装依赖

确保已安装所有必需的依赖：

```bash
pip install -r requirements.txt
```

主要依赖包括：
- `langchain>=0.3.0` - LangChain 核心库
- `langchain-openai>=0.2.0` - OpenAI 集成
- `langchain-community>=0.3.0` - 社区工具集成
- `langgraph>=0.2.0` - LangGraph 工作流引擎
- `tavily-python>=0.3.0` - Tavily 搜索工具

## 环境配置

使用前需要设置以下环境变量：

```bash
# OpenAI API Key（必需）
export OPENAI_API_KEY="your-openai-api-key"

# Tavily API Key（可选，用于搜索功能）
export TAVILY_API_KEY="your-tavily-api-key"
```

或者在代码中设置：

```python
import os
os.environ["OPENAI_API_KEY"] = "your-openai-api-key"
os.environ["TAVILY_API_KEY"] = "your-tavily-api-key"
```

## 使用方法

### 基本使用

```python
from app.utils.langchain_langgraph import ResearchAssistant

# 创建研究助手实例
assistant = ResearchAssistant(max_iterations=3)

# 执行研究任务
result = assistant.research("人工智能在医疗领域的应用")

# 获取最终报告
print(result["final_report"])

# 查看详细信息
print(f"迭代次数: {result['iteration_count']}")
print(f"分析结果: {result['analysis']}")
print(f"审核反馈: {result['review_feedback']}")
```

### 简化接口

```python
from app.utils.langchain_langgraph import ResearchAssistant

assistant = ResearchAssistant()

# 直接获取报告文本
report = assistant.get_report("量子计算的最新进展")
print(report)
```

### 自定义配置

```python
from app.utils.langchain_langgraph import ResearchAssistant

assistant = ResearchAssistant(max_iterations=5)  # 最多迭代5次

# 使用自定义配置
config = {
    "configurable": {
        "thread_id": "research-001"
    }
}

result = assistant.research("区块链技术", config=config)
```

## 代码结构

```
langchain_langgraph/
├── __init__.py              # 模块导出
├── research_assistant.py    # 主要实现文件
└── README.md                # 本文档
```

## 核心类和方法

### ResearchAssistant

主类，封装了完整的研究助手功能。

**方法：**
- `__init__(max_iterations=3)`: 初始化，设置最大迭代次数
- `research(topic, config=None)`: 执行完整的研究流程
- `get_report(topic)`: 简化接口，直接返回报告文本

### ResearchState

状态类型定义，包含：
- `messages`: 消息历史
- `research_topic`: 研究主题
- `search_results`: 搜索结果
- `analysis`: 分析结果
- `draft_report`: 草稿报告
- `review_feedback`: 审核反馈
- `final_report`: 最终报告
- `current_stage`: 当前阶段
- `iteration_count`: 迭代次数

## 工作流详解

### 状态流转

1. **初始状态**: `current_stage = "search"`
2. **搜索完成**: `current_stage = "analyze"`
3. **分析完成**: `current_stage = "write"`
4. **写作完成**: `current_stage = "review"`
5. **审核判断**:
   - 如果通过 → `current_stage = "finalize"`
   - 如果需要修改 → `current_stage = "write"` (循环)
6. **最终化完成**: `current_stage = "done"`

### 条件分支逻辑

`should_continue()` 函数根据以下条件决定下一步：
- 如果达到最大迭代次数 → 直接最终化
- 如果审核通过 → 进入最终化
- 如果需要修改 → 返回写作阶段

## 示例输出

执行研究任务时，会看到类似以下的输出：

```
============================================================
开始研究任务: 人工智能在医疗领域的应用
============================================================

[搜索阶段] 正在搜索主题: 人工智能在医疗领域的应用
[搜索阶段] 完成，找到 5 条结果

>>> 节点 'search' 执行完成

[分析阶段] 正在分析收集到的信息...
[分析阶段] 完成

>>> 节点 'analyze' 执行完成

[写作阶段] 正在撰写报告草稿...
[写作阶段] 完成，草稿长度: 1234 字符

>>> 节点 'write' 执行完成

[审核阶段] 正在审核报告草稿...
[审核阶段] 完成，反馈: 报告质量良好，但建议...

>>> 节点 'review' 执行完成

[最终化阶段] 正在生成最终报告...
[最终化阶段] 完成，最终报告长度: 1567 字符

============================================================
研究任务完成！
============================================================
```

## 扩展和定制

### 添加自定义工具

```python
from langchain_core.tools import tool

@tool
def custom_analysis_tool(data: str) -> str:
    """自定义分析工具"""
    # 实现你的逻辑
    return "分析结果"
```

### 修改节点逻辑

可以直接修改 `research_assistant.py` 中的节点函数：
- `search_node()`: 修改搜索逻辑
- `analyze_node()`: 修改分析逻辑
- `write_node()`: 修改写作逻辑
- `review_node()`: 修改审核逻辑
- `finalize_node()`: 修改最终化逻辑

### 添加新节点

```python
def new_node(state: ResearchState) -> ResearchState:
    # 实现节点逻辑
    return state

# 在 create_research_graph() 中添加
workflow.add_node("new_node", new_node)
workflow.add_edge("previous_node", "new_node")
```

## 注意事项

1. **API 费用**: 使用 OpenAI API 会产生费用，请注意控制使用量
2. **搜索限制**: Tavily 搜索有使用限制，建议设置 API Key
3. **迭代次数**: 合理设置 `max_iterations`，避免无限循环
4. **错误处理**: 代码包含基本的错误处理，但建议在生产环境中增强

## 故障排除

### 常见问题

1. **OpenAI API 错误**
   - 检查 `OPENAI_API_KEY` 是否正确设置
   - 确认账户有足够的额度

2. **Tavily 搜索失败**
   - 检查 `TAVILY_API_KEY` 是否设置
   - 如果没有设置，搜索功能可能不可用

3. **导入错误**
   - 确保已安装所有依赖：`pip install -r requirements.txt`
   - 检查 Python 版本（建议 3.8+）

## 参考资料

- [LangChain 官方文档](https://python.langchain.com/)
- [LangGraph 官方文档](https://langchain-ai.github.io/langgraph/)
- [Tavily 搜索 API](https://tavily.com/)

## 许可证

本代码遵循项目主许可证。
