"""path-planner 测试公共夹具。"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


@pytest.fixture
def sample_user_profile():
    """构造一个 UserProfile（pydantic 模型）。"""
    from ai_edu_common import (
        CognitiveStyle,
        KnowledgeBase,
        LearningPace,
        ProfileDimensions,
        UserProfile,
    )

    return UserProfile(
        sessionId="sess_demo",
        dimensions=ProfileDimensions(
            knowledgeBase=KnowledgeBase(
                level="intermediate", tags=["Python"], confidence=0.8
            ),
            cognitiveStyle=CognitiveStyle(style="practical", confidence=0.6),
            learningPace=LearningPace(pace="moderate", confidence=0.5),
            weaknessPreferences=[{"weakTags": ["注意力机制"], "confidence": 0.7}],
            interestAreas=[{"areas": ["NLP"], "depth": 3, "confidence": 0.6}],
            targetDifficulty={"level": 7, "confidence": 0.5},
        ),
        updatedAt="2026-06-15T10:00:00Z",
        version=1,
    )


@pytest.fixture
def sample_resources():
    from ai_edu_common import Resource
    from ai_edu_common.enums import ResourceTypeEnum

    return [
        Resource(
            resourceId="res_1",
            type=ResourceTypeEnum.PPT,
            title="注意力机制详解",
            url="http://x/attn.pptx",
            description="Self-Attention、Multi-Head",
            createdAt="2026-06-15T10:00:00Z",
        ),
        Resource(
            resourceId="res_2",
            type=ResourceTypeEnum.DOC,
            title="Python 基础回顾",
            url="http://x/py.md",
            createdAt="2026-06-15T10:00:00Z",
        ),
    ]
