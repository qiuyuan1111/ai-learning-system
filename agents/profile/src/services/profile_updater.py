"""画像增量更新服务"""

import json
import logging
import os
from typing import Any, Dict, List

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
from ..config import settings
from .llm_service import LLMService

logger = logging.getLogger(__name__)


def _safe_enum(enum_cls, value, default):
    """安全地将字符串转换为 Enum，无效值时使用默认值"""
    if value is None or not isinstance(value, str):
        return default
    try:
        return enum_cls(value)
    except ValueError:
        return default


_UPDATE_PROMPT_FILE = os.path.join(os.path.dirname(__file__), "..", "prompts", "update.txt")


def _format_update_prompt(current_profile: str, source_type: str, source_content: str) -> str:
    """加载并格式化更新提示词（文件中的 { } 为字面大括号，仅替换已知模板变量）"""
    try:
        with open(_UPDATE_PROMPT_FILE, encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        content = _UPDATE_PROMPT_FALLBACK
    return content.replace("{current_profile}", current_profile) \
                   .replace("{source_type}", source_type) \
                   .replace("{source_content}", source_content)


_UPDATE_PROMPT_FALLBACK = """你是一个画像更新分析助手。根据用户的对话历史或评估结果，
分析哪些画像维度需要更新。

当前画像：{current_profile}
更新来源：{source_type}  （dialogue / evaluation）
来源内容：{source_content}

请分析并返回 JSON：
{{
    "should_update": true|false,
    "updates": {{  // 需要更新的维度（仅包含有变化的字段）
        "knowledge_base": {{"level": "...", "tags": [...], "confidence": 0.0-1.0}} | null,
        "cognitive_style": {{"style": "...", "detail": "...", "confidence": 0.0-1.0}} | null,
        "learning_pace": {{"pace": "...", "preferred_session_minutes": ..., "confidence": 0.0-1.0}} | null,
        "weakness_preferences": [{{"weak_tags": [...], "description": "...", "confidence": 0.0-1.0}}] | null,
        "interest_areas": [{{"areas": [...], "depth": 1-5, "confidence": 0.0-1.0}}] | null,
        "target_difficulty": {{"level": 1-10, "description": "...", "confidence": 0.0-1.0}} | null
    }},
    "reason": "为什么要更新这些维度"
}}
"""


class ProfileUpdater:
    """画像增量更新服务

    职责：在学习过程中，根据用户行为（问答、做题、资源观看）动态更新画像。
    触发时机:
    1. tutoring 对话中提取新的画像信息
    2. evaluate 结果回写到画像
    3. 用户主动补充信息
    """

    def __init__(self, llm_service: LLMService):
        self.llm = llm_service

    async def update_from_dialogue(
        self,
        session_id: str,
        dialogue_history: List[Dict[str, Any]],
        current_profile: UserProfile,
    ) -> UserProfile:
        """从对话中提取画像更新信息

        参数:
            dialogue_history: 最近 N 轮对话
            current_profile: 当前画像

        返回: 更新后的画像
        """
        profile_json = json.loads(current_profile.dimensions.model_dump_json(exclude_none=True))
        dialogue_text = json.dumps(dialogue_history, ensure_ascii=False, indent=2)

        messages = [
            {
                "role": "system",
                "content": _format_update_prompt(
                    current_profile=json.dumps(profile_json, ensure_ascii=False),
                    source_type="dialogue",
                    source_content=dialogue_text,
                ),
            }
        ]

        try:
            result = await self.llm.chat_structured(messages)
        except Exception as e:  # noqa: BLE001  LLM 调用失败不阻断主流程
            logger.warning("画像更新（dialogue）LLM 调用失败，跳过本次更新: %s", e)
            return current_profile
        if result.get("should_update") and result.get("updates"):
            self._merge_updates(current_profile.dimensions, result["updates"])
            current_profile.version += 1

        return current_profile

    async def update_from_evaluation(
        self,
        session_id: str,
        evaluation_result: Dict[str, Any],
        current_profile: UserProfile,
    ) -> UserProfile:
        """从评估结果更新画像

        例如: 评估发现用户"注意力机制"薄弱
        → weakness_preferences 增加 "Attention"
        → knowledge_base 相应调整
        """
        profile_json = json.loads(current_profile.dimensions.model_dump_json(exclude_none=True))
        eval_text = json.dumps(evaluation_result, ensure_ascii=False, indent=2)

        messages = [
            {
                "role": "system",
                "content": _format_update_prompt(
                    current_profile=json.dumps(profile_json, ensure_ascii=False),
                    source_type="evaluation",
                    source_content=eval_text,
                ),
            }
        ]

        try:
            result = await self.llm.chat_structured(messages)
        except Exception as e:  # noqa: BLE001  LLM 调用失败不阻断主流程
            logger.warning("画像更新（evaluation）LLM 调用失败，跳过本次更新: %s", e)
            return current_profile
        if result.get("should_update") and result.get("updates"):
            self._merge_updates(current_profile.dimensions, result["updates"])
            current_profile.version += 1

        return current_profile

    def _merge_updates(self, dims: ProfileDimensions, updates: dict) -> None:
        """将分析结果合并到现有维度"""
        kb = updates.get("knowledge_base")
        if kb:
            prev = dims.knowledge_base
            dims.knowledge_base = KnowledgeBase(
                level=_safe_enum(KnowledgeLevel, kb.get("level"), prev.level if prev else KnowledgeLevel.BEGINNER),
                tags=kb.get("tags", prev.tags if prev else []),
                confidence=kb.get("confidence", prev.confidence if prev else 0.5),
            )

        cs = updates.get("cognitive_style")
        if cs:
            prev = dims.cognitive_style
            dims.cognitive_style = CognitiveStyleDim(
                style=_safe_enum(CognitiveStyle, cs.get("style"), prev.style if prev else CognitiveStyle.VERBAL),
                detail=cs.get("detail", prev.detail if prev else ""),
                confidence=cs.get("confidence", prev.confidence if prev else 0.5),
            )

        lp = updates.get("learning_pace")
        if lp:
            prev = dims.learning_pace
            dims.learning_pace = LearningPaceDim(
                pace=_safe_enum(LearningPace, lp.get("pace"), prev.pace if prev else LearningPace.MODERATE),
                preferred_session_minutes=lp.get(
                    "preferred_session_minutes",
                    prev.preferred_session_minutes if prev else 30,
                ),
                confidence=lp.get("confidence", prev.confidence if prev else 0.5),
            )

        wp_list = updates.get("weakness_preferences")
        if wp_list:
            items = wp_list if isinstance(wp_list, list) else [wp_list]
            existing_tags = {t for w in dims.weakness_preferences for t in w.weak_tags}
            new_weaknesses = [
                WeaknessPreference(
                    weak_tags=w.get("weak_tags", []),
                    description=w.get("description", ""),
                    confidence=w.get("confidence", 0.5),
                )
                for w in items
                if any(t not in existing_tags for t in w.get("weak_tags", []))
            ]
            dims.weakness_preferences.extend(new_weaknesses)

        ia_list = updates.get("interest_areas")
        if ia_list:
            items = ia_list if isinstance(ia_list, list) else [ia_list]
            existing_areas = {a for ia in dims.interest_areas for a in ia.areas}
            new_areas = [
                InterestArea(
                    areas=ia.get("areas", []),
                    depth=ia.get("depth", 3),
                    confidence=ia.get("confidence", 0.5),
                )
                for ia in items
                if any(a not in existing_areas for a in ia.get("areas", []))
            ]
            dims.interest_areas.extend(new_areas)

        td = updates.get("target_difficulty")
        if td:
            dims.target_difficulty = TargetDifficulty(
                level=td.get("level", 5),
                description=td.get("description", ""),
                confidence=td.get("confidence", 0.5),
            )
