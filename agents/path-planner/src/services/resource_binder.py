"""资源绑定器（见 work-person-c.md 5.2 ResourceBinder）。

将已生成资源匹配到路径节点。匹配度 = 标题/描述的关键词重合度（Jaccard）。
开发期用纯关键词匹配（无需嵌入模型）；预留接口，后续可替换为 embedding。
"""
from __future__ import annotations

import re
from typing import List

from ai_edu_common import PathNode, Resource


class ResourceBinder:
    """资源绑定器。"""

    def __init__(self, threshold: float = 0.3) -> None:
        self.threshold = threshold

    async def bind(self, nodes: List[PathNode], resources: List[Resource]) -> List[PathNode]:
        if not resources:
            return nodes
        for node in nodes:
            best, best_score = None, 0.0
            node_terms = self._terms(f"{node.title} {node.description or ''}")
            for res in resources:
                res_terms = self._terms(f"{res.title} {res.description or ''}")
                score = self._jaccard(node_terms, res_terms)
                if score > best_score:
                    best, best_score = res, score
            if best is not None and best_score >= self.threshold:
                node.resource = {
                    "resourceId": best.resourceId,
                    "type": best.type,
                    "url": best.url,
                }
        return nodes

    # ── 匹配度量 ──────────────────────────────────────
    @staticmethod
    def _terms(text: str) -> set:
        # 中英文混合分词：英文按词，中文按 2-gram
        tokens = set(re.findall(r"[A-Za-z0-9]+", text.lower()))
        zh = re.sub(r"[^一-龥]", "", text)
        for i in range(len(zh) - 1):
            tokens.add(zh[i : i + 2])
        return tokens

    @staticmethod
    def _jaccard(a: set, b: set) -> float:
        if not a or not b:
            return 0.0
        inter = len(a & b)
        union = len(a | b)
        return inter / union if union else 0.0
