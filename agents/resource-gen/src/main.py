"""资源生成编排器 —— FastAPI 入口。

对外接口（经网关）：
    POST /api/v1/sessions/{sessionId}/resources/generate   启动生成（异步）
    GET  /api/v1/resource-tasks/{taskId}                   查询任务状态
    GET  /api/v1/sessions/{sessionId}/resources            资源列表（分页）
    GET  /files/{name}                                     静态文件访问（开发期）

响应体统一为 ApiResponse（见 api.md 1.5）。
"""
from __future__ import annotations

import asyncio
import logging
import math
from typing import Optional

from ai_edu_common import error, paginated, success
from ai_edu_common.enums import ErrorCodeEnum, ResourceTypeEnum
from fastapi import FastAPI, Query, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .dependencies import get_container
from .models.dto import GenerationRequest

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(title="资源生成编排器", version="1.0.0")
    container = get_container()

    # 静态文件服务（开发期访问生成的 PPT/PDF 等）
    settings.ensure_storage_dir()
    app.mount(
        "/files",
        StaticFiles(directory=str(settings.FILE_STORAGE_PATH)),
        name="files",
    )

    def _req_id(request: Request) -> str:
        return request.headers.get("X-Request-Id", "") or ""

    # ── 启动资源生成 ──────────────────────────────────
    @app.post("/api/v1/sessions/{sessionId}/resources/generate")
    async def start_generation(sessionId: str, req: GenerationRequest, request: Request):
        """启动资源生成（内部接口，由网关触发）。"""
        rid = _req_id(request)
        if not req.text:
            return error(ErrorCodeEnum.PARAM_ERROR, "参数错误: text 不能为空", rid)

        tm = container.task_manager
        task = await tm.create_task(session_id=sessionId, request=req.text)
        # 记录任务入参上下文
        tm._context[task.taskId] = {  # noqa: SLF001
            "session_id": sessionId,
            "request": req.text,
            "resource_type": req.resourceType,
            "profile": req.profile,
        }
        # 后台异步执行管线，立即返回 taskId
        tm.start_pipeline_background(
            task_id=task.taskId,
            session_id=sessionId,
            user_request=req.text,
            profile=req.profile,
        )
        return success(task.model_dump(mode="json"), rid)

    # ── 查询任务状态 ──────────────────────────────────
    @app.get("/api/v1/resource-tasks/{taskId}")
    async def get_task(taskId: str, request: Request):
        rid = _req_id(request)
        task = await container.task_manager.get_task(taskId)
        if task is None:
            return error(ErrorCodeEnum.TASK_NOT_FOUND, "任务不存在", rid)
        return success(task.model_dump(mode="json"), rid)

    # ── 资源列表（分页） ──────────────────────────────
    @app.get("/api/v1/sessions/{sessionId}/resources")
    async def list_resources(
        sessionId: str,
        request: Request,
        type: Optional[str] = Query(None),
        page: int = Query(1, ge=1),
        pageSize: int = Query(20, ge=1, le=100),
    ):
        rid = _req_id(request)
        type_filter = None
        if type:
            try:
                type_filter = ResourceTypeEnum(type)
            except ValueError:
                return error(ErrorCodeEnum.PARAM_ERROR, f"无效的资源类型: {type}", rid)

        items = await container.repository.list(sessionId, type_filter, page, pageSize)
        total = await container.repository.count(sessionId, type_filter)
        total_pages = math.ceil(total / pageSize) if pageSize > 0 else 0
        data = paginated(
            [r.model_dump(mode="json") for r in items], page, pageSize, total
        )
        return success(data.model_dump(mode="json"), rid)

    # ── 健康检查 ──────────────────────────────────────
    @app.get("/health")
    async def health():
        return {"status": "ok", "service": settings.SERVICE_NAME}

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=False,
    )
