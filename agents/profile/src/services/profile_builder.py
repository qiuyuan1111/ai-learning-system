"""画像构建核心逻辑"""

import json
import os
from typing import List, Optional

from ..models.schema import (
    CognitiveStyle,
    CognitiveStyleDim,
    InterestArea,
    KnowledgeBase,
    KnowledgeLevel,
    LearningPace,
    LearningPaceDim,
    ProfileDimensions,
    TargetDifficulty,
    UserProfile,
    WeaknessPreference,
)
from ..models.dto import ProfileBuildResult
from ..config import settings
from .llm_service import LLMService


def _safe_enum(enum_cls, value, default):
    """安全地将字符串转换为 Enum，无效值时使用默认值"""
    if value is None or not isinstance(value, str):
        return default
    try:
        return enum_cls(value)
    except ValueError:
        return default

# 系统提示词模板 — 优先从文件加载，支持定制
_PROMPT_FILE = os.path.join(os.path.dirname(__file__), "..", "prompts", "build.txt")


def _format_build_prompt(existing_profile: str, missing_dims: str) -> str:
    """加载并格式化画像构建提示词（文件中的 { } 为字面大括号，仅替换已知模板变量）"""
    try:
        with open(_PROMPT_FILE, encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        content = _BUILD_PROMPT_FALLBACK
    return content.replace("{existing_profile}", existing_profile) \
                   .replace("{missing_dims}", missing_dims)


_BUILD_PROMPT_FALLBACK = """你是一个友好的用户画像构建助手。你的任务是通过自然对话了解用户，
构建包含以下 6 个维度的画像：
1. knowledge_base（知识基础）：用户的学历、专业、已掌握技能标签
2. cognitive_style（认知风格）：理论推导型 / 实践应用型 / 视觉图像型 / 语言阅读型
3. learning_pace（学习节奏）：慢 / 中等 / 快
4. weakness_preferences（易错点偏好）：用户觉得自己薄弱的知识点
5. interest_areas（兴趣领域）：用户感兴趣的领域和深度
6. target_difficulty（目标难度等级）：用户希望的学习目标难度 (1-10)

当前已有信息：{existing_profile}
当前缺失维度：{missing_dims}

规则：
- 每次对话最多追问 1-2 个维度
- 问题要自然、友好，像真人聊天而不是填表
- 根据用户回答更新对应的维度信息
- 当你认为某个维度的信息足够时，设置其置信度 >= 0.7

请分析用户的回复，以 JSON 格式返回：
{{
    "extracted": {{  // 本次提取到的维度信息，只包含有更新的维度
        "knowledge_base": {{"level": "beginner|intermediate|advanced", "tags": [...], "confidence": 0.0-1.0}} | null,
        "cognitive_style": {{"style": "theoretical|practical|visual|verbal", "detail": "...", "confidence": 0.0-1.0}} | null,
        "learning_pace": {{"pace": "slow|moderate|fast", "preferred_session_minutes": 30, "confidence": 0.0-1.0}} | null,
        "weakness_preferences": [{{"weak_tags": [...], "description": "...", "confidence": 0.0-1.0}}] | null,
        "interest_areas": [{{"areas": [...], "depth": 1-5, "confidence": 0.0-1.0}}] | null,
        "target_difficulty": {{"level": 1-10, "description": "...", "confidence": 0.0-1.0}} | null
    }},
    "reply": "对用户的回复",  // 友好的回应，接着追问下一个问题
    "is_complete": false  // 是否所有维度都已覆盖且置信度达标
}}
"""


class ProfileBuilder:
    """画像构建服务

    职责：通过多轮对话逐步构建用户画像。
    每次用户发送 profile_build 意图的消息，触发追问-回答循环。
    当画像信息足够丰富（所有维度置信度 > 0.7）时，结束构建。
    """

    def __init__(self, llm_service: LLMService):
        self.llm = llm_service

    async def process_message(
        self,
        session_id: str,
        user_text: str,
        current_profile: Optional[UserProfile],
    ) -> ProfileBuildResult:
        """处理用户的一条消息，返回更新后的画像和回复

        参数:
            session_id: 会话 ID
            user_text: 用户输入的文本
            current_profile: 当前画像（None 表示首次构建）

        返回:
            ProfileBuildResult: 包含更新后的画像和回复信息
        """
        if current_profile is None:
            current_profile = UserProfile(
                session_id=session_id,
                dimensions=ProfileDimensions(),
            )

        # 追加对话原文（控制上限防止无限增长）
        max_dialogue = settings.dialogue_history_size * 2
        current_profile.raw_dialogue.append(f"user: {user_text}")
        if len(current_profile.raw_dialogue) > max_dialogue:
            current_profile.raw_dialogue = current_profile.raw_dialogue[-max_dialogue:]

        # 调用大模型提取画像信息
        result = await self._extract_and_respond(current_profile, user_text)

        # 合并提取到的维度信息
        if result.get("extracted"):
            self._merge_dimensions(current_profile.dimensions, result["extracted"])

        # 追加回复原文（同样控制上限）
        current_profile.raw_dialogue.append(f"assistant: {result.get('reply', '')}")
        if len(current_profile.raw_dialogue) > max_dialogue:
            current_profile.raw_dialogue = current_profile.raw_dialogue[-max_dialogue:]

        # 更新版本号和更新时间
        current_profile.version += 1

        missing = current_profile.dimensions.missing_dimensions()
        is_complete = (
            result.get("is_complete", False)
            and current_profile.dimensions.is_complete(settings.min_confidence)
        )

        return ProfileBuildResult(
            updated_profile=current_profile,
            reply_text=result.get("reply", ""),
            is_complete=is_complete,
            missing_dimensions=missing,
        )

    async def _extract_and_respond(self, profile: UserProfile, user_text: str) -> dict:
        """调用大模型，从用户文本中提取画像信息并生成回复"""
        existing = self._serialize_existing(profile.dimensions)
        missing = profile.dimensions.missing_dimensions()

        profile_text = json.dumps(existing, ensure_ascii=False)
        dims_text = ", ".join(missing) if missing else "无"
        messages = [
            {
                "role": "system",
                "content": _format_build_prompt(profile_text, dims_text),
            },
            {"role": "user", "content": user_text},
        ]

        raw = await self.llm.chat_structured(messages)
        return raw

    def _merge_dimensions(self, dims: ProfileDimensions, extracted: dict) -> None:
        """将大模型提取的维度信息合并到现有画像中"""
        kb = extracted.get("knowledge_base")
        if kb:
            level = _safe_enum(KnowledgeLevel, kb.get("level"), KnowledgeLevel.BEGINNER)
            dims.knowledge_base = KnowledgeBase(
                level=level,
                tags=kb.get("tags", []),
                confidence=kb.get("confidence", 0.5),
            )

        cs = extracted.get("cognitive_style")
        if cs:
            style = _safe_enum(CognitiveStyle, cs.get("style"), CognitiveStyle.VERBAL)
            dims.cognitive_style = CognitiveStyleDim(
                style=style,
                detail=cs.get("detail", ""),
                confidence=cs.get("confidence", 0.5),
            )

        lp = extracted.get("learning_pace")
        if lp:
            pace = _safe_enum(LearningPace, lp.get("pace"), LearningPace.MODERATE)
            dims.learning_pace = LearningPaceDim(
                pace=pace,
                preferred_session_minutes=lp.get("preferred_session_minutes", 30),
                confidence=lp.get("confidence", 0.5),
            )

        wp_list = extracted.get("weakness_preferences")
        if wp_list:
            items = wp_list if isinstance(wp_list, list) else [wp_list]
            dims.weakness_preferences = [
                WeaknessPreference(
                    weak_tags=w.get("weak_tags", []),
                    description=w.get("description", ""),
                    confidence=w.get("confidence", 0.5),
                )
                for w in items
            ]

        ia_list = extracted.get("interest_areas")
        if ia_list:
            items = ia_list if isinstance(ia_list, list) else [ia_list]
            dims.interest_areas = [
                InterestArea(
                    areas=ia.get("areas", []),
                    depth=ia.get("depth", 3),
                    confidence=ia.get("confidence", 0.5),
                )
                for ia in items
            ]

        td = extracted.get("target_difficulty")
        if td:
            dims.target_difficulty = TargetDifficulty(
                level=td.get("level", 5),
                description=td.get("description", ""),
                confidence=td.get("confidence", 0.5),
            )

    def _serialize_existing(self, dims: ProfileDimensions) -> dict:
        """将现有维度序列化为 JSON 兼容 dict，用于填入提示词"""
        return json.loads(dims.model_dump_json(exclude_none=True))
