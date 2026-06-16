"""
消息 DTO 定义

遵循 common/ 中定义的通用 WS 消息帧格式。
"""

import uuid
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


# ── 客户端 → 服务端 ──────────────────────────────────────────────


class Attachment(BaseModel):
    """附件元信息"""

    type: str
    url: str
    mimeType: str


class MessageContent(BaseModel):
    """消息内容体"""

    text: str
    attachments: Optional[List[Attachment]] = None


class WSClientMessage(BaseModel):
    """客户端 WS 消息帧"""

    msgId: str
    intent: Literal["tutoring"]
    content: MessageContent
    context: Optional[Dict[str, Any]] = None


# ── 服务端 → 客户端 ──────────────────────────────────────────────


class WSServerMessage(BaseModel):
    """服务端 WS 消息帧"""

    msgId: str
    replyTo: str
    intent: str = "tutoring"
    type: Literal["text", "resource_card", "progress", "done", "error"]
    content: Dict[str, Any]


# ── 内部 DTO ────────────────────────────────────────────────────


class TutorRequest(BaseModel):
    """辅导引擎内部请求"""

    session_id: str
    question: str
    attachments: List[Attachment] = Field(default_factory=list)
    resource_id: Optional[str] = None
    course_id: Optional[str] = None


class TutorResponseChunk(BaseModel):
    """辅导引擎输出流式块"""

    type: Literal["text", "progress", "done", "error"]
    content: Dict[str, Any]


def make_server_message(
    reply_to: str,
    type_: Literal["text", "resource_card", "progress", "done", "error"],
    content: Dict[str, Any],
    msg_id: Optional[str] = None,
    intent: str = "tutoring",
) -> WSServerMessage:
    """构造服务端消息帧的快捷方法"""
    return WSServerMessage(
        msgId=msg_id or str(uuid.uuid4()),
        replyTo=reply_to,
        intent=intent,
        type=type_,
        content=content,
    )
