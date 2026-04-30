import hashlib
import json
from datetime import datetime
from typing import Dict, Any, List

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough


class PromptVersion:
    """提示词版本管理"""

    def __init__(self, name: str, template: str, version: str, model: str):
        self.name = name
        self.template = template
        self.version = version
        self.model = model
        self.created_at = datetime.now()
        self.prompt = ChatPromptTemplate.from_template(template)
        self.version_id = hashlib.md5(
            f"{template}{model}".encode()
        ).hexdigest()[:8]

    def format(self, **kwargs):
        return self.prompt.format_messages(**kwargs)


class PromptRegistry:
    """提示词注册中心"""

    def __init__(self):
        self.versions: Dict[str, List[PromptVersion]] = {}
        self.active_versions: Dict[str, str] = {}

    def register(self, version: PromptVersion):
        if version.name not in self.versions:
            self.versions[version.name] = []
        self.versions[version.name].append(version)

    def activate(self, name: str, version_id: str):
        self.active_versions[name] = version_id

    def get_active(self, name: str) -> PromptVersion:
        target_id = self.active_versions.get(name)
        for v in self.versions.get(name, []):
            if v.version_id == target_id:
                return v
        return self.versions.get(name, [])[-1]  # 默认最新


from langchain_openai import ChatOpenAI
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import BaseMessage
from pydantic import BaseModel, Field
from typing import Literal
import time


class MetricsCallback(BaseCallbackHandler):
    """记录调用指标"""

    def __init__(self):
        self.tokens = 0
        self.start_time = None

    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs):
        self.start_time = time.time()

    def on_llm_end(self, response, **kwargs):
        if hasattr(response, 'llm_output') and response.llm_output:
            self.tokens = response.llm_output.get('token_usage', {}).get('total_tokens', 0)

    def on_chain_end(self, outputs, **kwargs):
        self.latency = time.time() - self.start_time

# 定义期望的输出结构（替代"角色扮演"）
class Explanation(BaseModel):
    """概念解释的结构化输出"""
    concept: str = Field(description="被解释的概念名称")
    analogy: str = Field(description="生活化的比喻，帮助理解")
    code_example: str = Field(description="简单的代码示例")
    common_mistake: str = Field(description="初学者常见的误解")
    difficulty: Literal["简单", "中等", "困难"] = Field(description="概念的难度级别")

class PromptExecutor:
    """提示词执行器（带监控）"""

    def __init__(self, registry: PromptRegistry, model_name: str = "gpt-4o-mini"):
        self.registry = registry
        self.llm = ChatOpenAI(model=model_name, temperature=0)
        self.metrics = []

    def run(self, prompt_name: str, **kwargs) -> Dict[str, Any]:
        # 获取版本
        version = self.registry.get_active(prompt_name)
        parser = PydanticOutputParser(pydantic_object=Explanation)

        # 准备回调
        callback = MetricsCallback()

        # 构建链（带结构化输出）
        chain = (
                RunnablePassthrough.assign(
                    format_instructions=lambda _: parser.get_format_instructions()
                )
                | version.prompt
                | self.llm
                | parser
        )

        # 执行
        start = time.time()
        result = chain.invoke(kwargs, config={"callbacks": [callback]})
        latency = time.time() - start

        # 记录指标
        metric = {
            "prompt_name": prompt_name,
            "version_id": version.version_id,
            "timestamp": datetime.now(),
            "tokens": callback.tokens,
            "latency": latency,
            "success": True
        }
        self.metrics.append(metric)

        return {
            "result": result,
            "version": version.version_id,
            "metrics": metric
        }