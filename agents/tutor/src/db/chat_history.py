"""
对话历史存储

基于文件的 JSON 持久化方案。
每个会话一个文件，使用 aiofiles 实现异步文件 I/O。
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional

import aiofiles

from src.config import config
from src.models.context import DialogueContext, DialogueRound

logger = logging.getLogger(__name__)

# JSON 序列化格式
_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


def _utcnow() -> str:
    """返回 UTC 当前时间的格式化字符串"""
    return datetime.now(timezone.utc).strftime(_DATETIME_FORMAT)


class ChatHistoryStore:
    """
    对话历史存储

    按 session_id 将 DialogueContext 持久化为 JSON 文件。
    每个会话一个独立文件，所有 I/O 操作均为异步。
    """

    def __init__(self, data_dir: Optional[str] = None):
        self.data_dir = data_dir or config.data_dir
        os.makedirs(self.data_dir, exist_ok=True)

    def _file_path(self, session_id: str) -> str:
        """获取会话对应的文件路径"""
        safe_name = session_id.replace("/", "_").replace("\\", "_")
        return os.path.join(self.data_dir, f"session_{safe_name}.json")

    def _path_exists(self, path: str) -> bool:
        """同步检查文件是否存在（__init__ 中调用，无需异步）"""
        return os.path.exists(path)

    async def load_context(self, session_id: str) -> Optional[DialogueContext]:
        """
        从文件加载 DialogueContext

        返回: DialogueContext 实例，文件不存在时返回 None
        """
        path = self._file_path(session_id)
        if not os.path.exists(path):
            return None

        try:
            async with aiofiles.open(path, "r", encoding="utf-8") as f:
                content = await f.read()
            data = json.loads(content)

            rounds = [
                DialogueRound(
                    question=r["question"],
                    answer=r["answer"],
                    timestamp=datetime.strptime(r["timestamp"], _DATETIME_FORMAT),
                    resource_id=r.get("resource_id"),
                    course_id=r.get("course_id"),
                )
                for r in data.get("rounds", [])
            ]

            context = DialogueContext(
                session_id=data["session_id"],
                rounds=rounds,
                summary=data.get("summary"),
                summary_rounds=data.get("summary_rounds", 0),
                created_at=datetime.strptime(
                    data.get("created_at", _utcnow()),
                    _DATETIME_FORMAT,
                ),
                updated_at=datetime.strptime(
                    data.get("updated_at", _utcnow()),
                    _DATETIME_FORMAT,
                ),
            )
            return context

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning("加载会话 %s 失败，将重建: %s", session_id, e)
            return None

    async def save_context(self, context: DialogueContext):
        """将 DialogueContext 持久化到文件"""
        path = self._file_path(context.session_id)

        data = {
            "session_id": context.session_id,
            "summary": context.summary,
            "summary_rounds": context.summary_rounds,
            "created_at": context.created_at.strftime(_DATETIME_FORMAT),
            "updated_at": context.updated_at.strftime(_DATETIME_FORMAT),
            "rounds": [
                {
                    "question": r.question,
                    "answer": r.answer,
                    "timestamp": r.timestamp.strftime(_DATETIME_FORMAT),
                    "resource_id": r.resource_id,
                    "course_id": r.course_id,
                }
                for r in context.rounds
            ],
        }

        # 原子写入：先写临时文件再重命名
        tmp_path = path + ".tmp"
        async with aiofiles.open(tmp_path, "w", encoding="utf-8") as f:
            await f.write(json.dumps(data, ensure_ascii=False, indent=2))

        os.replace(tmp_path, path)

    async def delete_context(self, session_id: str):
        """删除指定会话的历史记录"""
        path = self._file_path(session_id)
        if os.path.exists(path):
            os.remove(path)
            logger.info("已删除会话 %s 的历史记录", session_id)

    async def list_sessions(self) -> List[str]:
        """列出所有有历史记录的会话 ID"""
        sessions = []
        for fname in os.listdir(self.data_dir):
            if fname.startswith("session_") and fname.endswith(".json"):
                session_id = fname[len("session_"):-len(".json")]
                sessions.append(session_id)
        return sessions

    async def get_stats(self) -> Dict[str, int]:
        """获取存储统计信息"""
        sessions = await self.list_sessions()
        total_rounds = 0
        for sid in sessions:
            ctx = await self.load_context(sid)
            if ctx:
                total_rounds += ctx.total_rounds()
        return {
            "session_count": len(sessions),
            "total_rounds": total_rounds,
        }
