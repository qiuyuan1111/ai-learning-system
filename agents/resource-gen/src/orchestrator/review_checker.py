"""⑤ 审核集成（见 work-person-c.md 4.3.4）。

资源生成完成后，执行最终审核：
    1. 内容安全过滤（违规拦截 → code 3001）
    2. 防幻觉校验（虚假引用 → code 3002）
    3. 格式检查（文件存在性）
审核通过才构造最终 Resource 并落库。
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from ai_edu_common import IdGenerator, Resource
from ai_edu_common.enums import ErrorCodeEnum, ResourceTypeEnum

logger = logging.getLogger(__name__)

# 简易违规词清单（生产应接入专业内容安全服务，如 OpenAI Moderation）
_UNSAFE_KEYWORDS = [
    "炸弹制作", "毒品合成", "色情", "违禁药品",
]

# 虚假引用特征（无出处的杜撰 DOI/arXiv 编号）
_HALLUCINATION_PATTERNS = ["arxiv.org/abs/0000.00000", "doi:10.0000/fake"]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ReviewChecker:
    """审核集成器。"""

    def __init__(self, enable_safety: bool = True) -> None:
        self.enable_safety = enable_safety

    async def review(
        self,
        *,
        content_text: str,
        file_path: Optional[Path],
        resource_type: ResourceTypeEnum,
        title: str,
        url: str,
        description: Optional[str] = None,
    ) -> "ReviewResult":
        from ..models.dto import ReviewResult

        if not self.enable_safety:
            return self._pass(resource_type, title, url, description)

        # 1. 内容安全
        if self._has_unsafe_content(content_text):
            logger.warning("内容安全审核未通过")
            return ReviewResult(
                passed=False,
                code=ErrorCodeEnum.CONTENT_SAFETY_VIOLATION,
                message="生成内容包含违规信息，已拦截",
            )

        # 2. 防幻觉
        if self._has_hallucination(content_text):
            logger.warning("防幻觉校验未通过")
            return ReviewResult(
                passed=False,
                code=ErrorCodeEnum.HALLUCINATION_DETECTED,
                message="存在疑似虚假引用，未生成回答",
            )

        # 3. 文件格式检查（若有文件产物）
        if file_path is not None and not file_path.exists():
            logger.warning("产物文件不存在：%s", file_path)
            return ReviewResult(
                passed=False,
                code=ErrorCodeEnum.RESOURCE_GEN_FAILED,
                message="生成文件完整性校验失败",
            )

        return self._pass(resource_type, title, url, description)

    # ── 内部判定 ──────────────────────────────────────
    @staticmethod
    def _has_unsafe_content(text: str) -> bool:
        low = text.lower()
        return any(k in low for k in _UNSAFE_KEYWORDS)

    @staticmethod
    def _has_hallucination(text: str) -> bool:
        return any(p in text for p in _HALLUCINATION_PATTERNS)

    def _pass(
        self,
        resource_type: ResourceTypeEnum,
        title: str,
        url: str,
        description: Optional[str],
    ) -> "ReviewResult":
        from ..models.dto import ReviewResult

        resource = Resource(
            resourceId=IdGenerator.resource_id(),
            type=resource_type,
            title=title,
            url=url,
            description=description,
            createdAt=_now_iso(),
        )
        return ReviewResult(passed=True, code=0, message="success", resource=resource)
