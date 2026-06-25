"""① 大纲生成智能体（见 work-person-c.md 4.3.1）。

输入：用户需求 + 用户画像
输出：Outline 结构（章节树）
策略：根据画像调整章节深度/侧重，薄弱点加章节，兴趣点加案例章节。
"""
from __future__ import annotations

import logging
from typing import Optional

from ..models.dto import Outline
from ..services.llm_service import LlmService

logger = logging.getLogger(__name__)


class OutlineGenerator:
    """大纲生成智能体。"""

    def __init__(self, llm: LlmService) -> None:
        self.llm = llm

    async def generate(self, user_request: str, profile: Optional[dict]) -> Outline:
        prompt = self._build_prompt(user_request, profile or {})
        raw = await self.llm.chat_json(prompt)
        outline = Outline.model_validate(raw)
        logger.info("大纲生成完成：%s，共 %d 章", outline.title, len(outline.sections))
        return outline

    def _build_prompt(self, user_request: str, profile: dict) -> str:
        dims = profile.get("dimensions", {}) if isinstance(profile, dict) else {}
        kb = dims.get("knowledgeBase") or {}
        weak = dims.get("weaknessPreferences") or []
        interest = dims.get("interestAreas") or []
        target = dims.get("targetDifficulty") or {}

        weak_tags = []
        for w in weak:
            weak_tags.extend(w.get("weakTags", []))
        interest_areas = []
        for i in interest:
            interest_areas.extend(i.get("areas", []))

        return (
            "[OUTLINE] 你是一个教学大纲设计专家。请输出 JSON。\n"
            f"用户需求: {user_request}\n"
            f"知识水平: {kb.get('level', '未知')}（已掌握: {kb.get('tags', [])}）\n"
            f"薄弱知识点: {weak_tags}\n"
            f"兴趣领域: {interest_areas}\n"
            f"目标难度: {target.get('level', '适中')}/10\n"
            "输出格式（JSON）: { \"title\": str, \"sections\": [ "
            "{ \"order\": int, \"title\": str, \"description\": str, "
            "\"estimatedMinutes\": int, \"subsections\": [...] } ] }\n"
            "设计原则：从基础到高级递进；薄弱点处增加练习章节；穿插兴趣领域案例。"
        )
