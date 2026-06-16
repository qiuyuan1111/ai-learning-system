"""
辅导引擎核心

接收用户的辅导请求（intent=tutoring），结合画像生成个性化回答。
支持多模态输入（图片/附件），输出图文混合 Markdown。
"""

import logging
import os
import re
from typing import Any, AsyncGenerator, Dict, List, Optional

import aiofiles

from src.config import config
from src.models.dto import Attachment, TutorRequest
from src.models.context import DialogueContext
from src.services.llm_service import LLMService
from src.services.answer_generator import AnswerGenerator
from src.services.context_manager import ContextManager

logger = logging.getLogger(__name__)

# 提示词模板路径（相对于项目根目录）
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_SYSTEM_PROMPT_PATH = os.path.join(_PROJECT_ROOT, "prompts", "system.txt")
_ADAPT_PROMPT_PATH = os.path.join(_PROJECT_ROOT, "prompts", "adapt.txt")


class TutorEngine:
    """
    辅导引擎

    职责：
    接收用户的辅导请求（intent=tutoring），结合画像生成个性化回答。
    支持多模态输入（图片/附件），输出图文混合 Markdown。

    核心策略：
    1. 根据画像中的 knowledge_base 调整回答深度
    2. 根据 cognitive_style 调整呈现方式（理论推导/代码示例/图解）
    3. 根据 learning_pace 调整语速和信息密度
    4. 关联 weakness_preferences 对薄弱点着重讲解
    5. 关联 interest_areas 使用用户感兴趣的例子
    """

    def __init__(
        self,
        llm_service: LLMService,
        profile_service: "ProfileServiceClient",
        answer_generator: AnswerGenerator,
        context_manager: ContextManager,
    ):
        self.llm = llm_service
        self.profile_service = profile_service
        self.answer_generator = answer_generator
        self.context_manager = context_manager

        # 缓存已加载的提示词模板
        self._system_template: Optional[str] = None
        self._adapt_template: Optional[str] = None

    async def generate_answer(
        self,
        session_id: str,
        question: str,
        attachments: List[Attachment],
        resource_id: Optional[str] = None,
        course_id: Optional[str] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        生成个性化辅导回答

        参数:
            session_id: 会话 ID（用于获取画像和上下文）
            question: 用户问题
            attachments: 附件列表（图片等）
            resource_id: 可选的资源 ID
            course_id: 可选的课程 ID

        生成（yield）:
            逐步输出 type=text 流式消息
            最终输出 type=done 结束

        实现步骤:
        1. 从 profile_service 获取当前画像
        2. 根据画像构建系统提示词（注入画像维度信息）
        3. 从 context_manager 获取对话历史
        4. 调用 llm.chat_stream() 生成回答
        5. 将回答通过 WS 逐段推送给前端
        6. 保存对话到上下文
        """
        try:
            # 1. 加载模板
            system_template = await self._load_system_template()
            adapt_template = await self._load_adapt_template()

            # 2. 获取画像
            profile = None
            try:
                profile = await self.profile_service.get_profile(session_id)
            except Exception as e:
                logger.warning("获取画像失败，使用默认设置: %s", e)

            # 3. 构建系统提示词（含画像适配）
            system_prompt = self._build_system_prompt(
                system_template, adapt_template, profile,
            )

            # 4. 获取对话上下文
            context = await self.context_manager.get_context(session_id)

            # 5. 构建消息列表
            messages = self.context_manager.build_messages_for_llm(
                system_prompt, question, context,
            )

            # 6. 流式生成回答
            full_answer = ""
            async for chunk in self.answer_generator.generate_stream(
                system_prompt, messages, question, attachments,
            ):
                if chunk["type"] == "text":
                    full_answer += chunk["content"]["markdown"]
                yield chunk

            # 7. 保存对话
            await self.context_manager.append_round(
                session_id=session_id,
                question=question,
                answer=full_answer,
                resource_id=resource_id,
                course_id=course_id,
            )

        except Exception as e:
            logger.exception("辅导引擎生成回答失败")
            yield {
                "type": "error",
                "content": {
                    "code": "TUTOR_ENGINE_ERROR",
                    "message": "生成回答时出现错误，请稍后重试。",
                },
            }

    def _build_system_prompt(
        self,
        system_template: str,
        adapt_template: str,
        profile: Optional[Dict[str, Any]],
    ) -> str:
        """
        根据画像和上下文构建系统提示词

        将适配提示词注入到系统提示词的 {{ ADAPT_PROMPT }} 占位符处。
        如果 profile 为空，使用默认（空）适配提示词。

        例如:
        - 用户知识水平=intermediate → "使用中等难度的术语解释"
        - 认知风格=practical → "多提供代码示例和实际应用场景"
        - 薄弱点包含"注意力机制" → "对注意力机制部分重点讲解"
        """
        if profile:
            adapt_content = self._render_adapt_prompt(adapt_template, profile)
        else:
            adapt_content = "（暂无用户画像信息，请按默认方式回答。）"

        system_prompt = system_template.replace("{{ ADAPT_PROMPT }}", adapt_content)
        return system_prompt

    def _render_adapt_prompt(
        self,
        adapt_template: str,
        profile: Dict[str, Any],
    ) -> str:
        """
        渲染画像适配提示词

        将 profile 中的维度数据填充到 adapt.txt 模板中。
        """
        dimensions = profile.get("dimensions", profile)

        # 安全获取维度值
        knowledge_base = dimensions.get("knowledge_base", {})
        cognitive_style = dimensions.get("cognitive_style", {})
        learning_pace = dimensions.get("learning_pace", {})
        weakness_prefs = dimensions.get("weakness_preferences", [])
        interest_areas = dimensions.get("interest_areas", [])

        result = adapt_template

        # 知识水平
        level = knowledge_base.get("level", "intermediate") if knowledge_base else "intermediate"
        result = result.replace("{{ knowledge_level }}", str(level))

        # 认知风格
        style = cognitive_style.get("style", "practical") if cognitive_style else "practical"
        result = result.replace("{{ cognitive_style }}", str(style))

        # 学习节奏
        pace = learning_pace.get("pace", "moderate") if learning_pace else "moderate"
        result = result.replace("{{ learning_pace }}", str(pace))

        # 薄弱知识点
        weak_items = []
        for w in weakness_prefs:
            if isinstance(w, dict):
                tags = w.get("weak_tags", [])
                desc = w.get("description", "")
                item = ", ".join(tags) if tags else desc
                if item:
                    weak_items.append(item)
            elif isinstance(w, str):
                weak_items.append(w)

        if weak_items:
            weak_section = "\n".join(f"- {item}" for item in weak_items)
        else:
            weak_section = "（暂无特别薄弱的领域）"

        result = self._replace_for_block(
            result,
            "weakness_preferences",
            weak_section,
        )

        # 兴趣领域
        interest_items = []
        for area in interest_areas:
            if isinstance(area, dict):
                areas = area.get("areas", [])
                interest_items.extend(areas)
            elif isinstance(area, str):
                interest_items.append(area)

        if interest_items:
            interest_section = "\n".join(f"- {item}" for item in interest_items)
        else:
            interest_section = "（暂无特别兴趣记录）"

        result = self._replace_for_block(
            result,
            "interest_areas",
            interest_section,
        )

        return result

    async def _load_system_template(self) -> str:
        """加载系统提示词模板（带缓存）"""
        if self._system_template is None:
            try:
                async with aiofiles.open(_SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as f:
                    self._system_template = await f.read()
            except FileNotFoundError:
                self._system_template = self._default_system_prompt()
        return self._system_template

    async def _load_adapt_template(self) -> str:
        """加载画像适配提示词模板（带缓存）"""
        if self._adapt_template is None:
            try:
                async with aiofiles.open(_ADAPT_PROMPT_PATH, "r", encoding="utf-8") as f:
                    self._adapt_template = await f.read()
            except FileNotFoundError:
                self._adapt_template = self._default_adapt_prompt()
        return self._adapt_template

    @staticmethod
    def _default_system_prompt() -> str:
        return (
            "你是一位温柔耐心的AI辅导老师。用中文与学生交流，"
            "引导学生自己思考。使用 Markdown 格式排版。\n\n"
            "{{ ADAPT_PROMPT }}"
        )

    @staticmethod
    def _default_adapt_prompt() -> str:
        return "请根据学生的知识水平和学习风格调整回答方式。"

    @staticmethod
    def _replace_for_block(template: str, var_name: str, replacement: str) -> str:
        """
        替换模板中的 {% for ... %} 块

        搜索 `{% for ___ in var_name %}` 到 `{% endfor %}` 之间的内容并替换。
        使用正则匹配，支持跨行内容。
        """
        pattern = re.compile(
            r"\{% for \w+ in " + re.escape(var_name) + r" %\}[\s\S]*?\{% endfor %\}",
        )
        return pattern.sub(replacement, template)
