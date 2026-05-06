import os
import base64
from typing import List, Optional
from typing_extensions import TypedDict
from pydantic import BaseModel, Field

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END

import config

TEXT_MODEL_NAME = "gpt-4o"     # 纯文本请求时使用的模型（如果没有4o，可以降级写 "gpt-3.5-turbo"）
VISION_MODEL_NAME = "gpt-4o"   # 传图片时使用的模型（如果你中转站报错，可以尝试改成 "gpt-4-vision-preview" 或 "gpt-4o-mini"）

# ==========================================
# 1. 工具函数：本地图片转 Base64
# ==========================================
def encode_image_to_base64(image_path: str) -> str:
    """读取本地图片并转换为 base64 编码，以便喂给大模型"""
    if not os.path.exists(image_path):
        print(f"⚠️ 警告：找不到图片路径 {image_path}")
        return ""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        print(f"⚠️ 图片读取失败 {image_path}: {e}")
        return ""


# ==========================================
# 2. 定义数据状态 (State) 和 结构化输出模型
# ==========================================
class ListingState(TypedDict):
    keywords: str  # 输入：文本关键词/描述
    competitor_info: str  # 输入：竞品信息
    image_paths: Optional[List[str]]  # 【新增】输入：本地图片路径列表
    final_title: str  # 输出：生成的标题
    final_bullets: List[str]  # 输出：生成的 5 点描述


class AmazonListingOutput(BaseModel):
    title: str = Field(description="The Amazon product title, strictly under 200 characters.")
    bullet_points: List[str] = Field(
        description="Exactly 5 bullet points for the Amazon listing.",
        min_length=5,
        max_length=5
    )


# ==========================================
# 3. 核心 Prompt Engineering
# ==========================================
# 【修改了Prompt】：明确告诉模型需要结合图片来提取卖点
SYSTEM_PROMPT = """
You are a Top-Tier Amazon Listing Optimization Expert and native English copywriter. 
Your task is to generate 1 Product Title and 5 Bullet Points based on the provided text descriptions AND the provided images (if any).

=== MULTIMODAL INTEGRATION LOGIC (CRITICAL) ===
When both Images and Keywords are provided, you MUST follow this integration logic:
1. FACTUAL PRECEDENCE: Provided text keywords (materials, dimensions, brand, specific technical terms) ALWAYS take precedence. If the image seems to show plastic but the keyword says "304 Stainless Steel", strictly use "304 Stainless Steel".
2. VISUAL EXTRACTION: Use the images to extract descriptive details that words might miss: shape, color, texture, structural design, usability features, and the lifestyle/context of the product.
3. WEAVING: Seamlessly weave the hard factual Keywords with the rich visual details from the Images to create compelling, SEO-friendly copy. DO NOT invent features that are neither in the images nor the text.

=== STRICT GUIDELINES ===

[TITLE RULES]
1. Length Target: MUST be between 150 and 195 characters. DO NOT write short titles. You must maximize the character allowance to improve search visibility.
2. Structure: [Brand Name] + [Core Keyword] + [Top Feature/Material] + [Size/Color/Specs] + [Target Audience] + [Secondary Keywords/Synonyms] + [Ideal Use Case].
3. SEO Density Strategy: If the title is too short, naturally add highly relevant synonyms, descriptive adjectives (e.g., Heavy-Duty, Premium, Versatile), and specific scenarios (e.g., for Home, Kitchen, Outdoor Camping) to reach the 150-195 character target. 
4. Readability: Capitalize the first letter of each word. Ensure it flows naturally despite being keyword-dense.

[BULLET POINT RULES (Exactly 5)]
1. Length: Each bullet point MUST be between 150 and 250 characters.
2. Structure: [ALL CAPS BENEFIT/FEATURE HOOK] - [Detailed explanation highlighting the solution to customer pain points].
   Example: MULTI-PURPOSE ORGANIZATION - This versatile storage box...
3. Content Breakdown:
   - Bullet 1: Core Material & Build Quality (Combine text specs with visual texture).
   - Bullet 2: Main Functionality & Unique Design (Derived from visual structure).
   - Bullet 3: Key Selling Point or Portability/Size constraint.
   - Bullet 4: Ease of Use & Specific Scenarios (Imagine the scenario based on the image).
   - Bullet 5: Target Audience & Satisfaction/Gift appeal.
4. Tone: Persuasive, professional, and benefit-driven.

[PROHIBITED]
- DO NOT use promotional phrases like "Best seller", "Free shipping".
- DO NOT use special characters like ★, ®, ™, or emojis.
- DO NOT hallucinate features not supported by the inputs.
"""


