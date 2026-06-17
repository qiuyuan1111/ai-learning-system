"""对话记忆存储"""

from collections import defaultdict, deque
from typing import Any, Dict, List, Optional


class DialogueMemory:
    """对话记忆存储（环形缓冲区）

    存储每个 session 最近 N 轮的对话历史，用于画像构建和更新时的上下文参考。
    """

    def __init__(self, max_size: int = 50):
        self._storage: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_size))
        self.max_size = max_size

    def add(self, session_id: str, turn: Dict[str, Any]) -> None:
        """添加一轮对话到指定 session 的记忆中"""
        self._storage[session_id].append(turn)

    def get_history(self, session_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取指定 session 的对话历史，最新的在前"""
        history = list(self._storage.get(session_id, []))
        if limit:
            history = history[-limit:]
        return history

    def clear(self, session_id: str) -> None:
        """清空指定 session 的记忆"""
        self._storage.pop(session_id, None)

    def clear_all(self) -> None:
        """清空所有记忆"""
        self._storage.clear()
