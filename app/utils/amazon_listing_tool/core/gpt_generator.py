import os
from typing import TypedDict, List
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END

import config


# 如果你没有在环境变量中设置，取消下面这行的注释并填入你的 Key
# os.environ["OPENAI_API_KEY"] = "sk-xxxxxxxxxxxxxxxxxxxxxxxx"

# ==========================================
# 1. 定义数据状态 (State) 和 结构化输出模型
# ==========================================

# 定义 LangGraph 在节点之间传递的数据结构
class ListingState(TypedDict):
    keywords: str  # 输入：从 1688 或人工提取的关键词
    competitor_info: str  # 输入：竞品信息（可选）
    final_title: str  # 输出：生成的标题
    final_bullets: List[str]  # 输出：生成的 5 点描述


# 定义强制大模型输出的 JSON 数据结构 (Pydantic Model)
class AmazonListingOutput(BaseModel):
    title: str = Field(description="The Amazon product title, strictly under 200 characters.")
    bullet_points: List[str] = Field(
        description="Exactly 5 bullet points for the Amazon listing.",
        min_length=5,
        max_length=5
    )


# ==========================================
# 2. 核心 Prompt Engineering (极致的 Prompt)
# ==========================================

# 这是一个极其详细的 System Prompt，包含了亚马逊 A9 算法的优化逻辑
SYSTEM_PROMPT = """
You are a Top-Tier Amazon Listing Optimization Expert and native English copywriter. 
Your profound understanding of the Amazon A9 algorithm helps you write high-converting, SEO-optimized product listings.

Your task is to generate 1 Product Title and 5 Bullet Points based on the provided keywords and competitor information.

=== STRICT GUIDELINES ===

[TITLE RULES]
1. Length: STRICTLY under 200 characters (including spaces).
2. Structure: [Brand Name] + [Core Keyword] + [Key Feature/Material] + [Size/Color] + [Target Audience/Use Case]. 
   (Assume Brand Name is "Generic" if not provided, you can omit it if it makes the title too long).
3. SEO: Front-load the most important high-search-volume keywords at the beginning.
4. Readability: Do not just stuff keywords. It must read naturally to a human buyer. Capitalize the first letter of each word (except prepositions).

[BULLET POINT RULES (Exactly 5)]
1. Length: Each bullet point MUST be between 150 and 250 characters.
2. Structure for each point: [ALL CAPS BENEFIT/FEATURE HOOK] - [Detailed explanation highlighting the solution to customer pain points].
   Example: MULTI-PURPOSE ORGANIZATION - This versatile storage box...
3. Content Breakdown:
   - Bullet 1: Core Material/Build Quality & Durability.
   - Bullet 2: Main Functionality & Primary Use Case.
   - Bullet 3: Key Selling Point (Differentiator from competitors).
   - Bullet 4: Size, Compatibility, or Ease of Use.
   - Bullet 5: Warranty, Package contents, or Customer Satisfaction guarantee.
4. Tone: Persuasive, professional, and benefit-driven. Focus on 'What's in it for the buyer?'.

[PROHIBITED]
- DO NOT use promotional phrases like "Best seller", "Free shipping", "Number 1", "Hot sale".
- DO NOT use special characters like ★, ®, ™, or emojis.

Process the provided {keywords} and {competitor_info} to create the listing.
"""


# ==========================================
# 3. 定义 LangGraph 节点处理逻辑
# ==========================================

def generate_listing_node(state: ListingState):
    """
    这是 LangGraph 中的处理节点：调用 LLM 生成结构化文案
    """
    print("🤖 AI 正在基于关键词构思亚马逊文案...")

    # 推荐使用 gpt-4o，它的指令遵循能力和结构化输出能力极强
    # temperature 设为 0.7 保证一定的创造性，但不会过于发散
    # llm = ChatOpenAI(model="gpt-5.5", temperature=
    llm_cfg = config.LLM['silicon']

    llm = ChatOpenAI(
        model=llm_cfg['model_name'],
        api_key=llm_cfg['api_key'],
        base_url=llm_cfg['base_url'],
        temperature=0
    )
    # 绑定 Pydantic 模型，强制 LLM 输出 JSON 并解析为 Python 对象
    structured_llm = llm.with_structured_output(AmazonListingOutput)

    # 组装 Prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "Keywords/Features from source: {keywords}\n\nCompetitor Info/Extra notes: {competitor_info}")
    ])

    # 构建执行链
    chain = prompt | structured_llm

    # 执行大模型调用
    response: AmazonListingOutput = chain.invoke({
        "keywords": state.get("keywords", ""),
        "competitor_info": state.get("competitor_info", "None provided.")
    })

    # 将生成的结果更新到 Graph 的状态中
    return {
        "final_title": response.title,
        "final_bullets": response.bullet_points
    }


# ==========================================
# 4. 构建并编译 LangGraph 工作流
# ==========================================

def build_graph():
    # 初始化状态图
    workflow = StateGraph(ListingState) # type:ignore

    # 添加节点 (Node)
    workflow.add_node("generate_copy", generate_listing_node) # type:ignore

    # 定义执行边 (Edges) - 目前是最简单的一条直线
    workflow.set_entry_point("generate_copy")
    workflow.add_edge("generate_copy", END)

    # 编译成可执行的 application
    app = workflow.compile()
    return app


# ==========================================
# 5. 暴露给外部调用的主函数
# ==========================================

def generate_amazon_listing(keywords: str, competitor_info: str = "") -> dict:
    """
    封装好的外部接口，接收输入，返回包含 title 和 bullets 的字典
    """
    app = build_graph()

    # 初始状态输入
    initial_state = {
        "keywords": keywords,
        "competitor_info": competitor_info
    }

    try:
        # 执行图流转
        final_state = app.invoke(initial_state) # type:ignore
        return {
            "title": final_state["final_title"],
            "bullets": final_state["final_bullets"]
        }
    except Exception as e:
        print(f"❌ 生成文案时发生错误: {e}")
        return {"title": "Error generating title", "bullets": ["Error generating bullets."]}


# ================= 独立测试区 =================
if __name__ == "__main__":
    # 独立测试一下这个模块
    test_keywords = "便携式, 304不锈钢, 户外露营咖啡壶, 防烫手柄, 800ml容量"
    test_competitor = "竞品卖点是加热快，但用户评论抱怨盖子容易掉。我们需要强调我们的盖子有安全锁扣设计。"

    print("\n--- 开始测试 LangGraph 文案生成 ---")
    result = generate_amazon_listing(test_keywords, test_competitor)

    print("\n✅ 生成成功！\n")
    print("【Title】")
    print(result['title'])
    print(f"(字数: {len(result['title'])})")

    print("\n【Bullet Points】")
    for i, bp in enumerate(result['bullets']):
        print(f"{i + 1}. {bp}")
        print(f"   (字数: {len(bp)})")