"""路径规划装配层 + 业务编排。"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List, Optional

from ai_edu_common import (
    EvaluationReport,
    LearningPathResponse,
    ProfileDimensions,
    Resource,
    UserProfile,
)

from ..config import settings
from ..db.repository import PathRepository
from .llm_service import LlmService, get_llm_service
from .path_adjuster import PathAdjuster
from .path_generator import PathGenerator
from .resource_binder import ResourceBinder

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class PathPlannerService:
    """路径规划对外业务服务：组合 生成 / 查询 / 调整。"""

    def __init__(
        self,
        repository: Optional[PathRepository] = None,
        llm: Optional[LlmService] = None,
    ) -> None:
        self.repository = repository or PathRepository()
        self.llm = llm or get_llm_service()
        self.binder = ResourceBinder(threshold=settings.BIND_MATCH_THRESHOLD)
        self.generator = PathGenerator(self.llm, self.binder)
        self.adjuster = PathAdjuster()

    async def set_context(
        self, session_id: str, profile: UserProfile, resources: List[Resource]
    ) -> None:
        """注入画像与资源（由网关/其它服务在 GET 前调用）。"""
        await self.repository.set_profile(session_id, profile)
        await self.repository.set_resources(session_id, resources)

    async def get_or_create_path(self, session_id: str) -> Optional[LearningPathResponse]:
        """GET 入口：按 sessionId 内部取 profile/resources，无则首次生成。

        profile 缺失时使用默认空画像，保证接口可用。
        """
        path = await self.repository.get_path(session_id)
        if path is not None:
            return path

        profile = await self.repository.get_profile(session_id)
        if profile is None:
            profile = UserProfile(
                sessionId=session_id,
                dimensions=ProfileDimensions(),
                updatedAt=_now_iso(),
                version=1,
            )
        resources = await self.repository.get_resources(session_id)
        path = await self.generator.generate(session_id, profile, resources)
        await self.repository.save_path(session_id, path)
        return path

    async def adjust_path(
        self,
        session_id: str,
        evaluation_report: EvaluationReport,
        updated_profile: UserProfile,
    ) -> Optional[LearningPathResponse]:
        current = await self.repository.get_path(session_id)
        if current is None:
            return None
        adjusted = await self.adjuster.adjust(current, evaluation_report, updated_profile)
        await self.repository.save_path(session_id, adjusted)
        return adjusted
