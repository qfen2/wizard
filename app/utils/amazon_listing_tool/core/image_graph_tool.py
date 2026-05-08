import os
import re
import json
import uuid
import base64
from pathlib import Path
from typing import TypedDict, Optional, List, Dict, Any, Literal

from openai import OpenAI
from pydantic import BaseModel, Field

from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END


# =========================
# 1. 数据结构
# =========================

ImageIntent = Literal[
    "generate",          # 文生图
    "edit",              # 基于图片编辑
    "analyze",           # 图片分析
    "product_pack",      # 一组商品图
    "variants",          # 多变体
    "unknown"
]

# 定义生图流程状态
class ImageWorkflowState(TypedDict, total=False):
    user_request: str
    image_path: Optional[str]

    intent: ImageIntent
    product_name: Optional[str]
    platform: Optional[str]
    image_type: Optional[str]

    prompt: Optional[str]
    optimized_prompt: Optional[str]
    analysis: Optional[str]

    tasks: List[Dict[str, Any]]
    results: List[Dict[str, Any]]

    size: str
    quality: str
    output_dir: str

    error: Optional[str]

# 定义生图任务字段
class ImageTask(BaseModel):
    name: str = Field(description="任务名称，例如 amazon_main、lifestyle、ad_image")
    mode: Literal["generate", "edit", "analyze"] = Field(description="任务类型")
    prompt: str = Field(description="完整图片提示词或编辑指令")
    image_type: Optional[str] = Field(default=None, description="main/lifestyle/detail/ad/social 等")
    size: Optional[str] = Field(default="1024x1024")
    quality: Optional[str] = Field(default="high")


class PlannedTasks(BaseModel):
    intent: ImageIntent
    product_name: Optional[str] = None
    platform: Optional[str] = "Amazon"
    tasks: List[ImageTask]


# =========================
# 2. 底层 OpenAI 图片客户端
# =========================

