"""WebSocket 进度通知器（见 work-person-c.md 4.7）。

本服务不直接连接客户端 WS，而是把进度消息推送给网关（由网关转发）。
开发期网关未接通时，消息存入 in-memory 队列，便于测试断言。
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from ai_edu_common import IdGenerator, Resource

logger = logging.getLogger(__name__)


class WsNotifier:
    """进度通知器。"""

    def __init__(self, gateway_push_url: str = "") -> None:
        self.gateway_push_url = gateway_push_url
        # 开发期：记录所有推送消息，便于测试
        self.sent: List[Dict[str, Any]] = []

    async def notify_progress(self, task_id: str, progress: int, description: str) -> None:
        await self._send(
            {
                "type": "progress",
                "intent": "resource_generate",
                "content": {
                    "taskId": task_id,
                    "progress": progress,
                    "description": description,
                },
            }
        )

    async def notify_complete(self, resource: Resource) -> None:
        await self._send(
            {
                "type": "resource_card",
                "intent": "resource_generate",
                "content": {
                    "resourceType": resource.type.value,
                    "title": resource.title,
                    "url": resource.url,
                    "description": resource.description or "",
                },
            }
        )

    async def _send(self, payload: Dict[str, Any]) -> None:
        # 统一补充消息帧外层字段（见 api.md 2.2 服务端推送帧）
        frame = {
            "msgId": IdGenerator.request_id(),
            **payload,
        }
        self.sent.append(frame)
        if self.gateway_push_url:
            # 生产期：POST 到网关内部推送接口（此处仅占位，避免引入强依赖）
            logger.debug("推送至网关 %s: %s", self.gateway_push_url, frame.get("type"))
        else:
            logger.info("[WS推送] %s", frame.get("type"))

    # 测试辅助
    def types_sent(self) -> List[str]:
        return [m["type"] for m in self.sent]

    def clear(self) -> None:
        self.sent.clear()
