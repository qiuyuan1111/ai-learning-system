"""测试配置与夹具"""

import os

os.environ["LLM_API_KEY"] = "sk-placeholder-do-not-commit-real-key"
os.environ["LLM_MODEL"] = "gpt-4o-mini"
os.environ["ENABLE_KEYWORD_FILTER"] = "true"
os.environ["ENABLE_LLM_MODERATION"] = "false"
os.environ["ENABLE_CITATION_CHECK"] = "true"
os.environ["ENABLE_CONFIDENCE_EVAL"] = "false"

from unittest.mock import AsyncMock
import pytest

from src.services.safety_filter import ContentSafetyFilter
from src.services.hallucination_guard import HallucinationGuard


@pytest.fixture
def mock_llm_service():
    mock = AsyncMock()
    mock.chat = AsyncMock(return_value="模拟回复")
    mock.chat_structured = AsyncMock(return_value={
        "isViolation": False,
        "riskLevel": "safe",
        "reason": "",
        "suggestion": "",
    })
    return mock


@pytest.fixture
def safety_filter(mock_llm_service):
    return ContentSafetyFilter(llm_service=mock_llm_service)


@pytest.fixture
def hallucination_guard(mock_llm_service):
    return HallucinationGuard(llm_service=mock_llm_service)
