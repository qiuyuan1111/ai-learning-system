"""Schema 定义单元测试"""

import sys
import os
from pathlib import Path

# 确保项目根目录在 sys.path 中，支持 python test_file.py 直接执行
_root = str(Path(__file__).resolve().parent.parent)
if _root not in sys.path:
    sys.path.insert(0, _root)

import pytest
from datetime import datetime
from src.models.schema import (
    CognitiveStyle,
    CognitiveStyleDim,
    InterestArea,
    KnowledgeBase,
    KnowledgeLevel,
    LearningPace,
    LearningPaceDim,
    ProfileDimensions,
    TargetDifficulty,
    UserProfile,
    WeaknessPreference,
)


class TestKnowledgeBase:
    def test_create_knowledge_base(self):
        kb = KnowledgeBase(level=KnowledgeLevel.INTERMEDIATE, tags=["Python", "ML"], confidence=0.8)
        assert kb.level == KnowledgeLevel.INTERMEDIATE
        assert "Python" in kb.tags
        assert kb.confidence == 0.8

    def test_confidence_range(self):
        with pytest.raises(ValueError):
            KnowledgeBase(level=KnowledgeLevel.BEGINNER, confidence=1.5)
        with pytest.raises(ValueError):
            KnowledgeBase(level=KnowledgeLevel.BEGINNER, confidence=-0.1)


class TestProfileDimensions:
    def test_empty_dimensions(self):
        dims = ProfileDimensions()
        assert dims.filled_count == 0
        assert dims.is_complete() is False

    def test_missing_dimensions_returns_all(self):
        dims = ProfileDimensions()
        missing = dims.missing_dimensions()
        assert len(missing) == 6
        assert "knowledge_base" in missing

    def test_partial_fill(self):
        dims = ProfileDimensions(
            knowledge_base=KnowledgeBase(level=KnowledgeLevel.ADVANCED, tags=["Python"], confidence=0.9),
            cognitive_style=CognitiveStyleDim(style=CognitiveStyle.PRACTICAL, confidence=0.8),
        )
        assert dims.filled_count == 2
        missing = dims.missing_dimensions()
        assert len(missing) == 4

    def test_all_dimensions_complete(self):
        dims = ProfileDimensions(
            knowledge_base=KnowledgeBase(level=KnowledgeLevel.ADVANCED, tags=["Python"], confidence=0.9),
            cognitive_style=CognitiveStyleDim(style=CognitiveStyle.PRACTICAL, detail="喜欢动手", confidence=0.8),
            learning_pace=LearningPaceDim(pace=LearningPace.MODERATE, confidence=0.75),
            weakness_preferences=[WeaknessPreference(weak_tags=["NLP"], confidence=0.8)],
            interest_areas=[InterestArea(areas=["AI"], depth=4, confidence=0.85)],
            target_difficulty=TargetDifficulty(level=7, description="进阶", confidence=0.7),
        )
        assert dims.is_complete() is True
        assert dims.filled_count == 6
        assert len(dims.missing_dimensions()) == 0

    def test_low_confidence_makes_incomplete(self):
        dims = ProfileDimensions(
            knowledge_base=KnowledgeBase(level=KnowledgeLevel.BEGINNER, tags=[], confidence=0.3),
            cognitive_style=CognitiveStyleDim(style=CognitiveStyle.VERBAL, confidence=0.6),
            learning_pace=LearningPaceDim(pace=LearningPace.SLOW, confidence=0.9),
            weakness_preferences=[WeaknessPreference(weak_tags=["math"], confidence=0.9)],
            interest_areas=[InterestArea(areas=["science"], depth=2, confidence=0.9)],
            target_difficulty=TargetDifficulty(level=3, confidence=0.9),
        )
        assert dims.is_complete() is False  # knowledge_base 置信度太低
        assert "knowledge_base" in dims.missing_dimensions()


class TestUserProfile:
    def test_create_profile(self):
        dims = ProfileDimensions(
            knowledge_base=KnowledgeBase(level=KnowledgeLevel.BEGINNER, tags=[], confidence=0.5),
            cognitive_style=CognitiveStyleDim(style=CognitiveStyle.VISUAL, confidence=0.6),
            learning_pace=LearningPaceDim(pace=LearningPace.MODERATE, confidence=0.7),
            weakness_preferences=[WeaknessPreference(weak_tags=["data structures"], confidence=0.5)],
            interest_areas=[InterestArea(areas=["web dev"], depth=3, confidence=0.6)],
            target_difficulty=TargetDifficulty(level=5, confidence=0.5),
        )
        profile = UserProfile(session_id="test_001", dimensions=dims)
        assert profile.session_id == "test_001"
        assert profile.version == 1
        assert isinstance(profile.updated_at, datetime)

    def test_profile_defaults(self):
        profile = UserProfile(session_id="test_002", dimensions=ProfileDimensions())
        assert profile.raw_dialogue == []
        assert profile.version == 1

    def test_profile_version_increments(self):
        dims = ProfileDimensions()
        profile = UserProfile(session_id="test_003", dimensions=dims)
        profile.version += 1
        assert profile.version == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
