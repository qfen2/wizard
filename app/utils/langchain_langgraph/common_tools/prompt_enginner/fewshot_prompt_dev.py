"""
动态少样本示例（Few-shot）注入系统
基于 LangChain v1.2+
功能：根据用户问题类别，动态选择最相关的示例
"""

import os
from typing import List, Dict, Any, Literal
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# LangChain v1.2+ 导入（注意路径变化）
from langchain_core.prompts import ChatPromptTemplate, FewShotChatMessagePromptTemplate
from langchain_core.example_selectors import SemanticSimilarityExampleSelector
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda

import config

# 加载环境变量（API Key）
load_dotenv()


# ============ 1. 定义输出结构 ============
class AnswerWithCategory(BaseModel):
    """带类别的答案结构"""
    category: Literal["退货退款", "产品使用", "账户安全"] = Field(description="问题所属类别")
    answer: str = Field(description="问题的详细解答")
    confidence: float = Field(description="回答置信度，0-1之间")
    related_articles: List[str] = Field(default=[], description="相关帮助文章链接")


# ============ 2. 构建示例库 ============

# 2.1 基础示例数据（每个示例包含输入和期望输出）
examples = [
    # 退货退款类示例
    {
        "input": "我昨天买的衣服不合身，想退货怎么办？",
        "output": "退货流程很简单：1. 登录账号进入'我的订单'；2. 找到该商品点击'申请退货'；3. 选择退货原因并提交；4. 将商品寄回指定地址。退货款项会在收到商品后3个工作日内原路返回。",
        "category": "退货退款"
    },
    {
        "input": "商品有质量问题，可以退款吗？",
        "output": "是的，因质量问题可以全额退款。请提供商品瑕疵照片或视频，通过售后通道提交。审核通过后，我们会安排上门取件并承担运费。",
        "category": "退货退款"
    },
    {
        "input": "退货的运费谁承担？",
        "output": "运费承担规则：如果是商品质量问题或我们的失误，运费由我们承担；如果是个人原因（如不喜欢、尺码不合适），运费需由您承担。建议购买运费险。",
        "category": "退货退款"
    },

    # 产品使用类示例
    {
        "input": "怎么设置定时发布朋友圈？",
        "output": "目前APP支持定时发布功能：在发布界面点击'更多选项'，选择'定时发布'，设定好时间后点击确认即可。注意定时发布需要保持网络连接。",
        "category": "产品使用"
    },
    {
        "input": "如何修改支付密码？",
        "output": "修改支付密码步骤：我的 → 设置 → 账号安全 → 支付密码 → 修改。需要验证原密码或手机验证码。如忘记原密码，可通过'忘记密码'重置。",
        "category": "产品使用"
    },
    {
        "input": "视频能下载到本地吗？",
        "output": "支持下载功能：在视频播放页面点击下载图标，选择清晰度即可保存到本地。下载的视频可在'我的-离线缓存'中查看。部分版权视频可能不支持下载。",
        "category": "产品使用"
    },

    # 账户安全类示例
    {
        "input": "账号被盗了怎么办？",
        "output": "账号被盗请立即：1. 尝试通过手机号/邮箱找回密码；2. 联系客服冻结账号；3. 检查绑定手机和邮箱是否被篡改；4. 查看近期登录设备，踢出异常设备。",
        "category": "账户安全"
    },
    {
        "input": "收不到验证码怎么办？",
        "output": "收不到验证码请检查：1. 手机信号是否正常；2. 是否被手机管家拦截；3. 是否超过每日发送限制。如以上都正常，可尝试重启手机或联系客服。",
        "category": "账户安全"
    },
    {
        "input": "如何开启双重验证？",
        "output": "开启双重验证：我的 → 设置 → 账号安全 → 双重验证 → 按提示绑定手机或认证器APP。开启后，每次登录新设备都需要输入动态验证码。",
        "category": "账户安全"
    }
]