class OpenAIImageClient:
    """
    底层图片能力：
    - generate: Image API 文生图
    - edit: Image API 图片编辑
    - analyze: 视觉理解
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        image_model: str = "gpt-image-2",
        vision_model: str = "gpt-5.5",
        output_dir: str = "generated_images",
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("未找到 OPENAI_API_KEY，请传入 api_key 或设置环境变量。")

        self.client = OpenAI(api_key=self.api_key)
        self.image_model = image_model
        self.vision_model = vision_model
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _default_path(self, prefix: str = "img", ext: str = ".png") -> str:
        return str(self.output_dir / f"{prefix}_{uuid.uuid4().hex}{ext}")

    def _save_b64(self, b64_data: str, output_path: Optional[str] = None) -> str:
        output_path = output_path or self._default_path()
        Path(output_path).write_bytes(base64.b64decode(b64_data))
        return output_path

    def _image_to_data_url(self, image_path: str) -> str:
        ext = Path(image_path).suffix.lower().replace(".", "")
        if ext == "jpg":
            ext = "jpeg"
        if ext not in {"png", "jpeg", "webp", "gif"}:
            ext = "png"

        with open(image_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")

        return f"data:image/{ext};base64,{b64}"

    def generate(
        self,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "high",
        output_path: Optional[str] = None,
        prefix: str = "generate",
    ) -> Dict[str, Any]:
        """
        文生图。
        """
        response = self.client.images.generate(
            model=self.image_model,
            prompt=prompt,
            size=size, # type: ignore
            quality=quality, # type: ignore
            n=1,
        )

        image_path = self._save_b64(
            response.data[0].b64_json,
            output_path or self._default_path(prefix=prefix)
        )

        return {
            "success": True,
            "mode": "generate",
            "image_path": image_path,
            "prompt": prompt,
            "size": size,
            "quality": quality,
        }

    def edit(
        self,
        image_path: str,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "high",
        output_path: Optional[str] = None,
        prefix: str = "edit",
    ) -> Dict[str, Any]:
        """
        基于已有图片编辑。
        可用于换背景、重绘场景、增强质感、广告化、风格化、详情图改造等。
        """
        with open(image_path, "rb") as img:
            response = self.client.images.edit(
                model=self.image_model,
                image=img,
                prompt=prompt,
                size=size,
                quality=quality,
            )

        saved_path = self._save_b64(
            response.data[0].b64_json,
            output_path or self._default_path(prefix=prefix)
        )

        return {
            "success": True,
            "mode": "edit",
            "source_image": image_path,
            "image_path": saved_path,
            "prompt": prompt,
            "size": size,
            "quality": quality,
        }

    def analyze(
        self,
        image_path: str,
        question: str,
    ) -> str:
        """
        图片理解/分析。
        """
        image_url = self._image_to_data_url(image_path)

        response = self.client.responses.create(
            model=self.vision_model,
            input=[ # type: ignore
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": question},
                        {"type": "input_image", "image_url": image_url},
                    ],
                }
            ],
        )

        return response.output_text.strip()

# =========================
# 3. LangChain Tools 工厂
# =========================

class ImageToolFactory:
    def __init__(self, image_client: OpenAIImageClient):
        self.image_client = image_client

    def build_tools(self):
        image_client = self.image_client

        @tool
        def generate_image_tool(
            prompt: str,
            size: str = "1024x1024",
            quality: str = "high",
        ) -> str:
            """
            根据文本 prompt 生成图片，返回 JSON 字符串。
            """
            result = image_client.generate(
                prompt=prompt,
                size=size,
                quality=quality,
            )
            return json.dumps(result, ensure_ascii=False)

        @tool
        def edit_image_tool(
            image_path: str,
            prompt: str,
            size: str = "1024x1024",
            quality: str = "high",
        ) -> str:
            """
            根据已有图片和编辑指令生成新图片，返回 JSON 字符串。
            """
            result = image_client.edit(
                image_path=image_path,
                prompt=prompt,
                size=size,
                quality=quality,
            )
            return json.dumps(result, ensure_ascii=False)

        @tool
        def analyze_image_tool(
            image_path: str,
            question: str = "请分析这张图片的主体、场景、光线、构图、风格和可用于电商图片生成的要点。",
        ) -> str:
            """
            分析图片内容。
            """
            return image_client.analyze(
                image_path=image_path,
                question=question,
            )

        return [generate_image_tool, edit_image_tool, analyze_image_tool]

# =========================
# 4. LangGraph 主工具类
# =========================

class LangGraphImageTool:
    """
    基于 LangChain + LangGraph 的增强版图片工具类。

    支持：
    - 单张文生图
    - 单张图片编辑
    - 图片分析
    - 商品图片组生成
    - 多变体生成
    - 自然语言自动规划任务
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        image_model: str = "gpt-image-2",
        llm_model: str = "gpt-5.5",
        output_dir: str = "generated_images",
    ):
        self.output_dir = output_dir

        self.image_client = OpenAIImageClient(
            api_key=api_key,
            image_model=image_model,
            vision_model=llm_model,
            output_dir=output_dir,
        )

        self.llm = ChatOpenAI(
            model=llm_model,
            temperature=0.2,
            api_key=api_key or os.getenv("OPENAI_API_KEY"),
        )

        self.planner_llm = self.llm.with_structured_output(PlannedTasks)

        self.tools = ImageToolFactory(self.image_client).build_tools()
        self.graph = self._build_graph()

    # -------------------------
    # Prompt 构造
    # -------------------------

    def _build_product_prompt(
        self,
        product_name: str,
        image_type: str,
        scene: str,
        platform: str = "Amazon",
    ) -> str:
        type_map = {
            "main": "电商主图，主体突出，背景干净，适合 Listing 首图。",
            "lifestyle": "生活方式场景图，强调真实使用场景和代入感。",
            "detail": "细节图，突出材质、结构、卖点和做工。",
            "ad": "广告图，视觉冲击力更强，适合投放和活动宣传。",
            "social": "社媒图，更有氛围感，适合 Instagram、TikTok、小红书等平台。",
        }

        return f"""
你是专业跨境电商视觉设计师。

请生成一张高质量商品图片。

产品：{product_name}
平台：{platform}
图片类型：{image_type}
图片目标：{type_map.get(image_type, "高质量商业商品图")}
场景：{scene}

要求：
- 商品必须是画面主体
- 构图干净，重点明确
- 真实商业摄影质感
- 光线自然，材质清晰
- 背景服务于商品表达
- 不要无关文字、水印、二维码、logo
- 可用于商品页、详情页、广告图或社交媒体推广
        """.strip()

    # -------------------------
    # LangGraph 节点
    # -------------------------

    def _detect_intent_node(self, state: ImageWorkflowState) -> ImageWorkflowState:
        """
        识别用户需求类型。
        """
        user_request = state["user_request"]
        has_image = bool(state.get("image_path"))

        prompt = f"""
请判断用户的图片需求意图。

可选 intent：
- generate：纯文生图
- edit：用户提供了图片，并要求改图、优化、重绘、风格化、换场景等
- analyze：用户主要想分析图片
- product_pack：用户想为一个商品生成一组图片，例如主图、详情图、广告图、社媒图
- variants：用户想生成多个风格变体
- unknown：无法判断

用户是否提供图片：{has_image}
用户需求：
{user_request}

只返回一个 intent 字符串。
        """.strip()

        result = self.llm.invoke(prompt).content.strip().lower()
        result = re.sub(r"[^a-z_]", "", result)

        allowed = {"generate", "edit", "analyze", "product_pack", "variants", "unknown"}
        intent = result if result in allowed else "unknown"

        return {
            **state,
            "intent": intent,
        }

    def _plan_node(self, state: ImageWorkflowState) -> ImageWorkflowState:
        """
        规划任务。
        """
        user_request = state["user_request"]
        image_path = state.get("image_path")
        intent = state.get("intent", "unknown")

        planning_prompt = f"""
你是一个电商 AI 图片生产任务规划器。

请根据用户需求规划图片任务。

规则：
1. 如果用户要求生成一组商品图，规划 main、lifestyle、detail、ad/social 等任务
2. 如果用户提供了 image_path，并要求改造图片，任务 mode 应该是 edit
3. 如果用户只是要求分析图片，任务 mode 应该是 analyze
4. 如果用户要求多个版本，规划多个 generate 或 edit 任务
5. 每个任务的 prompt 必须完整、具体、可直接用于图片生成或编辑
6. 不要要求模型生成品牌 logo、二维码、水印或大量文字

已识别 intent：{intent}
是否有原图：{bool(image_path)}
用户需求：
{user_request}
        """.strip()

        try:
            planned = self.planner_llm.invoke(planning_prompt)

            tasks = []
            for task in planned.tasks:
                task_dict = task.model_dump()
                if image_path and task_dict["mode"] == "edit":
                    task_dict["image_path"] = image_path
                tasks.append(task_dict)

            return {
                **state,
                "intent": planned.intent or intent,
                "product_name": planned.product_name,
                "platform": planned.platform,
                "tasks": tasks,
            }

        except Exception as e:
            return {
                **state,
                "error": f"任务规划失败：{str(e)}",
                "tasks": [],
            }

    def _optimize_prompt_node(self, state: ImageWorkflowState) -> ImageWorkflowState:
        """
        对所有任务 prompt 做优化。
        """
        tasks = state.get("tasks", [])

        optimized_tasks = []
        for task in tasks:
            raw_prompt = task.get("prompt", "")

            optimize_prompt = f"""
请将下面的图片生成/编辑提示词优化为更专业的商业图片 prompt。

要求：
- 保留用户核心意图
- 强化主体、构图、光线、色彩、质感、场景
- 适合电商商品图、广告图或社媒素材
- 避免水印、二维码、乱码文字、无关 logo
- 直接输出优化后的 prompt，不要解释

原始 prompt：
{raw_prompt}
            """.strip()

            try:
                optimized = self.llm.invoke(optimize_prompt).content.strip()
            except Exception:
                optimized = raw_prompt

            task["prompt"] = optimized
            optimized_tasks.append(task)

        return {
            **state,
            "tasks": optimized_tasks,
        }

    def _execute_node(self, state: ImageWorkflowState) -> ImageWorkflowState:
        """
        执行图片任务。
        """
        tasks = state.get("tasks", [])
        results = []

        for index, task in enumerate(tasks, start=1):
            name = task.get("name", f"task_{index}")
            mode = task.get("mode", "generate")
            prompt = task.get("prompt", "")
            size = task.get("size") or state.get("size", "1024x1024")
            quality = task.get("quality") or state.get("quality", "high")

            try:
                if mode == "generate":
                    result = self.image_client.generate(
                        prompt=prompt,
                        size=size,
                        quality=quality,
                        prefix=name,
                    )

                elif mode == "edit":
                    image_path = task.get("image_path") or state.get("image_path")
                    if not image_path:
                        raise ValueError("edit 任务缺少 image_path")

                    result = self.image_client.edit(
                        image_path=image_path,
                        prompt=prompt,
                        size=size,
                        quality=quality,
                        prefix=name,
                    )

                elif mode == "analyze":
                    image_path = task.get("image_path") or state.get("image_path")
                    if not image_path:
                        raise ValueError("analyze 任务缺少 image_path")

                    analysis = self.image_client.analyze(
                        image_path=image_path,
                        question=prompt,
                    )
                    result = {
                        "success": True,
                        "mode": "analyze",
                        "analysis": analysis,
                        "source_image": image_path,
                    }

                else:
                    result = {
                        "success": False,
                        "mode": mode,
                        "error": f"不支持的任务模式：{mode}",
                    }

                result["task_name"] = name
                results.append(result)

            except Exception as e:
                results.append({
                    "success": False,
                    "task_name": name,
                    "mode": mode,
                    "error": str(e),
                })

        return {
            **state,
            "results": results,
        }

    def _summarize_node(self, state: ImageWorkflowState) -> ImageWorkflowState:
        """
        简单汇总。
        """
        results = state.get("results", [])
        success_count = sum(1 for r in results if r.get("success"))

        summary = {
            "success_count": success_count,
            "total": len(results),
            "image_paths": [
                r.get("image_path")
                for r in results
                if r.get("image_path")
            ],
        }

        return {
            **state,
            "summary": summary,
        }

    def _route_after_intent(self, state: ImageWorkflowState) -> str:
        """
        简单路由。
        """
        if state.get("error"):
            return "summarize"

        return "plan"

    def _build_graph(self):
        """
        构建 LangGraph 工作流。
        """
        graph = StateGraph(ImageWorkflowState)

        graph.add_node("detect_intent", self._detect_intent_node)
        graph.add_node("plan", self._plan_node)
        graph.add_node("optimize_prompt", self._optimize_prompt_node)
        graph.add_node("execute", self._execute_node)
        graph.add_node("summarize", self._summarize_node)

        graph.add_edge(START, "detect_intent")
        graph.add_conditional_edges(
            "detect_intent",
            self._route_after_intent,
            {
                "plan": "plan",
                "summarize": "summarize",
            }
        )
        graph.add_edge("plan", "optimize_prompt")
        graph.add_edge("optimize_prompt", "execute")
        graph.add_edge("execute", "summarize")
        graph.add_edge("summarize", END)

        return graph.compile()

    # -------------------------
    # 对外调用入口
    # -------------------------

    def invoke(
        self,
        user_request: str,
        image_path: Optional[str] = None,
        size: str = "1024x1024",
        quality: str = "high",
    ) -> ImageWorkflowState:
        """
        自然语言入口。
        """
        init_state: ImageWorkflowState = {
            "user_request": user_request,
            "image_path": image_path,
            "size": size,
            "quality": quality,
            "output_dir": self.output_dir,
            "tasks": [],
            "results": [],
        }

        return self.graph.invoke(init_state)  # type: ignore

    def generate_one(
        self,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "high",
    ) -> Dict[str, Any]:
        """
        直接生成单张图，不走复杂规划。
        """
        return self.image_client.generate(
            prompt=prompt,
            size=size,
            quality=quality,
        )

    def edit_one(
        self,
        image_path: str,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "high",
    ) -> Dict[str, Any]:
        """
        直接编辑单张图，不走复杂规划。
        """
        return self.image_client.edit(
            image_path=image_path,
            prompt=prompt,
            size=size,
            quality=quality,
        )

    def analyze_one(
        self,
        image_path: str,
        question: str,
    ) -> str:
        """
        直接分析单张图。
        """
        return self.image_client.analyze(
            image_path=image_path,
            question=question,
        )