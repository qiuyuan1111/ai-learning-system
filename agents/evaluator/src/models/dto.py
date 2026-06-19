"""请求/响应 DTO 定义

遵循 common/ 中定义的统一 API 响应格式（code, message, data, requestId）。
"""

import uuid
from typing import Any, Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

from .evaluation import Answer, Behavior, DimensionScore, PathAdjustment, WeakPoint

T = TypeVar("T")


# ── 通用 API 响应 ────────────────────────────────────────────────


class ApiResponse(BaseModel, Generic[T]):
    """统一 API 响应体"""

    code: int = 0
    message: str = "success"
    data: Optional[T] = None
    requestId: str = ""


def success(data: T, request_id: str = "") -> ApiResponse[T]:
    """构造成功响应"""
    return ApiResponse(
        code=0,
        message="success",
        data=data,
        requestId=request_id or str(uuid.uuid4()),
    )


def error(code: int, message: str, request_id: str = "") -> ApiResponse[Any]:
    """构造失败响应"""
    return ApiResponse(
        code=code,
        message=message,
        data=None,
        requestId=request_id or str(uuid.uuid4()),
    )


# ── 评估提交 ──────────────────────────────────────────────────────


class EvaluationSubmitRequest(BaseModel):
    """提交评估数据请求体"""

    sessionId: str
    quizId: str = ""
    answers: List[Answer] = Field(default_factory=list)
    behaviors: List[Behavior] = Field(default_factory=list)


class EvaluationSubmitData(BaseModel):
    """提交评估数据响应 data"""

    evaluationId: str
    status: str = "processing"


# ── 评估报告 ──────────────────────────────────────────────────────


class EvaluationReport(BaseModel):
    """评估报告 data"""

    dimensions: List[DimensionScore] = Field(default_factory=list)
    weakPoints: List[WeakPoint] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    pathAdjustments: List[PathAdjustment] = Field(default_factory=list)
