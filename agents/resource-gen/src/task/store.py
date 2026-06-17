"""任务状态存储 —— 开发阶段用内存 dict（见 work-person-c.md 4.5）。

预留接口，生产阶段可替换为 Redis 实现，无需改动上层 TaskManager。
"""
from __future__ import annotations

from typing import Dict, Optional

from ai_edu_common import TaskInfo


class TaskStore:
    """任务存储抽象（内存实现）。"""

    def __init__(self) -> None:
        self._tasks: Dict[str, TaskInfo] = {}

    def save(self, task: TaskInfo) -> None:
        self._tasks[task.taskId] = task

    def get(self, task_id: str) -> Optional[TaskInfo]:
        return self._tasks.get(task_id)

    def all(self) -> Dict[str, TaskInfo]:
        return dict(self._tasks)
