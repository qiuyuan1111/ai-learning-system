"""组件装配层（依赖注入容器）。

把 task/store、repository、llm、5 个子智能体、pipeline、notifier 组装在一起，
供 FastAPI 路由复用。集中装配，便于测试时替换组件。
"""
from __future__ import annotations

from functools import lru_cache

from .config import settings
from .db.repository import ResourceRepository
from .orchestrator.content_writer import ContentWriter
from .orchestrator.doc_renderer import DocRenderer
from .orchestrator.outline_generator import OutlineGenerator
from .orchestrator.pipeline import ResourceGenerationPipeline
from .orchestrator.ppt_renderer import PptRenderer
from .orchestrator.review_checker import ReviewChecker
from .services.llm_service import LlmService, get_llm_service
from .task.manager import TaskManager
from .task.store import TaskStore
from .ws.notifier import WsNotifier


class Container:
    """全局组件容器（单例）。"""

    def __init__(self) -> None:
        self.task_store = TaskStore()
        self.repository = ResourceRepository()
        self.notifier = WsNotifier(gateway_push_url=settings.GATEWAY_PUSH_URL)
        self.llm: LlmService = get_llm_service()

        self.outline_generator = OutlineGenerator(self.llm)
        self.content_writer = ContentWriter(self.llm)
        self.ppt_renderer = PptRenderer()
        self.doc_renderer = DocRenderer()
        self.review_checker = ReviewChecker(enable_safety=settings.ENABLE_SAFETY_CHECK)

        self.pipeline = ResourceGenerationPipeline(
            task_manager=None,  # 下方注入，避免循环
            outline_generator=self.outline_generator,
            content_writer=self.content_writer,
            ppt_renderer=self.ppt_renderer,
            doc_renderer=self.doc_renderer,
            review_checker=self.review_checker,
        )

        self.task_manager = TaskManager(self.task_store)
        self.task_manager.pipeline = self.pipeline
        self.task_manager.notifier = self.notifier
        # 补回 pipeline 对 task_manager 的引用
        self.pipeline.task_manager = self.task_manager


@lru_cache(maxsize=1)
def get_container() -> Container:
    return Container()
