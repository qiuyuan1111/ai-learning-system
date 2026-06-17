"""消息 DTO 定义"""

from pydantic import BaseModel, Field
from typing import Any, Dict, List
from datetime import datetime, timezone
from .schema import UserProfile


class WSMessage(BaseModel):
    """WebSocket 输入消息帧"""
    msgId: str
    intent: str
    content: Dict[str, Any]
    context: Dict[str, Any] = Field(default_factory=dict)


class WSOutputMessage(BaseModel):
    """WebSocket 输出消息帧"""
    msgId: str
    replyTo: str
    intent: str
    type: str  # text, done, error
    content: Dict[str, Any]
    ts: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ProfileBuildResult(BaseModel):
    """画像构建结果"""
    updated_profile: UserProfile
    reply_text: str
    is_complete: bool
    missing_dimensions: List[str] = Field(default_factory=list)
