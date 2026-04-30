from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

# ❌ 过时写法（2023风格）
# template = "你是一名资深Python专家，请解释{concept}"

# ✅ 2026年推荐写法：明确上下文和约束
template = ChatPromptTemplate.from_messages([
    ("system", """
<context>
用户水平：{user_level}
任务类型：{task_type}
输出要求：{output_requirements}
</context>

请根据以上上下文，严格遵循输出要求完成任务。
    """),
    ("human", "{user_input}")
])

# 使用时传入具体上下文
prompt = template.format_messages(
    user_level="刚学Python两周的初学者，对函数有基本了解",
    task_type="概念解释",
    output_requirements="用生活比喻，附简单代码示例，避免专业术语",
    user_input="什么是装饰器？"
)