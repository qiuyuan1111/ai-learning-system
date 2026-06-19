"""内容安全过滤器

三层审核：关键词过滤 → 规则引擎 → 大模型审核
"""

import logging
import re
from typing import List, Optional

from ..config import settings
from ..models.safety import KeywordMatch, SafetyCheckResult, SafetyVerdict
from .llm_service import LLMService, LLMServiceError

logger = logging.getLogger(__name__)

# 高风险词（直接违规）
_HIGH_RISK_KEYWORDS = [
    "恐怖袭击", "爆炸物制作", "枪支交易",
    "色情交易", "儿童色情",
    "毒品交易", "赌博网站", "诈骗教程",
    "分裂国家", "颠覆国家政权",
]

# 中风险词（标记 suspect）
_MEDIUM_RISK_KEYWORDS = [
    "暴力", "攻击", "伤害", "杀人",
    "歧视", "种族主义",
    "骚扰", "霸凌",
    "虚假信息", "谣言",
]

_KEYWORD_CATEGORY_MAP = {}
for kw in _HIGH_RISK_KEYWORDS:
    _KEYWORD_CATEGORY_MAP[kw] = "high_risk"
for kw in _MEDIUM_RISK_KEYWORDS:
    _KEYWORD_CATEGORY_MAP[kw] = "medium_risk"


_RULE_PATTERNS = [
    {"pattern": r"\b1[3-9]\d{9}\b", "rule": "泄露个人电话号码", "severity": "suspect"},
    {"pattern": r"\b\d{17}[\dXx]\b", "rule": "泄露身份证号码", "severity": "suspect"},
    {"pattern": r"\b\d{16,19}\b", "rule": "泄露银行卡号", "severity": "suspect"},
    {"pattern": r"(.{3,})\1{4,}", "rule": "内容重复刷屏", "severity": "suspect"},
    {"pattern": r"[^\s]{50,}", "rule": "异常连续字符", "severity": "suspect"},
]

_MODERATION_SYSTEM_PROMPT = """你是一名内容安全审核员。请判断以下文本是否包含违规内容。

审核类别：
1. 暴力恐怖
2. 色情低俗
3. 违法活动
4. 政治敏感
5. 歧视仇恨
6. 骚扰辱骂
7. 虚假信息

请以 JSON 格式输出审核结果：
{
    "isViolation": true/false,
    "riskLevel": "safe" / "suspect" / "violation",
    "categories": [],
    "reason": "",
    "suggestion": ""
}

注意：仅当有明确证据时标记为 violation；教育场景专业术语不应误判。
"""


def _load_custom_keywords() -> List[str]:
    raw = settings.custom_sensitive_words
    if not raw:
        return []
    return [w.strip() for w in raw.split(",") if w.strip()]


_CUSTOM_KEYWORDS = _load_custom_keywords()
if _CUSTOM_KEYWORDS:
    _HIGH_RISK_KEYWORDS = _HIGH_RISK_KEYWORDS + _CUSTOM_KEYWORDS
    for kw in _CUSTOM_KEYWORDS:
        _KEYWORD_CATEGORY_MAP[kw] = "custom"


class ContentSafetyFilter:
    """内容安全过滤器"""

    def __init__(self, llm_service: Optional[LLMService] = None):
        self._llm_service = llm_service

    async def check(
        self,
        text: str,
        context: str = "",
        source: str = "",
    ) -> SafetyCheckResult:
        keyword_hits: List[KeywordMatch] = []
        rule_matches: List[str] = []
        llm_score: float = 0.0
        verdict = SafetyVerdict(passed=True, riskLevel="safe", violatedRules=[], suggestion="")

        # 第一阶段：关键词匹配
        if settings.enable_keyword_filter:
            keyword_hits = self._keyword_scan(text)
            if keyword_hits:
                has_violation = any(
                    _KEYWORD_CATEGORY_MAP.get(h.keyword) in ("high_risk", "custom")
                    for h in keyword_hits
                )
                if has_violation:
                    rules = [f"命中敏感词「{h.keyword}」" for h in keyword_hits]
                    verdict = SafetyVerdict(
                        passed=False, riskLevel="violation",
                        violatedRules=rules, suggestion="内容包含违规关键词，请修改后重试。",
                    )
                    logger.warning("关键词审核不通过: %s (source=%s)", rules, source)
                    return SafetyCheckResult(
                        keywordHits=keyword_hits, llmModerationScore=0.0,
                        ruleMatches=[], verdict=verdict,
                    )

        # 第二阶段：规则引擎
        if settings.enable_rule_engine:
            rule_matches = self._rule_engine_check(text)
            if rule_matches:
                verdict = SafetyVerdict(
                    passed=True, riskLevel="suspect",
                    violatedRules=rule_matches, suggestion="内容触发了安全规则，建议复审。",
                )

        # 第三阶段：大模型审核
        if settings.enable_llm_moderation and self._llm_service:
            try:
                llm_result = await self._llm_moderation(text, context)
                llm_score = 1.0 if llm_result.get("isViolation", False) else 0.0
                llm_risk = llm_result.get("riskLevel", "safe")
                if llm_risk == "violation":
                    rules = [llm_result.get("reason", "LLM 审核判定违规")]
                    verdict = SafetyVerdict(
                        passed=False, riskLevel="violation",
                        violatedRules=rule_matches + rules,
                        suggestion=llm_result.get("suggestion", "内容审核未通过，请修改后重试。"),
                    )
                elif llm_risk == "suspect" and verdict.riskLevel == "safe":
                    verdict = SafetyVerdict(
                        passed=True, riskLevel="suspect",
                        violatedRules=rule_matches + [llm_result.get("reason", "")],
                        suggestion=llm_result.get("suggestion", ""),
                    )
            except LLMServiceError as e:
                logger.warning("LLM 审核失败，回退至规则引擎结果: %s", e)

        return SafetyCheckResult(
            keywordHits=keyword_hits, llmModerationScore=llm_score,
            ruleMatches=rule_matches, verdict=verdict,
        )

    def _keyword_scan(self, text: str) -> List[KeywordMatch]:
        hits = []
        for keyword in _HIGH_RISK_KEYWORDS + _MEDIUM_RISK_KEYWORDS:
            pos = text.find(keyword)
            if pos != -1:
                hits.append(KeywordMatch(
                    keyword=keyword,
                    category=_KEYWORD_CATEGORY_MAP.get(keyword, "default"),
                    position=pos,
                ))
        return hits

    def _rule_engine_check(self, text: str) -> List[str]:
        matches = []
        for rule in _RULE_PATTERNS:
            if re.search(rule["pattern"], text):
                matches.append(rule["rule"])
        return matches

    async def _llm_moderation(self, text: str, context: str = "") -> dict:
        user_prompt = f"请审核以下文本：\n\n{text}"
        if context:
            user_prompt += f"\n\n上下文说明：{context}"
        messages = [
            {"role": "system", "content": _MODERATION_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]
        return await self._llm_service.chat_structured(messages, temperature=0.3)
