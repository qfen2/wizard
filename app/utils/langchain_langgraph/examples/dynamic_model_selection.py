import time

from langchain_core.messages import SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from langgraph.prebuilt import ToolRuntime

import config

# 1. 配置 ModelScope 凭证
MODELSCOPE_API_KEY = "你的_MODELSCOPE_SDK_TOKEN"
MODELSCOPE_BASE_URL = "https://api-inference.modelscope.cn/v1"

# tools = [get_weather]
@tool
def summarize_conversation(
    runtime: ToolRuntime
) -> str:
    """Summarize the conversation so far."""
    messages = runtime.state["messages"]

    human_msgs = sum(1 for m in messages if m.__class__.__name__ == "HumanMessage")
    ai_msgs = sum(1 for m in messages if m.__class__.__name__ == "AIMessage")
    tool_msgs = sum(1 for m in messages if m.__class__.__name__ == "ToolMessage")

    return f"Conversation has {human_msgs} user messages, {ai_msgs} AI responses, and {tool_msgs} tool results"

llm_modelscope_cfg = config.LLM['modelscope']

# 3. 初始化模型 (连接到 ModelScope)
# 建议使用 Qwen2.5 系列，它们在工具调用（Tool Calling）上表现非常出色
basic_model = ChatOpenAI(
    model=llm_modelscope_cfg['model_name'],
    api_key=llm_modelscope_cfg['api_key'],
    base_url=llm_modelscope_cfg['base_url'],
    temperature=0
)

advanced_model = ChatOpenAI(
    model=llm_modelscope_cfg['model_name'],
    api_key=llm_modelscope_cfg['api_key'],
    base_url=llm_modelscope_cfg['base_url'],
    temperature=0
)

# basic_model = ChatOpenAI(model="gpt-4o-mini")
# advanced_model = ChatOpenAI(model="gpt-4o")

@wrap_model_call
def dynamic_model_selection(request: ModelRequest, handler) -> ModelResponse:
    """Choose model based on conversation complexity."""
    message_count = len(request.state["messages"])

    if message_count > 0:
        # Use an advanced model for longer conversations
        model = advanced_model
    else:
        model = basic_model

    return handler(request.override(model=model))

agent = create_agent(
    model=basic_model,  # Default model
    middleware=[dynamic_model_selection],
    tools=[summarize_conversation],
    system_prompt=SystemMessage(
        content=[
            {
                "type": "text",
                "text": "You are an AI assistant tasked with analyzing literary works.",
            },
            {
                "type": "text",
                "text": "<the entire contents of 'Pride and Prejudice'>",
                "cache_control": {"type": "ephemeral"}
            }
        ]
    )
)

input = {"messages": [("user", "分析一下这本书的主题。")]}
input_third = {"messages": [("user", "书中达西先生的性格是如何转变的？。")]}
start_time = time.time()

result = agent.invoke(input) # type: ignore

duration = time.time() - start_time

start_time1 = time.time()

result2 = agent.invoke(input_third) # type: ignore

duration1 = time.time() - start_time1

print(duration)
print(duration1)
print(result)
print(result2)

