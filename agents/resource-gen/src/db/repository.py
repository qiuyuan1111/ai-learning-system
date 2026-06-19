"""资源存储 —— 按 sessionId 组织，开发阶段内存实现。"""
from __future__ import annotations

from typing import Dict, List, Optional

from ai_edu_common import Resource
from ai_edu_common.enums import ResourceTypeEnum


class ResourceRepository:
    """资源仓储（内存实现）。

    数据结构：{ sessionId: [Resource, ...] }
    """

    def __init__(self) -> None:
        self._by_session: Dict[str, List[Resource]] = {}

    async def save(self, session_id: str, resource: Resource) -> Resource:
        self._by_session.setdefault(session_id, []).append(resource)
        return resource

    async def list(
        self,
        session_id: str,
        type_filter: Optional[ResourceTypeEnum] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> List[Resource]:
        items = self._by_session.get(session_id, [])
        if type_filter is not None:
            items = [r for r in items if r.type == type_filter]
        start = (page - 1) * page_size
        return items[start : start + page_size]

    async def count(
        self,
        session_id: str,
        type_filter: Optional[ResourceTypeEnum] = None,
    ) -> int:
        items = self._by_session.get(session_id, [])
        if type_filter is None:
            return len(items)
        return sum(1 for r in items if r.type == type_filter)

    async def get_all(self, session_id: str) -> List[Resource]:
        return list(self._by_session.get(session_id, []))
