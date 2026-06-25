"""WebSocket 消息处理器（画像构建）"""

import json
import uuid
from typing import Any, Dict, List, Optional

from ..models.schema import UserProfile
from ..models.dto import WSMessage, WSOutputMessage, ProfileBuildResult
from ..services.profile_builder import ProfileBuilder
from ..services.profile_updater import ProfileUpdater
from ..db.repository import ProfileRepository
from ..db.memory import DialogueMemory


class ProfileWSHandler:
    """WebSocket 消息处理器（画像构建）

    处理 /ws/chat 中 intent=profile_build 的消息。
    支持构建(build)和增量更新(update)两种模式。
    """

    def __init__(
        self,
        builder: ProfileBuilder,
        updater: ProfileUpdater,
        repo: ProfileRepository,
        memory: DialogueMemory,
    ):
        self.builder = builder
        self.updater = updater
        self.repo = repo
        self.memory = memory

    async def handle_message(self, raw: str, session_id: str) -> List[Dict[str, Any]]:
        """处理一条原始 WebSocket 消息

        参数:
            raw: 原始 JSON 字符串
            session_id: 会话 ID

        返回: 服务端推送帧列表
        """
        try:
            message = WSMessage.model_validate_json(raw)
        except Exception as e:
            return [
                self._error_frame("", "invalid_message", f"消息格式错误: {e}")
            ]

        if message.intent == "profile_build":
            return await self._handle_build(session_id, message)
        elif message.intent == "profile_update":
            return await self._handle_update(session_id, message)
        else:
            return [
                self._error_frame(
                    message.msgId, "unknown_intent", f"不支持的 intent: {message.intent}"
                )
            ]

    async def _handle_build(self, session_id: str, message: WSMessage) -> List[Dict[str, Any]]:
        """处理画像构建消息"""
        user_text = message.content.get("text", "")
        if not user_text.strip():
            return [self._error_frame(message.msgId, "empty_text", "消息内容不能为空")]

        # 获取当前画像
        current_profile = await self.repo.get(session_id)

        # 处理画像构建
        result: ProfileBuildResult = await self.builder.process_message(
            session_id, user_text, current_profile
        )

        # 保存画像
        await self.repo.save(result.updated_profile)

        # 记录对话记忆
        self.memory.add(session_id, {"role": "user", "content": user_text})
        self.memory.add(session_id, {"role": "assistant", "content": result.reply_text})

        # 构建返回帧
        frames = [
            self._text_frame(
                message.msgId,
                result.reply_text,
                extra={
                    "missing_dimensions": result.missing_dimensions,
                },
            )
        ]

        if result.is_complete:
            profile_summary = self._summarize_profile(result.updated_profile)
            frames.append(
                self._done_frame(message.msgId, profile_summary)
            )

        return frames

    async def _handle_update(self, session_id: str, message: WSMessage) -> List[Dict[str, Any]]:
        """处理画像更新消息"""
        content = message.content
        source_type = content.get("source", "dialogue")
        current_profile = await self.repo.get(session_id)

        if current_profile is None:
            return [self._error_frame(message.msgId, "no_profile", "尚未构建画像，请先发起构建")]

        if source_type == "evaluation":
            updated = await self.updater.update_from_evaluation(
                session_id, content.get("evaluation", {}), current_profile
            )
        else:
            history = self.memory.get_history(session_id, limit=10)
            updated = await self.updater.update_from_dialogue(
                session_id, history, current_profile
            )

        await self.repo.save(updated)

        return [
            self._text_frame(
                message.msgId,
                "画像已更新",
                extra={"version": updated.version},
            )
        ]

    def _text_frame(
        self,
        reply_to: str,
        text: str,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """构造 text 类型输出帧"""
        content: Dict[str, Any] = {"markdown": text}
        if extra:
            content.update(extra)
        return WSOutputMessage(
            msgId=str(uuid.uuid4()),
            replyTo=reply_to,
            intent="profile_build",
            type="text",
            content=content,
        ).model_dump()

    def _done_frame(self, reply_to: str, profile_summary: dict) -> Dict[str, Any]:
        """构造 done 类型输出帧"""
        return WSOutputMessage(
            msgId=str(uuid.uuid4()),
            replyTo=reply_to,
            intent="profile_build",
            type="done",
            content={"profile": profile_summary},
        ).model_dump()

    def _error_frame(self, reply_to: str, code: str, detail: str) -> Dict[str, Any]:
        """构造 error 类型输出帧"""
        return WSOutputMessage(
            msgId=str(uuid.uuid4()),
            replyTo=reply_to,
            intent="profile_build",
            type="error",
            content={"code": code, "detail": detail},
        ).model_dump()

    def _summarize_profile(self, profile: UserProfile) -> dict:
        """生成画像摘要（用于 done 帧）"""
        dims = profile.dimensions
        summary = {
            "session_id": profile.session_id,
            "version": profile.version,
            "dimensions": {},
        }

        if dims.knowledge_base:
            summary["dimensions"]["knowledge_base"] = {
                "level": dims.knowledge_base.level.value,
                "tags": dims.knowledge_base.tags,
                "confidence": dims.knowledge_base.confidence,
            }
        if dims.cognitive_style:
            summary["dimensions"]["cognitive_style"] = {
                "style": dims.cognitive_style.style.value,
                "confidence": dims.cognitive_style.confidence,
            }
        if dims.learning_pace:
            summary["dimensions"]["learning_pace"] = {
                "pace": dims.learning_pace.pace.value,
                "confidence": dims.learning_pace.confidence,
            }
        if dims.weakness_preferences:
            summary["dimensions"]["weakness_preferences"] = [
                {"tags": w.weak_tags, "confidence": w.confidence}
                for w in dims.weakness_preferences
            ]
        if dims.interest_areas:
            summary["dimensions"]["interest_areas"] = [
                {"areas": ia.areas, "depth": ia.depth, "confidence": ia.confidence}
                for ia in dims.interest_areas
            ]
        if dims.target_difficulty:
            summary["dimensions"]["target_difficulty"] = {
                "level": dims.target_difficulty.level,
                "confidence": dims.target_difficulty.confidence,
            }

        return summary
