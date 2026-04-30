from langchain_core.prompts import FewShotChatMessagePromptTemplate, ChatPromptTemplate

# 示例库（按用户水平分类）
examples = [
    {
        "input": "什么是函数？",
        "output": "函数就像是一个菜谱，你把食材（参数）放进去，按照步骤（代码）操作，就能得到一道菜（返回值）"
    },
    {
        "input": "什么是循环？",
        "output": "循环就像是在跑步机上，你设定好圈数，它会自动重复跑步动作直到完成"
    }
]

# 构建 Few-Shot 模板
example_prompt = ChatPromptTemplate.from_messages([
    ("human", "{input}"),
    ("ai", "{output}")
])

few_shot_prompt = FewShotChatMessagePromptTemplate(
    example_prompt=example_prompt,
    examples=examples
)

# 组合最终模板
final_prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个用比喻解释概念的助手。请参考示例的讲解风格。"),
    few_shot_prompt,
    ("human", "{input}")
])