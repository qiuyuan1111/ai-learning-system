"""
辅导引擎测试

测试 TutorEngine 的核心逻辑：系统提示词构建、画像适配渲染。
"""

from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.models.dto import Attachment
from src.services.tutor_engine import TutorEngine


# ── Fixtures ────────────────────────────────────────────────────


@pytest.fixture
def mock_llm():
    return AsyncMock()


@pytest.fixture
def mock_profile_service():
    svc = AsyncMock()
    svc.get_profile = AsyncMock(return_value={
        "dimensions": {
            "knowledge_base": {"level": "intermediate", "confidence": 0.8},
            "cognitive_style": {"style": "practical", "confidence": 0.7},
            "learning_pace": {"pace": "moderate", "confidence": 0.6},
            "weakness_preferences": [
                {"weak_tags": ["注意力机制"], "description": "对注意力机制理解不够"}
            ],
            "interest_areas": [
                {"areas": ["NLP", "计算机视觉"]}
            ],
        }
    })
    return svc


@pytest.fixture
def mock_answer_generator():
    gen = AsyncMock()

    async def fake_generate_stream(system_prompt, messages, question, attachments):
        yield {"type": "text", "content": {"markdown": "这是关于"}}
        yield {"type": "text", "content": {"markdown": "注意力机制的解释。"}}
        yield {"type": "done", "content": {}}

    gen.generate_stream = fake_generate_stream
    return gen


@pytest.fixture
def mock_context_manager():
    cm = AsyncMock()
    cm.get_context = AsyncMock()
    cm.build_messages_for_llm = MagicMock(return_value=[
        {"role": "system", "content": "test"},
        {"role": "user", "content": "test question"},
    ])
    cm.append_round = AsyncMock()
    return cm


@pytest.fixture
def engine(mock_llm, mock_profile_service, mock_answer_generator, mock_context_manager):
    eng = TutorEngine(
        llm_service=mock_llm,
        profile_service=mock_profile_service,
        answer_generator=mock_answer_generator,
        context_manager=mock_context_manager,
    )
    # 预加载模板缓存
    eng._system_template = "你是一位AI老师。\n\n{{ ADAPT_PROMPT }}"
    eng._adapt_template = (
        "## 知识水平：{{ knowledge_level }}\n"
        "## 认知风格：{{ cognitive_style }}\n"
        "## 学习节奏：{{ learning_pace }}\n"
        "{% for weak in weakness_preferences %}\n- {{ weak }} —— 请重点讲解\n{% endfor %}\n"
        "{% for interest in interest_areas %}\n- {{ interest }}\n{% endfor %}"
    )
    return eng


# ── 测试：构建系统提示词 ────────────────────────────────────────


class TestBuildSystemPrompt:
    """系统提示词构建测试"""

    def test_with_full_profile(self, engine):
        """提供完整画像时，应该正确渲染所有维度"""
        profile = {
            "dimensions": {
                "knowledge_base": {"level": "advanced"},
                "cognitive_style": {"style": "theoretical"},
                "learning_pace": {"pace": "fast"},
                "weakness_preferences": [
                    {"weak_tags": ["Transformer"], "description": ""},
                ],
                "interest_areas": [
                    {"areas": ["LLM"]},
                ],
            }
        }
        adapt = engine._render_adapt_prompt(
            engine._adapt_template, profile,
        )
        assert "advanced" in adapt
        assert "theoretical" in adapt
        assert "fast" in adapt
        assert "Transformer" in adapt
        assert "LLM" in adapt

    def test_with_partial_profile(self, engine):
        """提供部分画像时，缺失字段应使用默认值"""
        profile = {
            "dimensions": {
                "knowledge_base": {"level": "beginner"},
                # 缺少 cognitive_style, learning_pace
                "weakness_preferences": [],
                "interest_areas": [],
            }
        }
        adapt = engine._render_adapt_prompt(
            engine._adapt_template, profile,
        )
        assert "beginner" in adapt
        assert "practical" in adapt  # 默认值
        assert "moderate" in adapt  # 默认值
        assert "暂无特别薄弱的领域" in adapt
        assert "暂无特别兴趣记录" in adapt

    def test_without_profile(self, engine):
        """没有画像时，应使用默认提示"""
        system_prompt = engine._build_system_prompt(
            "你是一位AI老师。\n\n{{ ADAPT_PROMPT }}",
            "请根据画像调整回答。",
            None,
        )
        assert "暂无用户画像信息" in system_prompt

    def test_system_prompt_integration(self, engine, mock_profile_service):
        """系统提示词应正确嵌入适配内容"""
        engine._system_template = "角色设定。\n\n{{ ADAPT_PROMPT }}"
        system_prompt = engine._build_system_prompt(
            engine._system_template,
            engine._adapt_template,
            {
                "dimensions": {
                    "knowledge_base": {"level": "intermediate"},
                    "cognitive_style": {"style": "visual"},
                    "learning_pace": {"pace": "slow"},
                    "weakness_preferences": [],
                    "interest_areas": [],
                }
            },
        )
        assert "角色设定。" in system_prompt
        assert "intermediate" in system_prompt
        assert "visual" in system_prompt
        assert "slow" in system_prompt


