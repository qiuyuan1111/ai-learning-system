"""路径规划智能体 —— FastAPI 入口。

对外接口（经网关，符合 api.md）：
    GET  /api/v1/sessions/{sessionId}/learning-path   获取学习路径（首次自动生成）
    POST /api/v1/sessions/{sessionId}/recommend        触发推荐（响应为空，资源走 WS）

内部接口（由网关/其它服务调用，注入画像与资源）：
    POST /api/v1/sessions/{sessionId}/path-context     注入 profile + resources
    POST /api/v1/sessions/{sessionId}/path/adjust      根据评估调整路径（内部/测试用）

设计说明：GET /learning-path 按 api.md 不带请求体，profile/resources 由
上下文注入端点预先提供；缺失时使用默认空画像，保证接口可用。
"""
from __future__ import annotations

import asyncio
import logging
from typing import List

from ai_edu_common import (
    ErrorCodeEnum,
    EvaluationReport,
    Resource,
    UserProfile,
    error,
    success,
)
from fastapi import FastAPI, Request
from pydantic import BaseModel, ConfigDict, Field

from .config import settings
from .services.path_service import PathPlannerService

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


class PathContextRequest(BaseModel):
    """上下文注入请求（内部）：profile + resources。"""

    model_config = ConfigDict(extra="forbid")
    profile: UserProfile
    resources: List[Resource] = Field(default_factory=list)


class AdjustRequest(BaseModel):
    """路径调整请求。"""

    model_config = ConfigDict(extra="forbid")
    profile: UserProfile
    report: EvaluationReport


def create_app() -> FastAPI:
    app = FastAPI(title="路径规划智能体", version="1.0.0")
    service = PathPlannerService()

    def _req_id(request: Request) -> str:
        return request.headers.get("X-Request-Id", "") or ""

    @app.get("/api/v1/sessions/{sessionId}/learning-path")
    async def get_learning_path(sessionId: str, request: Request):
        """获取学习路径（无请求体）。首次访问时按已注入的画像+资源自动生成。"""
        rid = _req_id(request)
        path = await service.get_or_create_path(sessionId)
        if path is None:
            return error(ErrorCodeEnum.SESSION_NOT_FOUND, "会话不存在", rid)
        return success(path.model_dump(mode="json"), rid)

    @app.post("/api/v1/sessions/{sessionId}/path-context")
    async def set_context(sessionId: str, body: PathContextRequest, request: Request):
        """注入画像与资源（内部接口，GET 前由网关调用）。"""
        rid = _req_id(request)
        await service.set_context(sessionId, body.profile, body.resources)
        return success(None, rid)

    @app.post("/api/v1/sessions/{sessionId}/recommend")
    async def trigger_recommendation(sessionId: str, request: Request):
        """触发推荐（后台推送，响应为空）。"""
        rid = _req_id(request)
        asyncio.create_task(_noop_push(sessionId))
        return success(None, rid)

    @app.post("/api/v1/sessions/{sessionId}/path/adjust")
    async def adjust_path(sessionId: str, body: AdjustRequest, request: Request):
        """根据评估报告调整路径（内部/测试用）。"""
        rid = _req_id(request)
        path = await service.adjust_path(sessionId, body.report, body.profile)
        if path is None:
            return error(
                ErrorCodeEnum.SESSION_NOT_FOUND, "会话不存在，路径尚未生成", rid
            )
        return success(path.model_dump(mode="json"), rid)

    @app.get("/health")
    async def health():
        return {"status": "ok", "service": settings.SERVICE_NAME}

    return app


async def _noop_push(session_id: str) -> None:
    """占位推送（实际由网关 WS 下发，见 api.md 2.4.2）。"""
    logger.info("[推荐触发] session=%s（将由网关 WS 下发资源卡片）", session_id)


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.main:app", host="0.0.0.0", port=settings.PORT, reload=False)