# ==========================================
# 4. 定义 LangGraph 节点处理逻辑 (支持图文混合)
# ==========================================
def generate_listing_node(state: ListingState):
    print("🤖 AI 正在分析图片与文本，构思亚马逊文案...")

    # 必须使用具备视觉能力的模型，如 gpt-4o 或 gpt-4o-mini
    # llm = ChatOpenAI(model="gpt-4o", temperature=0.7)
    llm_cfg = config.LLM['silicon']

    llm = ChatOpenAI(
        model=llm_cfg['model_name'],
        api_key=llm_cfg['api_key'],
        base_url=llm_cfg['base_url'],
        temperature=0
    )

    img_llm = ChatOpenAI(
        model=llm_cfg['img_model_name'],
        api_key=llm_cfg['api_key'],
        base_url=llm_cfg['base_url'],
        temperature=0
    )

    # 构建 System Message
    sys_msg = SystemMessage(content=SYSTEM_PROMPT)
    images = state.get("image_paths") or []
    valid_images = [img for img in images if os.path.exists(img)]

    structured_llm = llm.with_structured_output(AmazonListingOutput) if not valid_images else img_llm.with_structured_output(AmazonListingOutput)


    # 构建 Human Message 的内容数组（图文混合结构）
    user_text = f"Keywords/Features: {state.get('keywords', 'None')}\nCompetitor Info: {state.get('competitor_info', 'None')}"

    # ---------------- 核心分支逻辑 ----------------
    if not valid_images:
        print(f"📝 未检测到图片，采用 [纯文本模式] 调用 {TEXT_MODEL_NAME}...")
        human_msg = HumanMessage(content=user_text)
    else:
        print(f"📸 检测到 {len(valid_images)} 张图片，采用 [多模态模式] 调用 {VISION_MODEL_NAME}...")

        # 多模态模式：构建复杂的 List 结构
        message_content = [{"type": "text", "text": user_text}]
        for img_path in valid_images:
            base64_image = encode_image_to_base64(img_path)
            if base64_image:
                message_content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}",
                        "detail": "high"
                    }
                })

        human_msg = HumanMessage(content=message_content)

    messages = [sys_msg, human_msg]

    # ---------------- 执行调用 ----------------
    response: AmazonListingOutput = structured_llm.invoke(messages)

    return {
        "final_title": response.title,
        "final_bullets": response.bullet_points
    }

# ==========================================
# 5. 构建与暴露接口
# ==========================================
def build_graph():
    workflow = StateGraph(ListingState)  # type: ignore
    workflow.add_node("generate_copy", generate_listing_node)  # type: ignore
    workflow.set_entry_point("generate_copy")
    workflow.add_edge("generate_copy", END)
    return workflow.compile()


def generate_amazon_listing(keywords: str, competitor_info: str = "", image_paths: List[str] = None) -> dict:
    """
    外部接口：新增 image_paths 参数，支持传入多张本地图片路径
    """
    app = build_graph()
    initial_state = {
        "keywords": keywords,
        "competitor_info": competitor_info,
        "image_paths": image_paths or []
    }

    try:
        final_state = app.invoke(initial_state)  # type:ignore
        return {
            "title": final_state["final_title"],
            "bullets": final_state["final_bullets"]
        }
    except Exception as e:
        print(f"❌ 生成文案时发生错误: {e}")
        return {"title": "Error generating title", "bullets": ["Error generating bullets."]}


# ================= 独立测试区 =================
if __name__ == "__main__":
    # 【测试指引】随便在电脑里找一张产品的图片，把路径填在这里测试
    # 注意：Windows 路径用双反斜杠 \\ 或者在字符串前面加 r
    test_image_path = r"C:\Users\liukk\Desktop\wizard\app\utils\amazon_listing_tool\test_product1.jpg"

    test_keywords = "不粘锅, 适合送给岳母, 终身质保, 仅重500克。"

    # 构造图片列表，即使没有图片传入 [] 也不会报错
    test_images = [test_image_path] if os.path.exists(test_image_path) else []

    print("\n--- 开始测试 [多模态] LangGraph 文案生成 ---")
    if test_images:
        print(f"📸 发现了 {len(test_images)} 张图片，将结合图片生成文案...")
    else:
        print("⚠️ 未发现图片，将仅使用文本生成...")

    result = generate_amazon_listing(
        keywords=test_keywords,
        competitor_info="",
        image_paths=test_images
    )

    print("\n✅ 生成成功！\n")
    print("【Title】")
    print(result['title'])

    print("\n【Bullet Points】")
    for i, bp in enumerate(result['bullets']):
        print(f"{i + 1}. {bp}")