"""
答案生成服务测试

测试 AnswerGenerator 的附件处理、多模态降级等逻辑。
"""

from typing import Any, AsyncGenerator, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.models.dto import Attachment
from src.services.answer_generator import AnswerGenerator


# ── Fixtures ────────────────────────────────────────────────────


@pytest.fixture
def mock_llm():
    llm = AsyncMock()

    async def fake_stream(messages, temperature=0.7):
        yield "你好，"
        yield "这是一个"
        yield "测试回答。"

    llm.chat_stream = fake_stream

    # mock 客户端用于图片描述
    llm.client = AsyncMock()
    llm.client.chat = AsyncMock()
    llm.client.chat.completions = AsyncMock()

    mock_response = AsyncMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content="这是一张包含图表的图片。")),
    ]
    llm.client.chat.completions.create = AsyncMock(return_value=mock_response)

    return llm


@pytest.fixture
def generator(mock_llm):
    return AnswerGenerator(llm_service=mock_llm)


# ── 测试：基础流式生成 ──────────────────────────────────────────


class TestGenerateStream:
    """流式生成基本功能测试"""

    @pytest.mark.asyncio
    async def test_generate_text_stream(self, generator):
        """应逐块返回文本并最终 done"""
        messages = [
            {"role": "system", "content": "你是一个助手"},
            {"role": "user", "content": "请回答"},
        ]
        chunks = []
        async for chunk in generator.generate_stream(
            system_prompt="test",
            messages=messages,
            question="请回答",
            attachments=[],
        ):
            chunks.append(chunk)

        assert len(chunks) >= 2
        assert chunks[-1]["type"] == "done"
        # 验证文本块
        text_chunks = [c for c in chunks if c["type"] == "text"]
        assert len(text_chunks) > 0


# ── 测试：附件处理 ──────────────────────────────────────────────


class TestProcessAttachments:
    """附件处理逻辑测试"""

    def test_no_attachments(self, generator):
        """没有附件时消息列表不变"""
        messages = [{"role": "user", "content": "你好"}]
        result = generator._build_multimodal_messages(messages, [])
        assert result == messages

    def test_multimodal_message_structure(self, generator):
        """多模态消息应包含 text 和 image_url 两部分"""
        messages = [{"role": "user", "content": "描述这张图片"}]
        images = [
            Attachment(type="image", url="https://example.com/img.png", mimeType="image/png"),
        ]
        result = generator._build_multimodal_messages(messages, images)

        assert len(result) == 1
        content = result[0]["content"]
        assert isinstance(content, list)
        assert len(content) == 2
        assert content[0]["type"] == "text"
        assert content[1]["type"] == "image_url"
        assert content[1]["image_url"]["url"] == "https://example.com/img.png"

    def test_multimodal_multiple_images(self, generator):
        """支持多个图片附件"""
        messages = [{"role": "user", "content": "比较这两张图"}]
        images = [
            Attachment(type="image", url="https://example.com/a.png", mimeType="image/png"),
            Attachment(type="image", url="https://example.com/b.png", mimeType="image/png"),
        ]
        result = generator._build_multimodal_messages(messages, images)

        content = result[0]["content"]
        assert isinstance(content, list)
        assert len(content) == 3  # text + 2 images
        assert content[1]["image_url"]["url"] == "https://example.com/a.png"
        assert content[2]["image_url"]["url"] == "https://example.com/b.png"

    @pytest.mark.asyncio
    async def test_describe_image_fallback(self, generator):
        """非多模态模型的降级处理"""
        messages = [{"role": "user", "content": "描述这张图"}]
        images = [
            Attachment(type="image", url="https://example.com/chart.png", mimeType="image/png"),
        ]

        # 模拟非多模态模型
        with patch.object(generator.llm, "client") as mock_client:
            mock_response = AsyncMock()
            mock_response.choices = [
                MagicMock(message=MagicMock(content="这是一张数据图表。")),
            ]
            mock_client.chat.completions.create = AsyncMock(
                return_value=mock_response,
            )

            result = await generator._build_described_messages(messages, images)

            assert len(result) == 1
            content = result[0]["content"]
            assert "图片" in content or "图表" in content

    @pytest.mark.asyncio
    async def test_describe_image_error_graceful(self, generator):
        """图片描述失败时应给出友好占位"""
        messages = [{"role": "user", "content": "描述"}]
        images = [
            Attachment(type="image", url="https://example.com/bad.png", mimeType="image/png"),
        ]

        with patch.object(generator.llm, "client") as mock_client:
            mock_client.chat.completions.create = AsyncMock(
                side_effect=Exception("API error"),
            )
            result = await generator._build_described_messages(messages, images)

            assert len(result) == 1
            content = result[0]["content"]
            assert "无法自动描述" in content


# ── 测试：工具方法 ──────────────────────────────────────────────


class TestUtils:
    """工具方法测试"""

    def test_attachment_summary(self, generator):
        """附件摘要应包含类型和 MIME 信息"""
        attachments = [
            Attachment(type="image", url="https://example.com/a.png", mimeType="image/png"),
            Attachment(type="file", url="https://example.com/b.pdf", mimeType="application/pdf"),
        ]
        summary = generator.get_attachment_summary(attachments)
        assert "image" in summary
        assert "pdf" in summary

    def test_attachment_summary_empty(self, generator):
        """没有附件时返回空字符串"""
        assert generator.get_attachment_summary([]) == ""
