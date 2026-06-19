"""画像服务客户端

通过 REST API 调用画像智能体服务获取用户画像。
"""

import logging
from typing import Any, Dict, Optional

import httpx

from ..config import settings

logger = logging.getLogger(__name__)

_PROFILE_ROUTE = "/api/v1/profile/{session_id}"


class ProfileServiceClient:
    """画像服务 REST 客户端"""

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: int = 10,
    ):
        self.base_url = (base_url or settings.profile_service_url).rstrip("/")
        self.timeout = timeout or settings.profile_service_timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                base_url=self.base_url,
            )
        return self._client

    async def get_profile(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取指定会话的用户画像

        返回: 用户画像字典，服务不可用时返回 None
        """
        client = await self._get_client()
        url = _PROFILE_ROUTE.format(session_id=session_id)

        try:
            response = await client.get(url)
        except httpx.RequestError as e:
            logger.warning("画像服务连接失败: %s", e)
            return None

        if response.status_code != 200:
            logger.warning("画像服务返回 %s", response.status_code)
            return None

        data = response.json()
        return data.get("data") or data.get("profile") or data

    async def health_check(self) -> bool:
        """检查画像服务是否可用"""
        try:
            client = await self._get_client()
            resp = await client.get("/health")
            return resp.status_code == 200
        except Exception:
            return False

    async def close(self):
        """关闭 HTTP 客户端连接池"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
