"""评估领域模型

定义评估流程中使用的核心数据结构。
评估维度:
1. knowledge_mastery（基础知识掌握）— 答题正确率
2. understanding_depth（理解深度）— 复杂问题表现
3. application_ability（应用能力）— 能否举一反三
4. learning_efficiency（学习效率) — 单位时间掌握量
5. engagement（专注度）— 行为数据反映的投入程度
"""

from typing import List, Optional
from datetime import datetime, timezone

from pydantic import BaseModel, Field


# ── 数据来源（输入） ──────────────────────────────────────────────


class Answer(BaseModel):
    """单道答题数据"""

    questionId: str
    answer: str
    timeSpent: int = Field(ge=0, description="耗时（秒）")
    correctAnswer: Optional[str] = None
    isCorrect: Optional[bool] = None
    questionType: str = "choice"  # choice | fill | essay
    topic: str = ""  # 关联知识点
    difficulty: int = Field(default=1, ge=1, le=10, description="题目难度")


class Behavior(BaseModel):
    """单条行为数据"""

    action: str  # video_pause | video_seek_forward | video_seek_back | resource_view | code_edit
    resourceId: str = ""
    timestamp: Optional[str] = None
    detail: Optional[dict] = None  # 额外信息，如暂停位置、快进秒数等


# ── 中间结果 ─────────────────────────────────────────────────────


class QuizResult(BaseModel):
    """答题评分结果"""

    totalScore: float = 0.0
    maxScore: float = 0.0
    details: List[dict] = Field(default_factory=list)
    wrongTopics: List[str] = Field(default_factory=list)


class BehaviorScore(BaseModel):
    """行为分析得分"""

    learningEfficiency: float = Field(default=0.0, ge=0.0, le=1.0)
    engagement: float = Field(default=0.0, ge=0.0, le=1.0)
    details: dict = Field(default_factory=dict)


# ── 评估结果 ────────────────────────────────────────────────────


class DimensionScore(BaseModel):
    """单维度评分"""

    name: str
    score: float = Field(ge=0.0, le=100.0)
    maxScore: float = 100.0


class WeakPoint(BaseModel):
    """薄弱点"""

    topic: str
    severity: int = Field(ge=1, le=5, description="严重程度 1-5")
    description: str = ""
    suggestion: str = ""


class Suggestion(BaseModel):
    """改进建议"""

    content: str


class PathAdjustment(BaseModel):
    """路径调整建议"""

    nodeId: str
    action: str  # add | remove | reorder
    title: str = ""


class EvaluationResult(BaseModel):
    """完整评估结果"""

    sessionId: str
    dimensions: List[DimensionScore] = Field(default_factory=list)
    weakPoints: List[WeakPoint] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    pathAdjustments: List[PathAdjustment] = Field(default_factory=list)
    createdAt: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
