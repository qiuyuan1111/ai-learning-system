"""异步任务管理器（见 work-person-c.md 4.5）。

职责：
    - 创建任务（pending）
    - 在后台 asyncio 任务中驱动生成管线
    - 更新进度 / 完成 / 失败
    - 提供查询接口

存储层通过注入 TaskStore，便于后续替换为 Redis。
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from ai_edu_common import IdGenerator, Resource, TaskError, TaskInfo, TaskResult
from ai_edu_common.enums import ErrorCodeEnum, TaskStatusEnum

from .store import TaskStore

if TYPE_CHECKING:  # 避免循环导入
    from ..orchestrator.pipeline import ResourceGenerationPipeline
    from ..ws.notifier import WsNotifier

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class TaskManager:
    """异步任务管理器。"""

    def __init__(self, store: TaskStore) -> None:
        self.store = store
        # 运行期注入（main 中装配）
        self.pipeline: Optional["ResourceGenerationPipeline"] = None
        self.notifier: Optional["WsNotifier"] = None
        # 任务业务上下文（入参），与对外 TaskInfo 解耦
        self._context: dict[str, dict] = {}

    # ── 查询 ──────────────────────────────────────────
    async def get_task(self, task_id: str) -> Optional[TaskInfo]:
        return self.store.get(task_id)

    # ── 状态变更 ──────────────────────────────────────
    async def create_task(self, session_id: str, request: str) -> TaskInfo:
        task_id = IdGenerator.task_id()
        task = TaskInfo(
            taskId=task_id,
            status=TaskStatusEnum.PENDING,
            progress=0,
            createdAt=_now_iso(),
            updatedAt=_now_iso(),
        )
        # 额外记录业务上下文（不进对外契约，仅内部使用）
        self.store.save(task)
        self._context[task_id] = {
            "session_id": session_id,
            "request": request,
        }
        return task

    async def update_progress(self, task_id: str, progress: int, description: str) -> None:
        task = self.store.get(task_id)
        if task is None:
            return
        task.status = TaskStatusEnum.PROCESSING
        task.progress = min(max(progress, 0), 100)
        task.progressDescription = description
        task.updatedAt = _now_iso()
        self.store.save(task)
        if self.notifier:
            await self.notifier.notify_progress(task_id, task.progress, description)

    async def complete_task(self, task_id: str, resources: list[Resource]) -> None:
        task = self.store.get(task_id)
        if task is None:
            return
        task.status = TaskStatusEnum.COMPLETED
        task.progress = 100
        task.progressDescription = "生成完成"
        task.result = TaskResult(resources=resources)
        task.updatedAt = _now_iso()
        self.store.save(task)
        if self.notifier:
            for res in resources:
                await self.notifier.notify_complete(res)

    async def fail_task(self, task_id: str, code: int, message: str) -> None:
        task = self.store.get(task_id)
        if task is None:
            return
        task.status = TaskStatusEnum.FAILED
        task.error = TaskError(code=code, message=message)
        task.updatedAt = _now_iso()
        self.store.save(task)

    # ── 后台驱动 ──────────────────────────────────────
    def start_pipeline_background(
        self,
        task_id: str,
        session_id: str,
        user_request: str,
        profile: Optional[dict],
    ) -> asyncio.Task:
        """启动后台管线执行，不阻塞当前请求。"""
        return asyncio.create_task(
            self._run_pipeline(task_id, session_id, user_request, profile)
        )

    async def _run_pipeline(
        self,
        task_id: str,
        session_id: str,
        user_request: str,
        profile: Optional[dict],
    ) -> None:
        if self.pipeline is None:
            await self.fail_task(task_id, ErrorCodeEnum.UNKNOWN_ERROR, "管线未装配")
            return
        try:
            resource = await self.pipeline.execute(
                task_id=task_id,
                session_id=session_id,
                user_request=user_request,
                profile=profile or {},
            )
            await self.complete_task(task_id, [resource])
        except Exception as exc:  # noqa: BLE001  管线任意阶段失败都要兜底
            logger.exception("资源生成管线失败 task=%s", task_id)
            # 若异常携带业务错误码（如审核 3001/3002），保留之；否则统一标 2002
            code = getattr(exc, "code", ErrorCodeEnum.RESOURCE_GEN_FAILED)
            message = getattr(exc, "message", str(exc))
            await self.fail_task(task_id, code, message)

    def get_context(self, task_id: str) -> Optional[dict]:
        return self._context.get(task_id)
