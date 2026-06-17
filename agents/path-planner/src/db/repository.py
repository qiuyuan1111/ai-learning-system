"""学习路径存储 —— 按 sessionId 内存存储。"""
from __future__ import annotations

from typing import Dict, List, Optional

from ai_edu_common import LearningPathResponse, Resource, UserProfile


class PathRepository:
    def __init__(self) -> None:
        self._paths: Dict[str, LearningPathResponse] = {}
        self._resources: Dict[str, List[Resource]] = {}
        self._profiles: Dict[str, UserProfile] = {}

    async def save_path(self, session_id: str, path: LearningPathResponse) -> None:
        self._paths[session_id] = path

    async def get_path(self, session_id: str) -> Optional[LearningPathResponse]:
        return self._paths.get(session_id)

    async def set_resources(self, session_id: str, resources: List[Resource]) -> None:
        self._resources[session_id] = list(resources)

    async def get_resources(self, session_id: str) -> List[Resource]:
        return list(self._resources.get(session_id, []))

    async def set_profile(self, session_id: str, profile: UserProfile) -> None:
        self._profiles[session_id] = profile

    async def get_profile(self, session_id: str) -> Optional[UserProfile]:
        return self._profiles.get(session_id)

