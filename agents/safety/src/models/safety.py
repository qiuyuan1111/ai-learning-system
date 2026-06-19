"""内容安全审核领域模型"""

from typing import List, Optional

from pydantic import BaseModel, Field


class SafetyVerdict(BaseModel):
    """安全审核结果"""
    passed: bool
    riskLevel: str = Field(..., pattern="^(safe|suspect|violation)$")
    violatedRules: List[str] = Field(default_factory=list)
    suggestion: str = ""


class KeywordMatch(BaseModel):
    """关键词匹配结果"""
    keyword: str
    category: str = "default"
    position: int = 0


class SafetyCheckResult(BaseModel):
    """完整安全审核结果"""
    keywordHits: List[KeywordMatch] = Field(default_factory=list)
    llmModerationScore: float = Field(default=0.0, ge=0.0, le=1.0)
    ruleMatches: List[str] = Field(default_factory=list)
    verdict: SafetyVerdict
