"""
对话上下文管理器

维护多轮对话历史，支持上下文窗口截断。
当对话过长时，自动摘要历史或丢弃最早轮次。
"""

from typing import Any, Dict, List, Optional

from src.config import config
from src.models.context import DialogueContext, DialogueRound
from src.db.chat_history import ChatHistoryStore
from src.services.llm_service import LLMService


class ContextManager:
    """
    对话上下文管理器

    职责：
    维护多轮对话历史，支持上下文窗口截断。
    当对话过长时，自动摘要历史或丢弃最早轮次。

    策略:
    - 保留最近 MAX_ROUNDS 轮完整对话
    - 超过 MAX_ROUNDS 时，将前文压缩为摘要
    - 每次请求携带最近 N 轮 + 摘要
    """

    def __init__(
        self,
        store: ChatHistoryStore,
        llm_service: Optional[LLMService] = None,
        max_rounds: int = 10,
    ):
        self.store = store
        self._llm = llm_service
        self.max_rounds = max_rounds or config.max_context_rounds

    async def get_context(self, session_id: str) -> DialogueContext:
        """
        获取当前会话的对话上下文

        从存储中加载 DialogueContext，若不存在则创建新的。
        """
        context = await self.store.load_context(session_id)
        if context is None:
            context = DialogueContext(session_id=session_id)
            await self.store.save_context(context)
        return context

    async def append_round(
        self,
        session_id: str,
        question: str,
        answer: str,
        resource_id: Optional[str] = None,
        course_id: Optional[str] = None,
    ):
        """追加一轮对话记录，若超出轮次上限则触发摘要"""
        context = await self.get_context(session_id)
        context.add_round(
            question=question,
            answer=answer,
            resource_id=resource_id,
            course_id=course_id,
        )

        # 超出上限 → 触发摘要压缩
        if len(context.rounds) > self.max_rounds:
            await self._summarize_old_rounds(context)

        await self.store.save_context(context)

    async def summarize_history(self, session_id: str) -> str:
        """
        对历史对话进行摘要

        返回: 摘要文本
        """
        context = await self.get_context(session_id)
        if not context.rounds and not context.summary:
            return ""

        return await self._summarize_rounds(context.rounds, existing_summary=context.summary)

    def build_messages_for_llm(
        self,
        system_prompt: str,
        question: str,
        context: DialogueContext,
    ) -> List[Dict[str, Any]]:
        """
        构建发送给大模型的消息列表

        结构:
        1. system 消息（含画像适配后的系统提示）
        2. 前文摘要（如果有）
        3. 最近 N 轮对话
        4. 当前用户问题
        """
        messages: List[Dict[str, str]] = [
            {"role": "system", "content": system_prompt},
        ]

        # 注入前文摘要
        if context.summary:
            messages.append({
                "role": "system",
                "content": f"[历史对话摘要]\n{context.summary}",
            })

        # 注入最近 N 轮对话
        recent_rounds = context.rounds[-self.max_rounds:]
        for r in recent_rounds:
            messages.append({"role": "user", "content": r.question})
            messages.append({"role": "assistant", "content": r.answer})

        # 当前用户问题
        messages.append({"role": "user", "content": question})

        return messages

    async def _summarize_old_rounds(self, context: DialogueContext):
        """对最早的轮次进行摘要压缩"""
        if self._llm is None:
            # 没有 LLM 时直接丢弃最早一半的轮次
            drop_count = len(context.rounds) - self.max_rounds
            context.rounds = context.rounds[drop_count:]
            return

        # 对超出保留上限的轮次做摘要
        rounds_to_summarize = context.rounds[: -self.max_rounds]
        if not rounds_to_summarize:
            return

        summary = await self._summarize_rounds(
            rounds_to_summarize,
            existing_summary=context.summary,
        )

        context.summary = summary
        context.summary_rounds += len(rounds_to_summarize)
        context.rounds = context.rounds[-self.max_rounds:]

    async def _summarize_rounds(
        self,
        rounds: List[DialogueRound],
        existing_summary: Optional[str] = None,
    ) -> str:
        """执行摘要"""
        if not rounds:
            return existing_summary or ""

        dialogue_text = "\n".join(
            f"用户: {r.question}\n助手: {r.answer}" for r in rounds
        )

        previous = f"\n已有摘要:\n{existing_summary}\n\n" if existing_summary else "\n"

        messages = [
            {
                "role": "system",
                "content": (
                    "你是一个对话摘要助手。请将以下对话内容浓缩为一段连贯的摘要，"
                    "保留关键知识点、用户已提出的问题、已给出的答案要点。"
                ),
            },
            {
                "role": "user",
                "content": (
                    f"{previous}"
                    f"需要摘要的新对话:\n{dialogue_text}\n\n"
                    f"请输出整合后的完整摘要："
                ),
            },
        ]

        if self._llm:
            return await self._llm.chat(
                messages,
                temperature=0.3,
                max_tokens=512,
            )

        # 兜底：直接拼接
        return dialogue_text[:500]
