"""防幻觉校验领域模型"""

from typing import List, Optional

from pydantic import BaseModel, Field


class HallucinatedClaim(BaseModel):
    """疑似幻觉声明"""
    claim: str
    evidence: str = ""
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class HallucinationVerdict(BaseModel):
    """防幻觉校验结果"""
    passed: bool
    hallucinatedClaims: List[HallucinatedClaim] = Field(default_factory=list)
    overallConfidence: float = Field(default=0.0, ge=0.0, le=1.0)


class HallucinationCheckResult(BaseModel):
    """完整防幻觉校验结果"""
    citationCheckPassed: bool = True
    citationIssues: List[str] = Field(default_factory=list)
    factConsistencyScore: float = Field(default=1.0, ge=0.0, le=1.0)
    factConsistencyIssues: List[str] = Field(default_factory=list)
    suggestion: str = ""
    verdict: HallucinationVerdict
