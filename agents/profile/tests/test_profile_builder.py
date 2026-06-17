"""画像构建服务单元测试"""

import sys
import os
from pathlib import Path

# 确保项目根目录在 sys.path 中，支持 python test_file.py 直接执行
_root = str(Path(__file__).resolve().parent.parent)
if _root not in sys.path:
    sys.path.insert(0, _root)

import pytest
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
from src.models.dto import ProfileBuildResult
from src.services.profile_builder import ProfileBuilder
from src.services.llm_service import LLMService


class FakeLLMService(LLMService):
    """测试用的 LLM 模拟服务"""

    def __init__(self):
        # 不调用父类 __init__，避免真实 API 调用
        self.model = "fake-model"

    async def chat_structured(self, messages: list, temperature: float = 0.7) -> dict:
        """模拟 LLM 返回预定义的结构化输出"""
        # 检查用户消息，返回合适的模拟响应
        user_msg = messages[-1]["content"] if messages else ""

        if "大三" in user_msg and "机器学习" in user_msg:
            return {
                "extracted": {
                    "knowledge_base": {
                        "level": "intermediate",
                        "tags": ["机器学习", "Python"],
                        "confidence": 0.85,
                    },
                    "cognitive_style": {
                        "style": "practical",
                        "detail": "喜欢动手做项目",
                        "confidence": 0.75,
                    },
                    "interest_areas": {
                        "areas": ["AI", "机器学习"],
                        "depth": 4,
                        "confidence": 0.8,
                    },
                },
                "reply": "听起来你已经有了不错的机器学习基础！你平时学习时是喜欢先看理论推导，还是直接动手做项目呢？",
                "is_complete": False,
            }
        elif "理论" in user_msg:
            return {
                "extracted": {
                    "cognitive_style": {
                        "style": "theoretical",
                        "detail": "偏好先理解原理再实践",
                        "confidence": 0.9,
                    },
                    "learning_pace": {
                        "pace": "moderate",
                        "preferred_session_minutes": 60,
                        "confidence": 0.7,
                    },
                },
                "reply": "了解！你倾向于先弄懂原理再动手。那在学习节奏上，你觉得自己是慢慢消化型还是快节奏型？",
                "is_complete": False,
            }
        elif "慢" in user_msg or "消化" in user_msg:
            return {
                "extracted": {
                    "learning_pace": {
                        "pace": "slow",
                        "preferred_session_minutes": 45,
                        "confidence": 0.85,
                    },
                    "weakness_preferences": [
                        {"weak_tags": ["数学推导"], "description": "复杂的数学推导容易混淆", "confidence": 0.7}
                    ],
                    "target_difficulty": {
                        "level": 6,
                        "description": "希望在中等难度上扎实掌握",
                        "confidence": 0.7,
                    },
                },
                "reply": "慢慢来反而学得更扎实！为了让学习计划更贴合你的需求，你目前有特别想攻克的薄弱环节吗？",
                "is_complete": True,
            }
        else:
            return {
                "extracted": {},
                "reply": "请多告诉我一些关于你的信息吧！",
                "is_complete": False,
            }


@pytest.fixture
def builder():
    llm = FakeLLMService()
    return ProfileBuilder(llm)


@pytest.mark.asyncio
async def test_process_first_message(builder):
    """测试首次消息处理"""
    result = await builder.process_message(
        session_id="test_sid",
        user_text="我是人工智能大三学生，刚学完吴恩达机器学习",
        current_profile=None,
    )

    assert isinstance(result, ProfileBuildResult)
    assert result.updated_profile.session_id == "test_sid"
    assert result.updated_profile.dimensions.knowledge_base is not None
    assert result.updated_profile.dimensions.knowledge_base.level == KnowledgeLevel.INTERMEDIATE
    assert "机器学习" in result.updated_profile.dimensions.knowledge_base.tags
    assert result.reply_text != ""
    assert result.is_complete is False


@pytest.mark.asyncio
async def test_process_second_message(builder):
    """测试第二轮对话，补充认知风格和学习节奏"""
    # 先构建一个部分画像
    dims = ProfileDimensions(
        knowledge_base=KnowledgeBase(level=KnowledgeLevel.INTERMEDIATE, tags=["ML"], confidence=0.8),
    )
    profile = UserProfile(session_id="test_sid", dimensions=dims)

    result = await builder.process_message(
        session_id="test_sid",
        user_text="我比较喜欢先理解理论再动手实践",
        current_profile=profile,
    )

    assert result.updated_profile.dimensions.knowledge_base is not None
    assert result.updated_profile.dimensions.cognitive_style is not None
    assert result.updated_profile.dimensions.cognitive_style.style == CognitiveStyle.THEORETICAL
    assert result.updated_profile.dimensions.learning_pace is not None
    assert result.is_complete is False


@pytest.mark.asyncio
async def test_process_complete_profile(builder):
    """测试画像构建完成场景"""
    # 构建已有 4 个维度，需要补充剩下的
    dims = ProfileDimensions(
        knowledge_base=KnowledgeBase(level=KnowledgeLevel.INTERMEDIATE, tags=["Python"], confidence=0.9),
        cognitive_style=CognitiveStyleDim(style=CognitiveStyle.THEORETICAL, confidence=0.85),
        learning_pace=LearningPaceDim(pace=LearningPace.MODERATE, confidence=0.8),
        weakness_preferences=[WeaknessPreference(weak_tags=["NLP"], confidence=0.75)],
        interest_areas=[InterestArea(areas=["AI"], depth=3, confidence=0.8)],
    )
    profile = UserProfile(session_id="test_sid", dimensions=dims)

    result = await builder.process_message(
        session_id="test_sid",
        user_text="我学习速度比较慢，需要多点时间消化",
        current_profile=profile,
    )

    assert result.is_complete is True
    assert result.updated_profile.dimensions.target_difficulty is not None


@pytest.mark.asyncio
async def test_new_profile_has_raw_dialogue(builder):
    """测试画像构建过程中记录对话原文"""
    result = await builder.process_message(
        session_id="test_sid",
        user_text="我是人工智能大三学生",
        current_profile=None,
    )

    assert len(result.updated_profile.raw_dialogue) == 2
    assert "user: 我是人工智能大三学生" in result.updated_profile.raw_dialogue
    assert "assistant:" in result.updated_profile.raw_dialogue[1]


@pytest.mark.asyncio
async def test_profile_version_increments(builder):
    """测试每次处理递增版本号"""
    profile = UserProfile(session_id="test_sid", dimensions=ProfileDimensions())
    v1 = profile.version

    result = await builder.process_message(
        session_id="test_sid",
        user_text="我是人工智能大三学生",
        current_profile=profile,
    )

    assert result.updated_profile.version > v1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
