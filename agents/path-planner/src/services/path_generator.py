"""路径生成引擎（见 work-person-c.md 5.2 PathGenerator）。

输入：用户画像 + 已有资源
输出：LearningPathResponse（有序 PathNode 列表）

策略：
    1. 分析画像 → 起点与重点
    2. 调大模型生成节点序列
    3. 资源绑定到节点
    4. 排序、编号、保存
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List

from ai_edu_common import (
    IdGenerator,
    LearningPathResponse,
    PathNode,
    PathNodeStatusEnum,
    Resource,
    UserProfile,
)

from ..models.dto import ProfileAnalysis
from .llm_service import LlmService
from .resource_binder import ResourceBinder

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class PathGenerator:
    """路径生成引擎。"""

    def __init__(self, llm: LlmService, resource_binder: ResourceBinder) -> None:
        self.llm = llm
        self.resource_binder = resource_binder

    async def generate(
        self,
        session_id: str,
        profile: UserProfile,
        existing_resources: List[Resource],
    ) -> LearningPathResponse:
        analysis = await self._analyze_profile(profile)
        nodes = await self._generate_nodes(analysis)
        nodes = await self.resource_binder.bind(nodes, existing_resources)

        # 编号与状态
        for idx, node in enumerate(nodes, start=1):
            node.order = idx
            node.status = PathNodeStatusEnum.PENDING
            if not node.nodeId:
                node.nodeId = f"node_{IdGenerator.request_id()[:8]}"

        path = LearningPathResponse(
            pathId=IdGenerator.path_id(),
            updatedAt=_now_iso(),
            nodes=nodes,
        )
        logger.info("路径生成完成 session=%s 节点数=%d", session_id, len(nodes))
        return path

    async def _analyze_profile(self, profile: UserProfile) -> ProfileAnalysis:
        dims = profile.dimensions
        kb = dims.knowledgeBase
        weak = dims.weaknessPreferences or []
        interest = dims.interestAreas or []
        target = dims.targetDifficulty

        weak_tags: List[str] = []
        for w in weak:
            weak_tags.extend(w.weakTags)
        interest_areas: List[str] = []
        for i in interest:
            interest_areas.extend(i.areas)

        level = kb.level if kb else "beginner"
        starting = "基础知识" if level in ("beginner", "未知") else "核心概念"
        duration = 30 if level == "advanced" else (60 if level == "intermediate" else 90)

        return ProfileAnalysis(
            startingPoint=starting,
            goalTopics=interest_areas or ["核心原理", "综合应用"],
            focusAreas=weak_tags,
            estimatedDuration=duration,
        )

    async def _generate_nodes(self, analysis: ProfileAnalysis) -> List[PathNode]:
        prompt = (
            "[PATH_NODES] 你是学习路径设计专家，输出 JSON。\n"
            f"起点: {analysis.startingPoint}\n"
            f"目标主题: {analysis.goalTopics}\n"
            f"需重点加强: {analysis.focusAreas}\n"
            "输出格式: { \"nodes\": [ { \"title\": str, \"description\": str, "
            "\"resourceType\": \"ppt|doc|pdf|mindmap|video\" } ] }\n"
            "设计原则：从起点递进到目标；薄弱点处插入专项节点；节点数 4~6 个。"
        )
        raw = await self.llm.chat_json(prompt)
        node_list = raw.get("nodes", []) if isinstance(raw, dict) else []
        nodes: List[PathNode] = []
        for item in node_list:
            nodes.append(
                PathNode(
                    nodeId=f"node_{IdGenerator.request_id()[:8]}",
                    order=1,  # 占位（契约要求 >=1），后续统一编号覆盖
                    title=item.get("title", "未命名节点"),
                    description=item.get("description"),
                    status=PathNodeStatusEnum.PENDING,
                )
            )
        if not nodes:
            nodes.append(
                PathNode(
                    nodeId=f"node_{IdGenerator.request_id()[:8]}",
                    order=1,
                    title=analysis.startingPoint,
                    description="默认起始节点",
                    status=PathNodeStatusEnum.PENDING,
                )
            )
        return nodes
