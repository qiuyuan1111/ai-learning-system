"""
WebSocket 消息处理器

处理 /ws/chat 中 intent=tutoring 的消息。
协调 TutorEngine 生成个性化回答，通过 WS 逐段推送。
"""

import json
import logging
from typing import Any, AsyncGenerator, Dict, Optional

from src.config import config
from src.models.dto import (
    Attachment,
    MessageContent,
    WSClientMessage,
    WSServerMessage,
    make_server_message,
)
from src.services.tutor_engine import TutorEngine

logger = logging.getLogger(__name__)


class TutorWSHandler:
    """
    WebSocket 消息处理器（辅导）

    处理 /ws/chat 中 intent=tutoring 的消息

    输入消息帧:
    {
        "msgId": "client_uuid",
        "intent": "tutoring",
        "content": { "text": "请解释一下Transformer的注意力机制" },
        "context": { "resourceId": "...", "courseId": "..." }
    }

    输出消息帧（逐条推送）:
    {"msgId":"srv_uuid","replyTo":"client_uuid","intent":"tutoring",
     "type":"text","content":{"markdown":"好的！让我..."}}
    {"msgId":"srv_uuid","replyTo":"client_uuid","intent":"tutoring",
     "type":"done","content":{}}
    """

    def __init__(self, tutor_engine: TutorEngine):
        self.engine = tutor_engine

    async def handle_message(
        self,
        raw_message: Dict[str, Any],
        session_id: str,
    ) -> AsyncGenerator[WSServerMessage, None]:
        """
        处理一条 tutoring 消息

        参数:
            raw_message: 解析后的 JSON 消息字典
            session_id: 会话 ID（从 WS 连接路径参数获取）

        Yields:
            WSServerMessage: 服务端消息帧
        """
        # 1. 解析消息
        try:
            client_msg = self._parse_message(raw_message)
        except ValueError as e:
            yield make_server_message(
                reply_to=raw_message.get("msgId", ""),
                type_="error",
                content={"code": "INVALID_MESSAGE", "message": str(e)},
            )
            return

        # 2. 提取参数
        question = client_msg.content.text
        attachments = client_msg.content.attachments or []
        ctx = client_msg.context or {}
        resource_id = ctx.get("resourceId")
        course_id = ctx.get("courseId")

        if not question.strip():
            yield make_server_message(
                reply_to=client_msg.msgId,
                type_="error",
                content={"code": "EMPTY_QUESTION", "message": "请输入您的问题。"},
            )
            return

        # 3. 推送开始
        yield make_server_message(
            reply_to=client_msg.msgId,
            type_="progress",
            content={"status": "思考中..."},
        )

        # 4. 调用辅导引擎生成回答
        async for chunk in self.engine.generate_answer(
            session_id=session_id,
            question=question,
            attachments=attachments,
            resource_id=resource_id,
            course_id=course_id,
        ):
            chunk_type = chunk["type"]
            if chunk_type == "text":
                yield make_server_message(
                    reply_to=client_msg.msgId,
                    type_="text",
                    content=chunk["content"],
                )
            elif chunk_type == "done":
                yield make_server_message(
                    reply_to=client_msg.msgId,
                    type_="done",
                    content={},
                )
            elif chunk_type == "error":
                yield make_server_message(
                    reply_to=client_msg.msgId,
                    type_="error",
                    content=chunk["content"],
                )
            else:
                logger.warning("未知的 chunk type: %s", chunk_type)

    def _parse_message(self, raw: Dict[str, Any]) -> WSClientMessage:
        """校验并解析客户端消息"""
        intent = raw.get("intent", "")
        if intent != "tutoring":
            raise ValueError(f"不支持的 intent: {intent}，期望 'tutoring'")

        content = raw.get("content", {})
        if not isinstance(content, dict) or not content.get("text", "").strip():
            raise ValueError("消息内容不能为空")

        attachments_raw = content.get("attachments") or []
        attachments = [
            Attachment(**a) if isinstance(a, dict) else a
            for a in attachments_raw
        ]

        return WSClientMessage(
            msgId=raw.get("msgId", ""),
            intent="tutoring",
            content=MessageContent(text=content["text"], attachments=attachments),
            context=raw.get("context"),
        )

    def validate_message(self, raw: Dict[str, Any]) -> Optional[str]:
        """
        校验消息格式，返回错误描述（None 表示通过）

        用于连接层面的快速校验，不涉及业务逻辑。
        """
        if not isinstance(raw, dict):
            return "消息必须是 JSON 对象"

        intent = raw.get("intent")
        if intent != "tutoring":
            return f"不支持的 intent: {intent}"

        content = raw.get("content")
        if not isinstance(content, dict):
            return "缺少 content 字段"
        if not content.get("text", "").strip():
            return "content.text 不能为空"

        return None
