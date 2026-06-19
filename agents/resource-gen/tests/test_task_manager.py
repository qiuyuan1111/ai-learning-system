"""resource-gen —— 异步任务管理器测试。"""
from __future__ import annotations

import asyncio

import pytest
from ai_edu_common.enums import TaskStatusEnum

from src.task.manager import TaskManager
from src.task.store import TaskStore


@pytest.fixture
def manager():
    tm = TaskManager(TaskStore())
    return tm


class TestTaskManager:
    @pytest.mark.asyncio
    async def test_create_task(self, manager):
        task = await manager.create_task("sess_1", "生成PPT")
        assert task.taskId.startswith("task_")
        assert task.status == TaskStatusEnum.PENDING
        assert task.progress == 0

    @pytest.mark.asyncio
    async def test_get_task_not_found(self, manager):
        assert await manager.get_task("task_nope") is None

    @pytest.mark.asyncio
    async def test_update_progress(self, manager):
        task = await manager.create_task("sess_1", "x")
        await manager.update_progress(task.taskId, 55, "正在渲染...")
        updated = await manager.get_task(task.taskId)
        assert updated.progress == 55
        assert updated.status == TaskStatusEnum.PROCESSING
        assert updated.progressDescription == "正在渲染..."

    @pytest.mark.asyncio
    async def test_progress_clamped(self, manager):
        task = await manager.create_task("sess_1", "x")
        await manager.update_progress(task.taskId, 200, "超")
        updated = await manager.get_task(task.taskId)
        assert updated.progress == 100  # 被钳制到上限

    @pytest.mark.asyncio
    async def test_progress_clamped_lower_bound(self, manager):
        """边界：进度为负数时，应被钳制到 0，不允许负值。"""
        task = await manager.create_task("sess_1", "x")
        await manager.update_progress(task.taskId, -10, "负数")
        updated = await manager.get_task(task.taskId)
        assert updated.progress == 0  # 被钳制到下限


    @pytest.mark.asyncio
    async def test_complete_task(self, manager):
        from ai_edu_common import IdGenerator, Resource
        from ai_edu_common.enums import ResourceTypeEnum

        task = await manager.create_task("sess_1", "x")
        res = Resource(
            resourceId=IdGenerator.resource_id(),
            type=ResourceTypeEnum.PPT,
            title="t",
            url="u",
            createdAt="2026-06-15T10:00:00Z",
        )
        await manager.complete_task(task.taskId, [res])
        updated = await manager.get_task(task.taskId)
        assert updated.status == TaskStatusEnum.COMPLETED
        assert updated.progress == 100
        assert updated.result.resources[0].resourceId == res.resourceId

    @pytest.mark.asyncio
    async def test_fail_task(self, manager):
        task = await manager.create_task("sess_1", "x")
        await manager.fail_task(task.taskId, 2002, "生成失败")
        updated = await manager.get_task(task.taskId)
        assert updated.status == TaskStatusEnum.FAILED
        assert updated.error.code == 2002
        assert updated.error.message == "生成失败"
