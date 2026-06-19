"""resource-gen 单元测试 —— 各子智能体单独验证。"""
from __future__ import annotations

import pytest

from src.models.dto import Outline, SectionContent
from src.orchestrator.content_writer import ContentWriter
from src.orchestrator.doc_renderer import DocRenderer
from src.orchestrator.outline_generator import OutlineGenerator
from src.orchestrator.ppt_renderer import PptRenderer
from src.orchestrator.review_checker import ReviewChecker
from src.services.llm_service import MockLlmService, _extract_json


# ───────── LLM / JSON 解析 ─────────
class TestLlmService:
    @pytest.mark.asyncio
    async def test_mock_outline(self):
        llm = MockLlmService()
        data = await llm.chat_json("[OUTLINE] 生成BERT讲解")
        assert "title" in data and "sections" in data

    @pytest.mark.asyncio
    async def test_mock_content(self):
        llm = MockLlmService()
        text = await llm.chat("[CONTENT] 章节: Transformer回顾")
        assert "Transformer回顾" in text

    def test_extract_json_from_codeblock(self):
        out = _extract_json('```json\n{"a": 1}\n```')
        assert out == {"a": 1}

    def test_extract_json_embedded(self):
        out = _extract_json('前言 {"b": 2} 后语')
        assert out == {"b": 2}


# ───────── ① 大纲生成 ─────────
class TestOutlineGenerator:
    @pytest.mark.asyncio
    async def test_generate_outline(self, sample_profile):
        gen = OutlineGenerator(MockLlmService())
        outline = await gen.generate("生成BERT讲解PPT", sample_profile)
        assert isinstance(outline, Outline)
        assert outline.title
        assert len(outline.sections) >= 2


# ───────── ② 内容撰写 ─────────
class TestContentWriter:
    @pytest.mark.asyncio
    async def test_write_all_parallel(self, sample_profile):
        outline = Outline(
            title="测试",
            sections=[
                {"order": 1, "title": "A"},
                {"order": 2, "title": "B"},
                {"order": 3, "title": "C"},
            ],
        )
        # Outline 需 model_validate 才完整
        from src.models.dto import Outline as OL

        outline = OL.model_validate({"title": "测试", "sections": [
            {"order": 1, "title": "A"},
            {"order": 2, "title": "B"},
            {"order": 3, "title": "C"},
        ]})
        writer = ContentWriter(MockLlmService())
        results = await writer.write_all(outline, sample_profile)
        assert len(results) == 3
        assert all(isinstance(r, SectionContent) for r in results)


# ───────── ③ PPT 渲染 ─────────
class TestPptRenderer:
    def test_arrange_slides(self):
        renderer = PptRenderer()
        sections = [
            SectionContent(title="第一章", order=1, markdown="- 要点1\n- 要点2"),
        ]
        slides = renderer.arrange_slides("测试PPT", sections)
        # 至少：封面 + 章节 + 内容 + 总结
        assert len(slides) >= 3
        assert slides[0].layout == "cover"
        assert slides[-1].layout == "summary"

    def test_render_real_pptx(self, tmp_storage):
        renderer = PptRenderer()
        slides = renderer.arrange_slides(
            "Demo", [SectionContent(title="S1", order=1, markdown="- a\n- b\n- c")]
        )
        path = renderer.render("Demo", slides, tmp_storage)
        assert path.exists()
        assert path.suffix == ".pptx"
        assert path.stat().st_size > 0  # 文件非空

    def test_markdown_to_bullets(self):
        md = "## 标题\n- a\n- b\n正文行"
        bullets = PptRenderer._markdown_to_bullets(md)
        assert "标题" in bullets
        assert "a" in bullets


# ───────── ④ 文档渲染 ─────────
class TestDocRenderer:
    @pytest.mark.asyncio
    async def test_render_markdown(self, tmp_storage):
        r = DocRenderer()
        from src.models.dto import SectionContent as SC

        path = await r.render_markdown(
            "Doc", [SC(title="S1", order=1, markdown="## S1\n内容")], tmp_storage
        )
        assert path.exists()
        assert path.read_text(encoding="utf-8").startswith("# Doc")

    @pytest.mark.asyncio
    async def test_render_pdf(self, tmp_storage):
        r = DocRenderer()
        from src.models.dto import SectionContent as SC

        path = await r.render_pdf(
            "Doc", [SC(title="S1", order=1, markdown="内容内容")], tmp_storage
        )
        assert path.exists()
        assert path.suffix == ".pdf"
        assert path.stat().st_size > 0

    @pytest.mark.asyncio
    async def test_render_mindmap(self, tmp_storage):
        r = DocRenderer()
        outline = {"title": "M", "sections": [
            {"order": 1, "title": "A", "subsections": [{"order": 1.1, "title": "A1"}]}
        ]}
        from src.models.dto import Outline as OL

        ol = OL.model_validate(outline)
        path = await r.render_mindmap(ol, tmp_storage)
        assert path.exists()
        assert "# M" in path.read_text(encoding="utf-8")


# ───────── ⑤ 审核 ─────────
class TestReviewChecker:
    @pytest.mark.asyncio
    async def test_pass(self, tmp_storage):
        from ai_edu_common.enums import ResourceTypeEnum

        rc = ReviewChecker(enable_safety=True)
        result = await rc.review(
            content_text="正常教学内容",
            file_path=None,
            resource_type=ResourceTypeEnum.PPT,
            title="t",
            url="u",
        )
        assert result.passed is True
        assert result.code == 0
        assert result.resource is not None
        assert result.resource.resourceId.startswith("res_")

    @pytest.mark.asyncio
    async def test_block_unsafe(self, tmp_storage):
        rc = ReviewChecker(enable_safety=True)
        result = await rc.review(
            content_text="这里包含 色情 内容",
            file_path=None,
            resource_type="ppt",
            title="t",
            url="u",
        )
        assert result.passed is False
        assert result.code == 3001  # CONTENT_SAFETY_VIOLATION

    @pytest.mark.asyncio
    async def test_block_hallucination(self, tmp_storage):
        rc = ReviewChecker(enable_safety=True)
        result = await rc.review(
            content_text="参见 doi:10.0000/fake 的研究",
            file_path=None,
            resource_type="ppt",
            title="t",
            url="u",
        )
        assert result.passed is False
        assert result.code == 3002  # HALLUCINATION_DETECTED
