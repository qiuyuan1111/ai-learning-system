"""Pydantic 数据模型 —— 与 TS 版 DTO 严格对应（见 work-person-c.md 3.2）。

所有字段名采用 camelCase，与 api.md 对外契约完全一致。
Pydantic v2 默认按字段名序列化；此处统一关闭额外字段（extra=forbid）以防脏数据。
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field

from .enums import (
    ErrorCodeEnum,
    PathNodeStatusEnum,
    ResourceTypeEnum,
    TaskStatusEnum,
)

T = TypeVar("T")


# ────────────────────── 通用响应体 ──────────────────────

class ApiResponse(BaseModel, Generic[T]):
    """通用 API 响应体（api.md 1.5）。"""

    model_config = ConfigDict(extra="forbid")

    code: int = Field(description="业务状态码，0 表示成功")
    message: str
    data: Optional[T] = None
    requestId: str


class PageInfo(BaseModel):
    """分页信息（api.md 1.5）。"""

    model_config = ConfigDict(extra="forbid")

    page: int = Field(ge=1, description="当前页码，从 1 开始")
    pageSize: int = Field(ge=1, description="每页记录数")
    total: int = Field(ge=0, description="总记录数")
    totalPages: int = Field(ge=0, description="总页数")


class PaginatedData(BaseModel, Generic[T]):
    """分页响应数据包装。"""

    model_config = ConfigDict(extra="forbid")

    list: List[T]
    pageInfo: PageInfo


# ────────────────────── 会话 ──────────────────────

class CreateSessionRequest(BaseModel):
    """创建会话请求（POST /sessions）。"""

    model_config = ConfigDict(extra="forbid")

    nickname: str
    major: str
    grade: str


class CreateSessionResponse(BaseModel):
    """创建会话响应 data。"""

    model_config = ConfigDict(extra="forbid")

    sessionId: str
    token: str
    profile: dict


# ────────────────────── 用户画像 ──────────────────────

class KnowledgeBase(BaseModel):
    model_config = ConfigDict(extra="forbid")
    level: str  # beginner | intermediate | advanced
    tags: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)


class CognitiveStyle(BaseModel):
    model_config = ConfigDict(extra="forbid")
    style: str  # theoretical | practical | visual | verbal
    detail: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0)


class LearningPace(BaseModel):
    model_config = ConfigDict(extra="forbid")
    pace: str  # slow | moderate | fast
    preferredSessionMinutes: Optional[int] = None
    confidence: float = Field(ge=0.0, le=1.0)


class WeaknessItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    weakTags: List[str] = Field(default_factory=list)
    description: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0)


class InterestItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    areas: List[str] = Field(default_factory=list)
    depth: int = Field(ge=1, le=5)
    confidence: float = Field(ge=0.0, le=1.0)


class TargetDifficulty(BaseModel):
    model_config = ConfigDict(extra="forbid")
    level: int = Field(ge=1, le=10)
    description: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0)


class ProfileDimensions(BaseModel):
    """用户画像 6 维度（api.md 5.4），各维度初始可为空。"""

    model_config = ConfigDict(extra="forbid")

    knowledgeBase: Optional[KnowledgeBase] = None
    cognitiveStyle: Optional[CognitiveStyle] = None
    learningPace: Optional[LearningPace] = None
    weaknessPreferences: Optional[List[WeaknessItem]] = None
    interestAreas: Optional[List[InterestItem]] = None
    targetDifficulty: Optional[TargetDifficulty] = None


class UserProfile(BaseModel):
    """用户画像。"""

    model_config = ConfigDict(extra="forbid")

    sessionId: str
    dimensions: ProfileDimensions
    updatedAt: str  # ISO8601
    version: int = 1


# ────────────────────── 资源 ──────────────────────

class Resource(BaseModel):
    """资源对象。"""

    model_config = ConfigDict(extra="forbid")

    resourceId: str
    type: ResourceTypeEnum
    title: str
    url: str
    thumbnailUrl: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[dict] = None
    createdAt: str  # ISO8601


class TaskResult(BaseModel):
    """任务完成后返回的资源列表。"""

    model_config = ConfigDict(extra="forbid")
    resources: List[Resource] = Field(default_factory=list)


class TaskError(BaseModel):
    """任务失败时的错误信息。"""

    model_config = ConfigDict(extra="forbid")
    code: int
    message: str


class TaskInfo(BaseModel):
    """异步任务定义（GET /resource-tasks/{taskId} 响应 data）。"""

    model_config = ConfigDict(extra="forbid")

    taskId: str
    status: TaskStatusEnum
    progress: int = Field(ge=0, le=100)
    progressDescription: Optional[str] = None
    result: Optional[TaskResult] = None
    error: Optional[TaskError] = None
    createdAt: str  # ISO8601
    updatedAt: str  # ISO8601


class TaskProgressContent(BaseModel):
    """WS 推送的任务进度消息 content（type=progress）。"""

    model_config = ConfigDict(extra="forbid")
    taskId: str
    progress: int
    description: str


# ────────────────────── 学习路径 ──────────────────────

class PathNodeResource(BaseModel):
    """节点绑定的资源摘要。"""

    model_config = ConfigDict(extra="forbid")
    resourceId: str
    type: ResourceTypeEnum
    url: str


class PathNode(BaseModel):
    """学习路径节点。"""

    model_config = ConfigDict(extra="forbid")

    nodeId: str
    order: int = Field(ge=1)
    title: str
    description: Optional[str] = None
    resource: Optional[PathNodeResource] = None
    status: PathNodeStatusEnum


class LearningPathResponse(BaseModel):
    """学习路径完整响应（GET /sessions/{sessionId}/learning-path）。"""

    model_config = ConfigDict(extra="forbid")
    pathId: str
    updatedAt: str  # ISO8601
    nodes: List[PathNode]


# ────────────────────── 评估 ──────────────────────

class AnswerItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    questionId: str
    answer: str
    timeSpent: int = Field(ge=0, description="作答耗时（秒）")


class BehaviorItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: str  # video_pause | video_forward | video_rewind | resource_view
    resourceId: str
    timestamp: str


class SubmitEvaluationRequest(BaseModel):
    """评估提交请求（POST /evaluation/submit）。"""

    model_config = ConfigDict(extra="forbid")
    sessionId: str
    quizId: str
    answers: List[AnswerItem] = Field(default_factory=list)
    behaviors: List[BehaviorItem] = Field(default_factory=list)


class EvaluationDimension(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    score: float
    maxScore: float


class WeakPoint(BaseModel):
    model_config = ConfigDict(extra="forbid")
    topic: str
    severity: int = Field(ge=1, le=5)
    description: str
    suggestion: Optional[str] = None


class EvaluationReport(BaseModel):
    """评估报告。"""

    model_config = ConfigDict(extra="forbid")
    dimensions: List[EvaluationDimension] = Field(default_factory=list)
    weakPoints: List[WeakPoint] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
