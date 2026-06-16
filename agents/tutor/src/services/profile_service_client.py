"""
画像服务客户端

通过 REST API 调用画像智能体服务获取用户画像。
复用 httpx.AsyncClient 连接池以提高性能。
"""

import logging
from typing import Any, Dict, Optional

import httpx

from src.config import config, profile_routes

logger = logging.getLogger(__name__)


class ProfileServiceClient:
    """
    画像服务 REST 客户端

    封装对画像智能体（agents/profile/）的 HTTP 调用。
    复用 httpx.AsyncClient 连接池，避免每次请求创建新连接。
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: int = 10,
    ):
        self.base_url = (base_url or config.profile_service_url).rstrip("/")
        self.timeout = timeout or config.profile_service_timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """获取或创建复用的 HTTP 客户端"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                base_url=self.base_url,
            )
        return self._client

    async def get_profile(self, session_id: str) -> Dict[str, Any]:
        """
        获取指定会话的用户画像

        参数:
            session_id: 会话 ID

        返回: 用户画像字典

        抛出:
            ProfileNotFoundError: 画像不存在
            ProfileServiceError: 服务调用失败
        """
        client = await self._get_client()
        url = profile_routes.get_profile.format(session_id=session_id)

        try:
            response = await client.get(url)
        except httpx.RequestError as e:
            raise ProfileServiceError(session_id, 0, f"连接失败: {e}")

        if response.status_code == 404:
            raise ProfileNotFoundError(session_id)

        if response.status_code != 200:
            raise ProfileServiceError(
                session_id,
                response.status_code,
                response.text,
            )

        data = response.json()
        profile = data.get("data") or data.get("profile") or data
        return profile

    async def health_check(self) -> bool:
        """检查画像服务是否可用"""
        try:
            client = await self._get_client()
            resp = await client.get("/health")
            return resp.status_code == 200
        except Exception:
            logger.warning("画像服务健康检查失败", exc_info=True)
            return False

    async def close(self):
        """关闭 HTTP 客户端连接池"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None


class ProfileNotFoundError(Exception):
    """画像不存在异常"""

    def __init__(self, session_id: str):
        self.session_id = session_id
        super().__init__(f"Session {session_id} 的画像不存在")


class ProfileServiceError(Exception):
    """画像服务调用异常"""

    def __init__(self, session_id: str, status_code: int, body: str):
        self.session_id = session_id
        self.status_code = status_code
        self.body = body
        super().__init__(f"画像服务返回 {status_code}: {body[:200]}")
