"""② 内容撰写智能体（见 work-person-c.md 4.3.2）。

输入：Outline
输出：各章节 Markdown 内容
策略：独立章节并行生成（asyncio.gather），控制每节长度。
"""
from __future__ import annotations

import asyncio
import logging
from typing import List

from ..models.dto import Outline, OutlineSection, SectionContent
from ..services.llm_service import LlmService

logger = logging.getLogger(__name__)


class ContentWriter:
    """内容撰写智能体。"""

    def __init__(self, llm: LlmService) -> None:
        self.llm = llm

    async def write_all(self, outline: Outline, profile: dict) -> List[SectionContent]:
        # 仅对顶层章节并行；子章节并入父章节内容中
        tasks = [
            self._write_section(section, outline.title, profile)
            for section in outline.sections
        ]
        results = await asyncio.gather(*tasks)
        logger.info("内容撰写完成，共 %d 节", len(results))
        return list(results)

    async def _write_section(
        self, section: OutlineSection, doc_title: str, profile: dict
    ) -> SectionContent:
        prompt = (
            "[CONTENT] 请撰写以下章节的详细内容，输出 Markdown。\n"
            f"文档: {doc_title}\n"
            f"章节: {section.title}\n"
            f"章节说明: {section.description or '无'}\n"
            "要求：结构清晰（小标题+要点+示例），控制在 200~400 字。"
        )
        markdown = await self.llm.chat(prompt)
        return SectionContent(title=section.title, order=section.order, markdown=markdown)