# ── 测试：生成回答 ───────────────────────────────────────────────


class TestGenerateAnswer:
    """问答生成流程测试"""

    @pytest.mark.asyncio
    async def test_generate_answer_success(self, engine):
        """生成回答应逐块返回 text 和 done"""
        chunks = []
        async for chunk in engine.generate_answer(
            session_id="test_session",
            question="什么是注意力机制？",
            attachments=[],
        ):
            chunks.append(chunk)

        assert len(chunks) >= 2
        assert chunks[-1]["type"] == "done"
        text_types = [c["type"] for c in chunks if c["type"] == "text"]
        assert len(text_types) > 0

    @pytest.mark.asyncio
    async def test_generate_answer_profile_error_graceful(self, engine):
        """画像服务失败时仍应继续生成回答"""
        engine.profile_service.get_profile = AsyncMock(
            side_effect=Exception("服务不可用"),
        )

        chunks = []
        async for chunk in engine.generate_answer(
            session_id="test_session",
            question="什么是注意力机制？",
            attachments=[],
        ):
            chunks.append(chunk)

        # 即使画像失败也应返回回答
        assert len(chunks) >= 2
        assert chunks[-1]["type"] == "done"

    @pytest.mark.asyncio
    async def test_generate_answer_context_saved(self, engine):
        """生成回答后应保存对话上下文"""
        chunks = []
        async for chunk in engine.generate_answer(
            session_id="test_session",
            question="什么是注意力机制？",
            attachments=[],
        ):
            chunks.append(chunk)

        engine.context_manager.append_round.assert_called_once()
        call_kwargs = engine.context_manager.append_round.call_args[1]
        assert call_kwargs["session_id"] == "test_session"
        assert call_kwargs["question"] == "什么是注意力机制？"


# ── 测试：渲染方法 ──────────────────────────────────────────────


class TestRenderAdaptPrompt:
    """画像适配渲染测试"""

    def test_empty_weakness(self, engine):
        """没有薄弱点时显示占位文本"""
        profile = {
            "dimensions": {
                "knowledge_base": {"level": "beginner"},
                "cognitive_style": {"style": "practical"},
                "learning_pace": {"pace": "moderate"},
                "weakness_preferences": [],
                "interest_areas": [],
            }
        }
        adapt = engine._render_adapt_prompt(engine._adapt_template, profile)
        assert "暂无特别薄弱的领域" in adapt

    def test_weakness_from_strings(self, engine):
        """weakness_preferences 为字符串列表时正常处理"""
        profile = {
            "dimensions": {
                "knowledge_base": {"level": "beginner"},
                "cognitive_style": {"style": "practical"},
                "learning_pace": {"pace": "moderate"},
                "weakness_preferences": ["Python基础"],
                "interest_areas": [],
            }
        }
        adapt = engine._render_adapt_prompt(engine._adapt_template, profile)
        assert "Python基础" in adapt
