"""请求/响应 DTO 定义

遵循统一 API 响应格式（code, message, data, requestId）。
安全模块专用错误码:
- 3001: 内容安全违规
- 3002: 检测到幻觉
"""

import uuid
from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

from .safety import SafetyCheckResult, SafetyVerdict
from .hallucination import HallucinationCheckResult, HallucinationVerdict

T = TypeVar("T")


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


class SafetyCheckRequest(BaseModel):
    """安全审核请求体"""
    text: str = Field(..., description="待审核的文本内容")
    context: str = Field("", description="可选的上下文说明，帮助判别误报")
    source: str = Field("", description="内容来源标识（tutor / evaluator / profile）")


class SafetyCheckResponse(BaseModel):
    """安全审核响应 data"""
    passed: bool
    riskLevel: str
    violatedRules: List[str] = Field(default_factory=list)
    suggestion: str = ""
    filterResults: SafetyCheckResult


class HallucinationCheckRequest(BaseModel):
    """防幻觉校验请求体"""
    text: str = Field(..., description="待校验的生成文本")
    sessionId: str = Field("", description="会话 ID，用于获取画像")
    sourceMaterial: str = Field("", description="参考来源文本（如有）")
    dialogueHistory: List[dict] = Field(default_factory=list, description="对话历史")


class HallucinationCheckResponse(BaseModel):
    """防幻觉校验响应 data"""
    passed: bool
    overallConfidence: float
    hallucinatedClaims: List[dict] = Field(default_factory=list)
    suggestion: str = ""
    guardResult: HallucinationVerdict
