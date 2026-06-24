"""资源生成编排器 —— 请求/响应 DTO（见 work-person-c.md 4.4）。

复用 ai_edu_common 的契约模型，避免重复定义、保证全系统口径一致。
"""
from __future__ import annotations

from typing import List, Optional

from ai_edu_common import Resource, TaskInfo  # noqa: F401  (re-export)
from ai_edu_common.enums import ResourceTypeEnum
from pydantic import BaseModel, ConfigDict, Field, model_validator


class GenerationRequest(BaseModel):
    """资源生成请求体（POST /sessions/{sessionId}/resources/generate）。"""

    model_config = ConfigDict(extra="forbid")

    text: str = Field(..., description="用户需求描述，如「生成BERT模型的讲解PPT」")
    resourceType: str = Field(default="ppt", description="目标资源类型: ppt|pdf|doc|mindmap")
    profile: Optional[dict] = Field(default=None, description="用户画像（可选）")


class OutlineSection(BaseModel):
    """大纲章节。"""

    model_config = ConfigDict(extra="allow")  # LLM 产出结构允许少量额外字段

    order: float = 0.0  # LLM 偶尔漏返回 order，给默认值容错
    title: str
    description: Optional[str] = None
    estimatedMinutes: Optional[int] = None
    subsections: Optional[List["OutlineSection"]] = None

    @model_validator(mode="before")
    @classmethod
    def _coerce_str(cls, data):
        """LLM 有时把子节返回成纯字符串（如「什么是机器学习？」），
        这里容错：把字符串自动包装成 {title: <该字符串>}。"""
        if isinstance(data, str):
            return {"title": data}
        return data


class Outline(BaseModel):
    """大纲结构（阶段①产出物）。"""

    model_config = ConfigDict(extra="allow")
    title: str
    sections: List[OutlineSection] = Field(default_factory=list)


class SectionContent(BaseModel):
    """章节撰写内容（阶段②产出物）。"""

    model_config = ConfigDict(extra="forbid")
    title: str
    order: float
    markdown: str


class SlideData(BaseModel):
    """单张幻灯片数据（阶段③产出物）。"""

    model_config = ConfigDict(extra="forbid")
    layout: str = "content"  # cover|section|content|comparison|code|summary
    title: str
    bullets: List[str] = Field(default_factory=list)
    notes: Optional[str] = None


class ReviewResult(BaseModel):
    """审核结果（阶段⑤产出物）。"""

    model_config = ConfigDict(extra="forbid")
    passed: bool
    code: int = 0  # 0 通过；3001 违规；3002 幻觉
    message: str = "success"
    resource: Optional[Resource] = None


# 前向引用修正
OutlineSection.model_rebuild()
