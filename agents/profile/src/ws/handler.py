"""WebSocket 消息处理器（画像构建）"""

import json
import logging
import uuid
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

from ..models.schema import ProfileDimensions, UserProfile
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

    async def handle_message(self, raw: str, session_id: str):
        """处理一条原始 WebSocket 消息，流式 yield 服务端推送帧。

        参数:
            raw: 原始 JSON 字符串
            session_id: 会话 ID

        Yields: 服务端推送帧（dict）。profile_build 会逐 token yield type=text
                增量帧（流式），完成时再 yield type=done。
        """
        logger.info("[诊断] profile 收到消息 (session=%s): %s", session_id, raw)
        try:
            message = WSMessage.model_validate_json(raw)
        except Exception as e:
            logger.warning("[诊断] 消息解析失败: %s", e)
            yield self._error_frame("", "invalid_message", f"消息格式错误: {e}")
            return

        if message.intent == "profile_build":
            async for frame in self._handle_build(session_id, message):
                yield frame
        elif message.intent == "profile_update":
            async for frame in self._handle_update(session_id, message):
                yield frame
        else:
            yield self._error_frame(
                message.msgId, "unknown_intent", f"不支持的 intent: {message.intent}"
            )

    async def _handle_build(self, session_id: str, message: WSMessage):
        """处理画像构建消息：流式推送回复增量，流完后抽取+合并+落库，完成则发 done。"""
        user_text = message.content.get("text", "")
        if not user_text.strip():
            yield self._error_frame(message.msgId, "empty_text", "消息内容不能为空")
            return

        # 获取当前画像（首次则新建空画像）
        current_profile = await self.repo.get(session_id)
        if current_profile is None:
            current_profile = UserProfile(
                session_id=session_id,
                dimensions=ProfileDimensions(),
            )

        # 1. 流式回复：逐 token 推 type=text 增量帧（markdown=增量片段，与 tutor 一致）。
        #    此时 raw_dialogue 仅含历史轮次，当前 user_text 作为最后一条 user 消息，不重复送。
        full_reply = ""
        try:
            async for delta in self.builder.stream_reply(current_profile, user_text):
                full_reply += delta
                yield self._text_frame(message.msgId, delta)
        except Exception as e:
            logger.exception("[诊断] profile 流式回复失败 (session=%s)", session_id)
            yield self._error_frame(message.msgId, "llm_error", "回复生成失败，请重试")
            return

        # 2. 抽取维度更新（回复流完后串行跑，避免并发触发限流；失败不影响主流程）
        extracted = await self.builder.extract(current_profile, user_text)

        # 3. 合并 + 落本轮对话 + 滑动窗口压缩 + 算完成度
        result: ProfileBuildResult = await self.builder.finalize(
            current_profile, user_text, full_reply, extracted
        )

        # 保存画像 + 记录对话记忆
        await self.repo.save(result.updated_profile)
        self.memory.add(session_id, {"role": "user", "content": user_text})
        self.memory.add(session_id, {"role": "assistant", "content": full_reply})

        # 4. 完成则发 done（带画像摘要）；未完成不发 done（与原行为一致，前端靠回复文本感知）
        if result.is_complete:
            yield self._done_frame(
                message.msgId, self._summarize_profile(result.updated_profile)
            )

    async def _handle_update(self, session_id: str, message: WSMessage):
        """处理画像更新消息。

        联动场景（tutor 答疑动态更新画像）：调用方把最近几轮问答原文放进
        message.context['dialogue'] 传入（List[{role,content}]），优先使用它；
        未提供时回退到本服务自己的对话记忆 memory（仅含画像构建对话）。
        """
        content = message.content
        source_type = content.get("source", "dialogue")
        current_profile = await self.repo.get(session_id)

        if current_profile is None:
            yield self._error_frame(message.msgId, "no_profile", "尚未构建画像，请先发起构建")
            return

        if source_type == "evaluation":
            updated = await self.updater.update_from_evaluation(
                session_id, content.get("evaluation", {}), current_profile
            )
        else:
            # 优先用调用方传入的 dialogue（联动数据通道），无则回退本地对话记忆
            ctx = message.context or {}
            dialogue = ctx.get("dialogue")
            history = dialogue if dialogue else self.memory.get_history(session_id, limit=10)
            updated = await self.updater.update_from_dialogue(
                session_id, history, current_profile
            )

        await self.repo.save(updated)

        yield self._text_frame(
            message.msgId,
            "画像已更新",
            extra={"version": updated.version},
        )

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