# s = '《傲慢与偏见》是简·奥斯汀于1813年出版的经典小说，其主题丰富而深刻。让我来分析一下这本书的主要主题：\n\n## 1. 傲慢与偏见\n\n这是最核心的主题，体现在：\n- **达西先生的傲慢**：初见伊丽莎白时表现出的冷漠和高傲\n- **伊丽莎白的偏见**：因达西的傲慢而产生的负面印象，以及威克姆的误导\n- 两人的成长过程就是克服傲慢与偏见的过程\n\n## 2. 婚姻与爱情\n\n小说探讨了不同类型的婚姻观：\n- **伊丽莎白与达西**：基于相互理解、尊重和真爱的婚姻\n- **夏洛特·卢卡斯与柯林斯**：出于经济考虑的实用婚姻\n- **丽迪雅与威克姆**：基于冲动和激情的婚姻\n- **简与宾利**：温柔和谐的婚姻\n\n奥斯汀强调理想的婚姻应该建立在爱情和相互尊重的基础上，而非单纯的经济利益或社会地位。\n\n## 3. 社会阶级与地位\n\n- 19世纪英国的社会等级制度\n- 中产阶级向上流动的渴望（如柯林斯、班纳特夫人）\n- 贵族的傲慢与偏见（如凯瑟琳夫人）\n- 真正的品格与财富、地位的区别\n\n## 4. 个人成长与自我认知\n\n- 伊丽莎白从偏见中觉醒，认识到自己的错误\n- 达西放下傲慢，学会谦逊\n- 通过经历和反思实现人格完善\n\n## 5. 理性与情感\n\n- 伊丽莎白：既有理性判断，又有情感直觉\n- 简：过于善良轻信\n- 丽迪雅：完全受情感支配\n- 奥斯汀主张理性与情感的平衡\n\n## 6. 女性地位\n\n- 当时女性经济依附于男性的现实\n- 班纳特姐妹面临的婚姻压力\n- 伊丽莎白拒绝柯林斯求婚体现了女性的独立意识\n\n## 7. 幽默与讽刺\n\n- 奥斯汀用幽默讽刺社会风俗\n- 班纳特先生、柯林斯先生等人物的讽刺性描写\n- 对社会虚伪和势利的批判\n\n## 总结\n\n《傲慢与偏见》通过一个爱情故事，深刻探讨了人性、社会制度、婚姻观念等多个层面。奥斯汀以幽默讽刺的笔触，展现了18-19世纪英国中产阶级的生活图景，同时传递了关于自我认知、个人成长和真爱的永恒主题。这部小说之所以经典，在于它既反映了特定时代的社会现实，又触及了超越时代的人性真理。'
# s1 = '我来分析一下《傲慢与偏见》中达西先生的性格转变过程。\n\n## 达西先生性格转变的主要阶段\n\n### 1. 初期：傲慢冷漠\n在故事开始时，达西先生表现出明显的**傲慢**：\n- 在麦里屯舞会上拒绝与伊丽莎白跳舞，说她"不够漂亮"\n- 对中产阶级和乡下人表现出优越感\n- 不善于社交，给人留下冷漠、无礼的印象\n\n### 2. 第一次转折：被伊丽莎白拒绝\n当达西第一次向伊丽莎白求婚时，她的严厉拒绝和指责（包括他对威克姆的不公、拆散宾利和简）给了达西极大冲击。这让他开始反思自己的行为和态度。\n\n### 3. 转变过程：自我反省与成长\n达西的转变体现在几个关键事件：\n\n**a) 信件解释**\n- 他写了一封长信给伊丽莎白，详细解释威克姆的真实为人\n- 这显示他愿意澄清误会，也表现出诚实的一面\n\n**b) 救助莉迪亚**\n- 默默帮助解决莉迪亚和威克姆私奔的危机\n- 不求回报，不求名声，纯粹出于对伊丽莎白的关心\n\n**c) 对伊丽莎白家人的态度改变**\n- 开始尊重伊丽莎白的家人，包括她"粗俗"的亲戚\n\n### 4. 后期：谦逊善良\n转变后的达西：\n- 对人更加谦逊有礼\n- 乐于助人，不求回报\n- 学会了平等地对待不同社会阶层的人\n- 真诚地关心伊丽莎白及其家人\n\n## 转变的深层原因\n\n1. **伊丽莎白的影响**：她的智慧和独立精神吸引了达西，也让他意识到自己的傲慢\n2. **真正的爱**：对伊丽莎白的爱让他愿意改变自己\n3. **自我反思**：被拒绝后，他开始认真审视自己的品格和行为\n\n## 总结\n\n达西的转变是从**傲慢的贵族**到**谦逊的绅士**的过程。这个转变不是突然的，而是通过一系列事件和自我反思逐渐完成的。奥斯汀通过达西这个角色，探讨了人如何克服自身的缺陷，成长为更好的人——这正是小说的核心主题之一：**真正的贵族品格不在于出身，而在于品德和行为**。'