# 2.2 将示例转换为向量存储（用于语义搜索）
def create_example_selector():
    """创建基于语义相似度的示例选择器"""

    # 初始化嵌入模型
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    # 准备文本列表（用于向量化）
    texts = [ex["input"] for ex in examples]
    metadatas = examples  # 保留完整元数据

    # 创建向量存储
    vectorstore = FAISS.from_texts(
        texts=texts,
        embedding=embeddings,
        metadatas=metadatas
    )

    # 创建示例选择器
    example_selector = SemanticSimilarityExampleSelector(
        vectorstore=vectorstore,
        k=2,  # 每次选择2个最相关的示例
        example_keys=["input", "output"]  # 指定要返回的字段
    )

    return example_selector


# ============ 3. 构建动态少样本模板 ============

def create_few_shot_prompt(example_selector):
    """创建动态少样本提示模板"""

    # 定义单个示例的格式
    example_prompt = ChatPromptTemplate.from_messages([
        ("human", "{input}"),
        ("ai", "{output}")
    ])

    # 创建少样本模板
    few_shot_prompt = FewShotChatMessagePromptTemplate(
        example_selector=example_selector,  # 动态选择器
        example_prompt=example_prompt,
    )

    # 最终的系统提示
    system_prompt = """你是一个专业的客服助手。请根据用户问题，提供准确、友好的解答。

回答要求：
1. 基于提供的示例风格回答问题
2. 如果问题涉及多个方面，分点说明
3. 语气专业、耐心、友好
4. 不确定的信息不要编造

请用中文回答。"""

    # 组合最终模板
    final_prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        few_shot_prompt,  # 动态注入的示例
        ("human", "{input}")
    ])

    return final_prompt


# ============ 4. 构建带结构化输出的完整链 ============

def create_qa_chain():
    """创建完整的问答链"""

    # 创建示例选择器
    example_selector = create_example_selector()

    # 创建提示模板
    prompt = create_few_shot_prompt(example_selector)

    # 初始化模型（支持结构化输出）
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.3,
        max_tokens=1000
    )

    # 绑定结构化输出
    structured_llm = llm.with_structured_output(AnswerWithCategory)

    # 构建LCEL链
    chain = (
            RunnablePassthrough.assign(
                # 可以在这里添加其他预处理逻辑
                input=lambda x: x["question"]
            )
            | prompt
            | structured_llm
    )

    return chain


# ============ 5. 添加后处理和分析功能 ============

class FewShotAnalyzer:
    """少样本示例分析器：查看选中的示例"""

    def __init__(self, example_selector):
        self.example_selector = example_selector

    def get_selected_examples(self, query: str) -> List[Dict]:
        """查看给定查询会选中哪些示例"""
        selected = self.example_selector.select_examples({"input": query})
        return selected

    def print_selected_examples(self, query: str):
        """打印选中的示例"""
        selected = self.get_selected_examples(query)
        print(f"\n🔍 用户问题: {query}")
        print(f"📌 选中的 {len(selected)} 个示例:")
        for i, ex in enumerate(selected, 1):
            print(f"\n  示例 {i}:")
            print(f"    问题: {ex['input']}")
            print(f"    回答: {ex['output'][:50]}...")


# ============ 6. 使用示例 ============

def main():
    """主函数：演示动态少样本的效果"""

    print("=" * 60)
    print("动态少样本示例注入系统 (LangChain v1.2+)")
    print("=" * 60)
    llm_cfg = config.LLM.get('openai', config.LLM.get('modelscope', {}))

    model_name = llm_cfg.get('embedding_model', 'text-embedding-ada-002')

    # 如果 base_url 不为空，说明是使用兼容 API
    if llm_cfg.get('base_url'):
        # 使用兼容 API 时的模型名称
        model_name = llm_cfg.get('embedding_model', llm_cfg.get('model_name', 'text-embedding-ada-002'))


    embeddings = OpenAIEmbeddings(
            model=model_name,
            api_key=llm_cfg.get('api_key', os.getenv('OPENAI_API_KEY')),
            base_url=llm_cfg.get('base_url')
        )
    # 创建示例选择器
    # embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    texts = [ex["input"] for ex in examples]
    metadatas = examples
    vectorstore = FAISS.from_texts(texts, embeddings, metadatas)

    example_selector = SemanticSimilarityExampleSelector(
        vectorstore=vectorstore,
        k=2,
        example_keys=["input", "output"]
    )

    # 创建分析器
    analyzer = FewShotAnalyzer(example_selector)

    # 创建问答链
    chain = create_qa_chain()

    # 测试问题列表
    test_questions = [
        "我想退掉昨天买的鞋子，怎么操作？",  # 退货退款类
        "怎么设置自动回复？",  # 产品使用类
        "手机丢了，怎么保护账号安全？",  # 账户安全类
        "衣服买大了能换小一码吗？",  # 退货退款类（变体）
    ]

    # 逐个测试
    for question in test_questions:
        print("\n" + "-" * 50)

        # 1. 查看选中的示例
        analyzer.print_selected_examples(question)

        # 2. 执行问答
        print("\n🤖 AI 回答:")
        result = chain.invoke({"question": question})

        # 3. 打印结果
        print(f"类别: {result.category}")
        print(f"置信度: {result.confidence}")
        print(f"回答: {result.answer}")
        if result.related_articles:
            print(f"相关文章: {', '.join(result.related_articles)}")

        print("-" * 50)


