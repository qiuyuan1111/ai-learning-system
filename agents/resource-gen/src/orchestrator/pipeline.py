"""编排管线核心（见 work-person-c.md 4.2）。

5 阶段串行：
    ①大纲(10%) → ②内容(30%) → ③PPT编排(55%) → ④渲染(75%) → ⑤审核(90%) → 完成(100%)
每阶段更新 task 进度并经 WS 通知。
"""
from __future__ import annotations

import asyncio
import logging
import os
import re
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from ai_edu_common import Resource
from ai_edu_common.enums import ErrorCodeEnum, ResourceTypeEnum

from ..config import settings
from ..models.dto import GenerationRequest, Outline
from .content_writer import ContentWriter
from .doc_renderer import DocRenderer
from .outline_generator import OutlineGenerator
from .ppt_renderer import PptRenderer
from .review_checker import ReviewChecker

if TYPE_CHECKING:
    from ..task.manager import TaskManager

logger = logging.getLogger(__name__)


class ResourceGenerationPipeline:
    """资源生成编排管线。"""

    def __init__(
        self,
        task_manager: "TaskManager",
        outline_generator: OutlineGenerator,
        content_writer: ContentWriter,
        ppt_renderer: PptRenderer,
        doc_renderer: DocRenderer,
        review_checker: ReviewChecker,
    ) -> None:
        self.task_manager = task_manager
        self.outline_gen = outline_generator
        self.content_writer = content_writer
        self.ppt_renderer = ppt_renderer
        self.doc_renderer = doc_renderer
        self.review = review_checker

    async def execute(
        self,
        *,
        task_id: str,
        session_id: str,
        user_request: str,
        profile: dict,
        resource_type: str = "ppt",
    ) -> Resource:
        """执行完整管线，返回最终审核通过的 Resource。"""
        storage = settings.ensure_storage_dir()
        rtype = self._parse_resource_type(resource_type)

        # ① 大纲
        await self._update(task_id, 10, "正在生成大纲...")
        outline: Outline = await self.outline_gen.generate(user_request, profile)

        # ② 内容
        await self._update(task_id, 30, "正在撰写内容...")
        sections = await self.content_writer.write_all(outline, profile)
        content_text = "\n".join(s.markdown for s in sections)

        # 根据资源类型分流渲染
        await self._update(task_id, 55, "正在编排版式...")

        if rtype == ResourceTypeEnum.PPT:
            await self._update(task_id, 55, "正在编排幻灯片...")
            slides = self.ppt_renderer.arrange_slides(outline.title, sections)
            await self._update(task_id, 75, "正在渲染文档...")
            file_path = self.ppt_renderer.render(outline.title, slides, storage)
            url = self._to_url(file_path)
            description = self._describe_ppt(slides)

        elif rtype == ResourceTypeEnum.MINDMAP:
            await self._update(task_id, 75, "正在生成思维导图...")
            file_path = await self.doc_renderer.render_mindmap(outline, storage)
            url = self._to_url(file_path)
            description = f"思维导图，覆盖 {len(outline.sections)} 个章节"

        elif rtype == ResourceTypeEnum.DOC:
            await self._update(task_id, 75, "正在生成文档...")
            file_path = await self.doc_renderer.render_markdown(outline.title, sections, storage)
            url = self._to_url(file_path)
            description = f"Markdown 文档，共 {len(sections)} 节"

        elif rtype == ResourceTypeEnum.PDF:
            await self._update(task_id, 75, "正在生成 PDF...")
            file_path = await self.doc_renderer.render_pdf(outline.title, sections, storage)
            url = self._to_url(file_path)
            description = f"PDF 文档，共 {len(sections)} 节"

        else:  # video 等暂以文档兜底
            await self._update(task_id, 75, "正在生成文档...")
            file_path = await self.doc_renderer.render_markdown(outline.title, sections, storage)
            url = self._to_url(file_path)
            description = f"资料文档，共 {len(sections)} 节"

        # ⑤ 审核
        await self._update(task_id, 90, "正在进行安全审核...")
        result = await self.review.review(
            content_text=content_text,
            file_path=file_path,
            resource_type=rtype,
            title=outline.title,
            url=url,
            description=description,
        )

        if not result.passed:
            # 抛出由 TaskManager 兜底标记失败
            raise ResourceGenException(result.code, result.message)

        logger.info("资源生成完成 task=%s resource=%s", task_id, result.resource.resourceId)
        return result.resource

    # ── 辅助 ──────────────────────────────────────────
    async def _update(self, task_id: str, progress: int, description: str) -> None:
        await self.task_manager.update_progress(task_id, progress, description)
        # 演示慢放开关：DEMO_STEP_DELAY>0 时每个阶段停顿，便于观察进度爬升。
        # 默认 0（不影响生产与测试）；演示时设 set DEMO_STEP_DELAY=1 即可。
        delay = float(os.getenv("DEMO_STEP_DELAY", "0"))
        if delay > 0:
            await asyncio.sleep(delay)

    @staticmethod
    def _parse_resource_type(raw: str) -> ResourceTypeEnum:
        try:
            return ResourceTypeEnum(raw)
        except ValueError:
            return ResourceTypeEnum.PPT

    @staticmethod
    def _to_url(file_path: Path) -> str:
        """把本地文件路径转为可访问 URL（开发期用内置 /files 静态服务）。"""
        name = Path(file_path).name
        return f"{settings.PUBLIC_BASE_URL}/{name}"

    @staticmethod
    def _describe_ppt(slides) -> str:
        return f"共 {len(slides)} 页幻灯片"


class ResourceGenException(Exception):
    """资源生成业务异常，携带业务错误码。"""

    def __init__(self, code: int, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
