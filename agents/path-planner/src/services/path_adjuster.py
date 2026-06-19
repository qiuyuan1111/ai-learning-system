"""路径动态调整器（见 work-person-c.md 5.2 PathAdjuster）。

当评估发现新的薄弱点或画像变化时调整路径：
    ADD     在节点后插入专项练习
    MODIFY  修改节点
    REMOVE  移除已掌握节点
    REORDER 重排顺序
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List

from ai_edu_common import (
    EvaluationReport,
    IdGenerator,
    LearningPathResponse,
    PathNode,
    PathNodeStatusEnum,
    UserProfile,
)

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class PathAdjuster:
    """路径动态调整器。"""

    SEVERITY_THRESHOLD = 3  # severity >= 3 视为严重薄弱，需加练

    async def adjust(
        self,
        current_path: LearningPathResponse,
        evaluation_report: EvaluationReport,
        updated_profile: UserProfile,
    ) -> LearningPathResponse:
        nodes: List[PathNode] = [n.model_copy() for n in current_path.nodes]

        # 1. 根据严重薄弱点，插入专项练习节点（ADD）
        weak_topics = set()
        for wp in evaluation_report.weakPoints:
            if wp.severity >= self.SEVERITY_THRESHOLD:
                weak_topics.add(wp.topic)
                nodes.append(
                    PathNode(
                        nodeId=f"extra_{IdGenerator.request_id()[:8]}",
                        order=1,  # 占位（契约要求 >=1），下方重排覆盖
                        title=f"{wp.topic} 专项练习",
                        description=wp.suggestion or f"针对薄弱点 {wp.topic} 加强练习",
                        status=PathNodeStatusEnum.PENDING,
                    )
                )

        # 2. 若知识水平提升，把相关节点标记完成（基于建议中"已掌握"语义）
        suggestions_text = " ".join(evaluation_report.suggestions)
        if any(k in suggestions_text for k in ("已掌握", "掌握良好", "表现优秀")):
            for node in nodes[: max(1, len(nodes) // 3)]:
                node.status = PathNodeStatusEnum.COMPLETED

        # 3. 重新编号
        for idx, node in enumerate(nodes, start=1):
            node.order = idx

        logger.info(
            "路径调整完成 path=%s 新增薄弱练习=%d",
            current_path.pathId,
            len(weak_topics),
        )
        return LearningPathResponse(
            pathId=current_path.pathId,
            updatedAt=_now_iso(),
            nodes=nodes,
        )
