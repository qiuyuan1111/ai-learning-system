"""路径规划 —— 内部 DTO 与上下文。对外契约复用 ai_edu_common。"""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class ProfileAnalysis(BaseModel):
    """画像分析结果（_analyze_profile 产出，内部使用）。"""

    model_config = ConfigDict(extra="allow")
    startingPoint: str = "基础知识"
    goalTopics: List[str] = []
    focusAreas: List[str] = []
    estimatedDuration: int = 60


class PathAdjustment(BaseModel):
    """路径调整动作（add / modify / remove / reorder）。"""

    model_config = ConfigDict(extra="forbid")
    nodeId: str
    action: str  # add | modify | remove | reorder
    title: Optional[str] = None
    afterNodeId: Optional[str] = None
