"""ai_edu_common —— Python 版共享库（与 TS 版 @ai-edu/common 契约一致）。

统一出口，调用方：`from ai_edu_common import Resource, success, IdGenerator, ...`
"""
from __future__ import annotations

from .enums import (
    ErrorCodeEnum,
    IntentEnum,
    PathNodeStatusEnum,
    ResourceTypeEnum,
    TaskStatusEnum,
)
from .ids import IdGenerator
from .json_utils import JsonUtils
from .models import (
    AnswerItem,
    ApiResponse,
    BehaviorItem,
    CognitiveStyle,
    CreateSessionRequest,
    CreateSessionResponse,
    EvaluationDimension,
    EvaluationReport,
    InterestItem,
    KnowledgeBase,
    LearningPace,
    LearningPathResponse,
    PaginatedData,
    PageInfo,
    PathNode,
    PathNodeResource,
    ProfileDimensions,
    Resource,
    SubmitEvaluationRequest,
    TargetDifficulty,
    TaskError,
    TaskInfo,
    TaskProgressContent,
    TaskResult,
    UserProfile,
    WeakPoint,
    WeaknessItem,
)
from .response import error, paginated, success

__all__ = [
    # 枚举
    "IntentEnum",
    "ResourceTypeEnum",
    "TaskStatusEnum",
    "PathNodeStatusEnum",
    "ErrorCodeEnum",
    # 工具
    "IdGenerator",
    "JsonUtils",
    # 响应/分页
    "ApiResponse",
    "success",
    "error",
    "PageInfo",
    "PaginatedData",
    "paginated",
    # 会话
    "CreateSessionRequest",
    "CreateSessionResponse",
    # 画像
    "UserProfile",
    "ProfileDimensions",
    "KnowledgeBase",
    "CognitiveStyle",
    "LearningPace",
    "WeaknessItem",
    "InterestItem",
    "TargetDifficulty",
    # 资源
    "Resource",
    # 任务
    "TaskInfo",
    "TaskResult",
    "TaskError",
    "TaskProgressContent",
    # 路径
    "PathNode",
    "PathNodeResource",
    "LearningPathResponse",
    # 评估
    "SubmitEvaluationRequest",
    "AnswerItem",
    "BehaviorItem",
    "EvaluationReport",
    "EvaluationDimension",
    "WeakPoint",
]
