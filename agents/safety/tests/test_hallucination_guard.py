"""防幻觉校验模块测试"""

import pytest
from src.services.hallucination_guard import _SUSPICIOUS_CITATION_KEYWORDS


class TestHallucinationGuard:

    @pytest.mark.asyncio
    async def test_safe_factual_text(self, hallucination_guard):
        result = await hallucination_guard.check("水分子由两个氢原子和一个氧原子组成。")
        assert result.verdict.passed is True
        assert result.verdict.overallConfidence >= 0.6

    @pytest.mark.asyncio
    async def test_educational_content_passes(self, hallucination_guard):
        texts = [
            "地球绕太阳公转一周大约需要365天。",
            "勾股定理指出：直角三角形两直角边的平方和等于斜边的平方。",
            "光合作用是植物利用光能将二氧化碳和水转化为有机物和氧气的过程。",
        ]
        for text in texts:
            result = await hallucination_guard.check(text)
            assert result.verdict.passed is True, f"误判正常知识: {text}"

    @pytest.mark.asyncio
    async def test_suspicious_citation_detected(self, hallucination_guard):
        for keyword in _SUSPICIOUS_CITATION_KEYWORDS[:3]:
            text = f"{keyword}，超过80%的学生在使用了AI辅助学习后成绩提升了30%以上。"
            result = await hallucination_guard.check(text)
            assert len(result.verdict.hallucinatedClaims) > 0, f"未检测到可疑声明: {keyword}"

    @pytest.mark.asyncio
    async def test_citation_extraction(self, hallucination_guard):
        text = "根据Smith et al. (2020)的研究，以及https://example.com的数据显示..."
        citations = hallucination_guard._extract_citations(text)
        assert len(citations) > 0

    @pytest.mark.asyncio
    async def test_citation_url_validation(self, hallucination_guard):
        text = "更多信息请访问 https://example.com/research/2024/study"
        citations = hallucination_guard._extract_citations(text)
        assert any("https://" in c for c in citations)

    @pytest.mark.asyncio
    async def test_absolute_language_detected(self, hallucination_guard):
        text = "所有人都知道并且同意这个观点。"
        result = await hallucination_guard.check(text)
        assert len(result.factConsistencyIssues) > 0, "应检测到绝对化表述"

    @pytest.mark.asyncio
    async def test_with_source_material(self, hallucination_guard):
        result = await hallucination_guard.check(
            "根据教材定义，力是物体之间的相互作用。",
            source_material="教材：力是物体之间的相互作用...",
        )
        assert result.verdict.passed is True

    @pytest.mark.asyncio
    async def test_extract_citations_url(self, hallucination_guard):
        text = "详情参见 https://arxiv.org/abs/2301.00001"
        citations = hallucination_guard._extract_citations(text)
        assert any("arxiv.org" in c for c in citations)

    @pytest.mark.asyncio
    async def test_extract_citations_none(self, hallucination_guard):
        citations = hallucination_guard._extract_citations("今天天气很好。")
        assert len(citations) == 0

    def test_check_citations_future_year(self, hallucination_guard):
        issues, passed = hallucination_guard._check_citations(["Smith (2030)"])
        assert len(issues) > 0
        assert "年份" in issues[0]

    def test_check_citations_valid(self, hallucination_guard):
        issues, passed = hallucination_guard._check_citations(["根据牛顿定律"])
        assert passed is True

    @pytest.mark.asyncio
    async def test_suspicious_claim_extraction(self, hallucination_guard):
        text = "研究表明，每天喝8杯水能延长寿命10年。"
        claims = hallucination_guard._extract_suspicious_claims(text)
        assert len(claims) > 0
        assert claims[0].confidence == 0.5
