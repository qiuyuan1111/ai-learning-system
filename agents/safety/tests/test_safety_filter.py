"""内容安全过滤器测试"""

import pytest
from src.services.safety_filter import _HIGH_RISK_KEYWORDS


class TestSafetyFilter:

    @pytest.mark.asyncio
    async def test_safe_text_pass(self, safety_filter):
        result = await safety_filter.check("请解释牛顿第二定律 F=ma 的物理意义。")
        assert result.verdict.passed is True
        assert result.verdict.riskLevel == "safe"

    @pytest.mark.asyncio
    async def test_safe_educational_text(self, safety_filter):
        texts = [
            "什么是量子力学中的薛定谔方程？",
            "请分析第二次世界大战的历史背景。",
            "人体细胞分裂的过程包括有丝分裂和减数分裂。",
            "Python 中列表和元组的区别是什么？",
        ]
        for text in texts:
            result = await safety_filter.check(text)
            assert result.verdict.passed is True, f"误判正常教育内容: {text}"

    @pytest.mark.asyncio
    async def test_high_risk_keyword_detected(self, safety_filter):
        for keyword in _HIGH_RISK_KEYWORDS[:3]:
            text = f"请介绍关于{keyword}的相关内容"
            result = await safety_filter.check(text)
            assert result.verdict.passed is False
            assert result.verdict.riskLevel == "violation"
            assert any(h.keyword == keyword for h in result.keywordHits)

    @pytest.mark.asyncio
    async def test_medium_risk_keyword_hits_counted(self, safety_filter):
        from src.services.safety_filter import _MEDIUM_RISK_KEYWORDS
        for keyword in _MEDIUM_RISK_KEYWORDS[:3]:
            text = f"讨论一下{keyword}的问题"
            result = await safety_filter.check(text)
            assert any(h.keyword == keyword for h in result.keywordHits), f"未检测到: {keyword}"

    @pytest.mark.asyncio
    async def test_rule_engine_phone_detected(self, safety_filter):
        result = await safety_filter.check("请联系我 13800138000 获取更多信息")
        assert len(result.ruleMatches) > 0
        assert "电话号码" in result.ruleMatches[0]

    @pytest.mark.asyncio
    async def test_rule_engine_id_card_detected(self, safety_filter):
        result = await safety_filter.check("我的身份证号是 110101199001011234")
        assert len(result.ruleMatches) > 0
        assert "身份证" in result.ruleMatches[0]

    @pytest.mark.asyncio
    async def test_rule_engine_repeated_text(self, safety_filter):
        result = await safety_filter.check("哈哈哈" * 20)
        assert len(result.ruleMatches) > 0
        assert "重复" in result.ruleMatches[0]

    @pytest.mark.asyncio
    async def test_empty_text_rejected(self, safety_filter):
        result = await safety_filter.check("")
        assert result.verdict.passed is True

    @pytest.mark.asyncio
    async def test_long_safe_text(self, safety_filter):
        text = "人工智能（AI）是计算机科学的一个重要分支。" * 50
        result = await safety_filter.check(text)
        assert result.verdict.passed is True

    def test_keyword_scan(self, safety_filter):
        hits = safety_filter._keyword_scan("关于恐怖袭击的讨论")
        assert len(hits) > 0
        assert hits[0].keyword == "恐怖袭击"
        assert hits[0].category == "high_risk"

    def test_rule_engine_check(self, safety_filter):
        matches = safety_filter._rule_engine_check("电话 13800138000")
        assert len(matches) > 0

    def test_rule_engine_safe(self, safety_filter):
        matches = safety_filter._rule_engine_check("今天天气真好")
        assert len(matches) == 0
