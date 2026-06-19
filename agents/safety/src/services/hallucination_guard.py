"""防幻觉校验模块

三步校验：引用核查 → 事实一致性 → 置信度评估
"""

import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from ..config import settings
from ..models.hallucination import (
    HallucinatedClaim,
    HallucinationCheckResult,
    HallucinationVerdict,
)
from .llm_service import LLMService, LLMServiceError

logger = logging.getLogger(__name__)

_CITATION_FAILURE_THRESHOLD = 3

_CITATION_PATTERNS = [
    r"[A-Z][a-z]+(?:\s+et\s+al\.?)?\s*[\(，]?\s*(?:19|20)\d{2}\s*[\)，]?",
    r"[「「【\"]?[^「「【\"]{2,30}(?:论文|研究|报告|调查)[」」】\"]?",
    r"https?://[^\s，。；,;]+",
    r"根据\s*[^，。；,;]{2,30}(?:数据|统计|报告)",
    r"\[\d+(?:,\s*\d+)*\]",
]

_SUSPICIOUS_CITATION_KEYWORDS = [
    "研究表明", "调查显示", "数据显示", "据统计",
    "专家指出", "学者发现", "据报道", "最新研究",
]

_ABSOLUTE_PATTERNS = [
    (r"所有人?[都均]", "绝对化表述：'所有'"),
    (r"[必定一定肯定][会能是]", "绝对化表述"),
    (r"没有任何[^。，；]{2,20}(?:证据|可能|例外)", "绝对化否定"),
]

_HALLUCINATION_SYSTEM_PROMPT = """你是一名事实核查专家。请检查以下文本是否存在"幻觉"。

请以 JSON 格式输出：
{
    "overallConfidence": 0.85,
    "hallucinatedClaims": [
        {"claim": "...", "evidence": "...", "confidence": 0.3}
    ],
    "citationIssues": [],
    "factIssues": [],
    "suggestion": ""
}

注意：置信度 < 0.6 标记为疑似幻觉；教育场景基础知识不应误判。
"""


