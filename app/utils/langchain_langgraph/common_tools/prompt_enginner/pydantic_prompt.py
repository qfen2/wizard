from pydantic import BaseModel, Field
from typing import Literal
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnablePassthrough

import config


# 定义期望的输出结构（替代"角色扮演"）
class Explanation(BaseModel):
    """概念解释的结构化输出"""
    concept: str = Field(description="被解释的概念名称")
    analogy: str = Field(description="生活化的比喻，帮助理解")
    code_example: str = Field(description="简单的代码示例")
    common_mistake: str = Field(description="初学者常见的误解")
    difficulty: Literal["简单", "中等", "困难"] = Field(description="概念的难度级别")

# 创建解析器
parser = PydanticOutputParser(pydantic_object=Explanation)


# 构建模板（自动包含格式指令）
prompt = PromptTemplate(
    template="请解释{concept}。\n{format_instructions}",
    input_variables=["concept"],
    partial_variables={"format_instructions": parser.get_format_instructions()}
)

# 格式化
formatted_prompt = prompt.format(concept="装饰器")
print(formatted_prompt)
# 输出会包含详细的 JSON 格式说明

from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnablePassthrough

llm_modelscope_cfg = config.LLM['modelscope']

# 初始化模型
llm = advanced_llm = ChatOpenAI(
    model=llm_modelscope_cfg['model_name'],
    api_key=llm_modelscope_cfg['api_key'],
    base_url=llm_modelscope_cfg['base_url'],
    temperature=1
)
# 构建 LCEL 链（替代老式的 LLMChain）
chain = (
    RunnablePassthrough.assign(
        format_instructions=lambda _: parser.get_format_instructions()
    )
    | prompt
    | llm
    | parser
)

# 调用
result = chain.invoke({"concept": "装饰器"})
print(f"概念：{result.concept}")
print(f"比喻：{result.analogy}")
print(f"代码：{result.code_example}")
print(f"难度：{result.difficulty}")
# 输出是结构化的 Python 对象，可直接使用