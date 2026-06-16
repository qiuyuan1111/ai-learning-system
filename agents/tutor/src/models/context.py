"""
对话上下文模型

定义多轮对话中的上下文数据结构。
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional


@dataclass
class DialogueRound:
    """一轮对话记录"""

    question: str
    answer: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    resource_id: Optional[str] = None
    course_id: Optional[str] = None


@dataclass
class DialogueContext:
    """完整对话上下文"""

    session_id: str
    rounds: List[DialogueRound] = field(default_factory=list)
    summary: Optional[str] = None  # 早期轮次的摘要
    summary_rounds: int = 0  # 已摘要的轮次数
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def add_round(self, question: str, answer: str, **kwargs) -> DialogueRound:
        """追加一轮对话"""
        r = DialogueRound(question=question, answer=answer, **kwargs)
        self.rounds.append(r)
        self.updated_at = datetime.now(timezone.utc)
        return r

    def has_recent_history(self) -> bool:
        """是否有最近对话历史"""
        return len(self.rounds) > 0 or self.summary is not None

    def total_rounds(self) -> int:
        """总轮次（含已摘要的）"""
        return len(self.rounds) + self.summary_rounds