class HallucinationGuard:
    """防幻觉校验模块"""

    def __init__(self, llm_service: Optional[LLMService] = None):
        self._llm_service = llm_service

    async def check(
        self,
        text: str,
        session_id: str = "",
        source_material: str = "",
        dialogue_history: Optional[List[dict]] = None,
    ) -> HallucinationCheckResult:
        if dialogue_history is None:
            dialogue_history = []

        # 第一步：引用提取与核查
        citations = self._extract_citations(text)
        citation_issues: List[str] = []
        citation_passed = True
        if citations and settings.enable_citation_check:
            citation_issues, citation_passed = self._check_citations(citations)

        # 第二步：规则级事实扫描
        suspicious_claims = self._extract_suspicious_claims(text)
        fact_issues: List[str] = []
        fact_score: float = 1.0
        if settings.enable_fact_consistency:
            fact_issues = self._check_fact_consistency(text)
            if fact_issues:
                fact_score = max(0.0, 1.0 - 0.2 * len(fact_issues))

        # 第三步：LLM 深度审核
        llm_claims: List[HallucinatedClaim] = []
        llm_confidence: float = 1.0
        if settings.enable_confidence_eval and self._llm_service:
            try:
                llm_result = await self._llm_hallucination_check(text, citations, source_material)
                llm_claims = self._parse_llm_claims(llm_result)
                if "overallConfidence" in llm_result:
                    llm_confidence = float(llm_result["overallConfidence"])
            except LLMServiceError as e:
                logger.warning("LLM 幻觉检测失败，回退至规则检测: %s", e)

        # 综合判定
        combined_confidence = fact_score * 0.3 + llm_confidence * 0.7
        all_claims = self._merge_claims(llm_claims, suspicious_claims)
        passed = combined_confidence >= settings.hallucination_confidence_threshold and citation_passed

        if not passed:
            suggestion = "暂无法准确验证部分内容，请核实后重新生成。"
        elif combined_confidence < 0.8:
            suggestion = "部分内容置信度较低，建议人工复核。"
        else:
            suggestion = ""

        return HallucinationCheckResult(
            citationCheckPassed=citation_passed,
            citationIssues=citation_issues,
            factConsistencyScore=round(fact_score, 2),
            factConsistencyIssues=fact_issues,
            suggestion=suggestion,
            verdict=HallucinationVerdict(
                passed=passed,
                hallucinatedClaims=all_claims,
                overallConfidence=round(combined_confidence, 2),
            ),
        )

    def _extract_citations(self, text: str) -> List[str]:
        citations = []
        for pattern in _CITATION_PATTERNS:
            citations.extend(re.findall(pattern, text))
        seen, unique = set(), []
        for c in citations:
            if c not in seen:
                seen.add(c)
                unique.append(c)
        return unique

    def _check_citations(self, citations: List[str]) -> Tuple[List[str], bool]:
        issues, current_year = [], datetime.now().year
        for citation in citations:
            if citation.startswith("http"):
                if not re.match(r"^https?://[^\s，。；,;]+$", citation):
                    issues.append(f"引用链接格式异常: {citation[:50]}...")
                continue
            year_match = re.search(r"(?:19|20)\d{2}", citation)
            if year_match and int(year_match.group()) > current_year:
                issues.append(f"引用年份超出当前时间: {citation}")
            if len(citation) < 5:
                issues.append(f"引用过于简短，缺乏可验证信息: {citation}")
        return issues, len(issues) < _CITATION_FAILURE_THRESHOLD

    def _extract_suspicious_claims(self, text: str) -> List[HallucinatedClaim]:
        claims = []
        for keyword in _SUSPICIOUS_CITATION_KEYWORDS:
            pos = text.find(keyword)
            while pos != -1:
                end = pos + len(keyword)
                remainder = text[end:]
                sentence_end = float("inf")
                for sep in ("。", "；", "！", "？", "\n", ". ", "! ", "? "):
                    idx = remainder.find(sep)
                    if idx != -1 and idx < sentence_end:
                        sentence_end = idx
                claim_text = (keyword + remainder[:sentence_end]).strip() if sentence_end != float("inf") else (keyword + remainder[:80]).strip()
                if len(claim_text) > len(keyword) + 5:
                    claims.append(HallucinatedClaim(
                        claim=claim_text,
                        evidence=f"使用了模糊引用词「{keyword}」，缺少具体来源",
                        confidence=0.5,
                    ))
                pos = text.find(keyword, end + 1)
        return claims

    def _check_fact_consistency(self, text: str) -> List[str]:
        issues = []
        for pattern, reason in _ABSOLUTE_PATTERNS:
            if re.search(pattern, text):
                issues.append(reason)
        return issues

    async def _llm_hallucination_check(self, text: str, citations: List[str], source_material: str = "") -> dict:
        user_prompt = f"请检查以下文本是否存在幻觉：\n\n{text}\n"
        if citations:
            user_prompt += "\n检测到以下引用：\n" + "\n".join(f"- {c}" for c in citations)
        if source_material:
            user_prompt += f"\n参考来源：\n{source_material}"
        messages = [
            {"role": "system", "content": _HALLUCINATION_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]
        return await self._llm_service.chat_structured(messages, temperature=0.3)

    def _parse_llm_claims(self, llm_result: dict) -> List[HallucinatedClaim]:
        claims = []
        for rc in llm_result.get("hallucinatedClaims", []):
            if isinstance(rc, dict):
                claims.append(HallucinatedClaim(
                    claim=rc.get("claim", ""),
                    evidence=rc.get("evidence", ""),
                    confidence=float(rc.get("confidence", 0.5)),
                ))
        return claims

    def _merge_claims(self, *claim_lists: List[HallucinatedClaim]) -> List[HallucinatedClaim]:
        seen, merged = set(), []
        for claims in claim_lists:
            for claim in claims:
                if claim.claim not in seen:
                    seen.add(claim.claim)
                    merged.append(claim)
        return merged
