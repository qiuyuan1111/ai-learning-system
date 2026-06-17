"""用户画像 Schema 定义"""

from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
from datetime import datetime, timezone


class KnowledgeLevel(str, Enum):
    """知识水平枚举"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class CognitiveStyle(str, Enum):
    """认知风格枚举"""
    THEORETICAL = "theoretical"   # 理论推导型
    PRACTICAL = "practical"       # 实践应用型
    VISUAL = "visual"             # 视觉图像型
    VERBAL = "verbal"             # 语言阅读型


class LearningPace(str, Enum):
    """学习节奏枚举"""
    SLOW = "slow"
    MODERATE = "moderate"
    FAST = "fast"


class ProfileDimension(BaseModel):
    """画像维度基类，所有维度的通用置信度字段"""
    confidence: float = Field(ge=0.0, le=1.0, description="该维度的置信度 (0-1)")


class KnowledgeBase(ProfileDimension):
    """知识基础维度"""
    level: KnowledgeLevel
    tags: List[str] = Field(default_factory=list, description="已掌握的知识标签")


class CognitiveStyleDim(ProfileDimension):
    """认知风格维度"""
    style: CognitiveStyle
    detail: str = ""


class LearningPaceDim(ProfileDimension):
    """学习节奏维度"""
    pace: LearningPace
    preferred_session_minutes: int = 30


class WeaknessPreference(ProfileDimension):
    """易错点偏好维度"""
    weak_tags: List[str] = Field(default_factory=list, description="薄弱知识点标签")
    description: str = ""


class InterestArea(ProfileDimension):
    """兴趣领域维度"""
    areas: List[str] = Field(default_factory=list)
    depth: int = Field(ge=1, le=5, default=3)


class TargetDifficulty(ProfileDimension):
    """目标难度等级维度"""
    level: int = Field(ge=1, le=10, default=5)
    description: str = ""


class ProfileDimensions(BaseModel):
    """画像维度集合（至少 6 个维度）"""
    knowledge_base: Optional[KnowledgeBase] = None
    cognitive_style: Optional[CognitiveStyleDim] = None
    learning_pace: Optional[LearningPaceDim] = None
    weakness_preferences: List[WeaknessPreference] = Field(default_factory=list)
    interest_areas: List[InterestArea] = Field(default_factory=list)
    target_difficulty: Optional[TargetDifficulty] = None

    @property
    def filled_count(self) -> int:
        """返回已填充的维度数量（忽略列表型维度是否非空）"""
        count = 0
        if self.knowledge_base is not None:
            count += 1
        if self.cognitive_style is not None:
            count += 1
        if self.learning_pace is not None:
            count += 1
        if self.target_difficulty is not None:
            count += 1
        # 列表型维度只要有内容就算填充
        if self.weakness_preferences:
            count += 1
        if self.interest_areas:
            count += 1
        return count

    @property
    def total_dimensions(self) -> int:
        """总维度数"""
        return 6

    def is_complete(self, min_confidence: float = 0.7) -> bool:
        """判断所有维度是否已填充且置信度达标"""
        checks = []

        if self.knowledge_base is not None:
            checks.append(self.knowledge_base.confidence >= min_confidence)
        else:
            return False

        if self.cognitive_style is not None:
            checks.append(self.cognitive_style.confidence >= min_confidence)
        else:
            return False

        if self.learning_pace is not None:
            checks.append(self.learning_pace.confidence >= min_confidence)
        else:
            return False

        if self.weakness_preferences:
            checks.append(all(w.confidence >= min_confidence for w in self.weakness_preferences))
        else:
            return False

        if self.interest_areas:
            checks.append(all(i.confidence >= min_confidence for i in self.interest_areas))
        else:
            return False

        if self.target_difficulty is not None:
            checks.append(self.target_difficulty.confidence >= min_confidence)
        else:
            return False

        return all(checks)

    def missing_dimensions(self, min_confidence: float = 0.7) -> List[str]:
        """返回缺失或置信度不足的维度名称"""
        missing = []
        if self.knowledge_base is None or self.knowledge_base.confidence < min_confidence:
            missing.append("knowledge_base")
        if self.cognitive_style is None or self.cognitive_style.confidence < min_confidence:
            missing.append("cognitive_style")
        if self.learning_pace is None or self.learning_pace.confidence < min_confidence:
            missing.append("learning_pace")
        if not self.weakness_preferences or any(w.confidence < min_confidence for w in self.weakness_preferences):
            missing.append("weakness_preferences")
        if not self.interest_areas or any(i.confidence < min_confidence for i in self.interest_areas):
            missing.append("interest_areas")
        if self.target_difficulty is None or self.target_difficulty.confidence < min_confidence:
            missing.append("target_difficulty")
        return missing


class UserProfile(BaseModel):
    """完整用户画像"""
    session_id: str
    dimensions: ProfileDimensions
    raw_dialogue: List[str] = Field(default_factory=list, description="构建过程中的对话原文")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    version: int = 1