# ============ 7. 高级用法：自定义示例选择逻辑 ============

class HybridExampleSelector:
    """混合示例选择器：结合规则和语义"""

    def __init__(self, vectorstore, examples):
        self.vectorstore = vectorstore
        self.examples = examples
        self.category_keywords = {
            "退货退款": ["退货", "退款", "换货", "运费", "退钱", "质量问题"],
            "产品使用": ["怎么用", "如何设置", "功能", "操作", "步骤", "使用"],
            "账户安全": ["密码", "账号", "登录", "验证码", "安全", "被盗"]
        }

    def select_examples(self, query: str, k: int = 2) -> List[Dict]:
        """混合选择示例"""

        # 方法1：基于规则的类别匹配
        detected_category = self._detect_category(query)

        # 方法2：语义相似度搜索
        docs = self.vectorstore.similarity_search_with_score(query, k=k * 2)

        # 融合策略：优先选择同类别且语义相似的
        candidates = []
        for doc, score in docs:
            example = doc.metadata
            # 如果是同类别，降低相似度阈值
            if example.get("category") == detected_category:
                candidates.append((example, score * 0.8))  # 同类别加分
            else:
                candidates.append((example, score))

        # 排序并返回top k
        candidates.sort(key=lambda x: x[1])
        return [ex for ex, _ in candidates[:k]]

    def _detect_category(self, query: str) -> str:
        """基于关键词检测类别"""
        query_lower = query.lower()
        scores = {cat: 0 for cat in self.category_keywords}

        for cat, keywords in self.category_keywords.items():
            for kw in keywords:
                if kw in query_lower:
                    scores[cat] += 1

        return max(scores, key=scores.get) if max(scores.values()) > 0 else "产品使用"


# ============ 8. 性能评估 ============

async def evaluate_few_shot_performance(chain, test_set: List[Dict]):
    """评估少样本效果"""

    from langchain_core.callbacks import get_openai_callback

    results = []
    total_tokens = 0
    total_cost = 0

    for test in test_set:
        with get_openai_callback() as cb:
            # 执行
            result = chain.invoke({"question": test["question"]})

            # 记录指标
            results.append({
                "question": test["question"],
                "expected_category": test["category"],
                "actual_category": result.category,
                "correct_category": result.category == test["category"],
                "confidence": result.confidence,
                "tokens": cb.total_tokens,
                "cost": cb.total_cost
            })

            total_tokens += cb.total_tokens
            total_cost += cb.total_cost

    # 计算准确率
    accuracy = sum(1 for r in results if r["correct_category"]) / len(results)

    print(f"\n📊 评估结果:")
    print(f"准确率: {accuracy:.2%}")
    print(f"总Token: {total_tokens}")
    print(f"总成本: ${total_cost:.4f}")
    print(f"平均每个请求: {total_tokens / len(results):.0f} tokens")

    return results


# 运行主程序
if __name__ == "__main__":
    main()

    # 可选：运行评估
    # test_set = [
    #     {"question": "怎么申请退货", "category": "退货退款"},
    #     {"question": "如何修改密码", "category": "账户安全"},
    #     {"question": "视频播放卡顿", "category": "产品使用"},
    # ]
    # chain = create_qa_chain()
    # import asyncio
    # asyncio.run(evaluate_few_shot_performance(chain, test_set))