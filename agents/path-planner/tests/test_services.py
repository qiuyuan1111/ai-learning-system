"""path-planner —— 服务层单元测试。"""
from __future__ import annotations

import pytest
from ai_edu_common import (
    EvaluationDimension,
    EvaluationReport,
    PathNode,
    PathNodeStatusEnum,
    WeakPoint,
)
from ai_edu_common.enums import ResourceTypeEnum

from src.services.path_adjuster import PathAdjuster
from src.services.path_generator import PathGenerator
from src.services.path_service import PathPlannerService
from src.services.resource_binder import ResourceBinder


# ───────── 资源绑定 ─────────
class TestResourceBinder:
    @pytest.mark.asyncio
    async def test_bind_by_keyword(self, sample_resources):
        binder = ResourceBinder(threshold=0.1)
        nodes = [
            PathNode(nodeId="n1", order=1, title="注意力机制", status=PathNodeStatusEnum.PENDING),
            PathNode(nodeId="n2", order=2, title="量子力学", status=PathNodeStatusEnum.PENDING),
        ]
        result = await binder.bind(nodes, sample_resources)
        # 注意力机制节点应绑定到 res_1
        assert result[0].resource is not None
        assert result[0].resource["resourceId"] == "res_1"
        # 量子力学无匹配，不绑定
        assert result[1].resource is None

    @pytest.mark.asyncio
    async def test_no_resources(self):
        binder = ResourceBinder()
        nodes = [PathNode(nodeId="n1", order=1, title="x", status=PathNodeStatusEnum.PENDING)]
        result = await binder.bind(nodes, [])
        assert result[0].resource is None


# ───────── 路径生成 ─────────
class TestPathGenerator:
    @pytest.mark.asyncio
    async def test_generate(self, sample_user_profile, sample_resources):
        from src.services.llm_service import MockLlmService

        gen = PathGenerator(MockLlmService(), ResourceBinder(threshold=0.1))
        path = await gen.generate("sess_1", sample_user_profile, sample_resources)
        assert path.pathId.startswith("path_")
        assert len(path.nodes) >= 1
        # 节点应有序号且递增
        orders = [n.order for n in path.nodes]
        assert orders == sorted(orders)
        assert orders[0] == 1
        # 节点状态默认 pending
        assert all(n.status == PathNodeStatusEnum.PENDING for n in path.nodes)


# ───────── 路径调整 ─────────
class TestPathAdjuster:
    @pytest.mark.asyncio
    async def test_add_node_for_severe_weakness(self, sample_user_profile):
        from datetime import datetime, timezone

        from ai_edu_common import LearningPathResponse

        current = LearningPathResponse(
            pathId="path_1",
            updatedAt=datetime.now(timezone.utc).isoformat(),
            nodes=[
                PathNode(nodeId="n1", order=1, title="基础", status=PathNodeStatusEnum.PENDING),
            ],
        )
        report = EvaluationReport(
            dimensions=[EvaluationDimension(name="理解", score=6, maxScore=10)],
            weakPoints=[
                WeakPoint(topic="注意力机制", severity=4, description="掌握不牢"),
            ],
            suggestions=["建议加强练习"],
        )
        adjuster = PathAdjuster()
        adjusted = await adjuster.adjust(current, report, sample_user_profile)
        # 应新增专项练习节点
        titles = [n.title for n in adjusted.nodes]
        assert any("注意力机制" in t for t in titles)
        # 节点重新编号连续
        orders = [n.order for n in adjusted.nodes]
        assert orders == list(range(1, len(orders) + 1))

    @pytest.mark.asyncio
    async def test_no_adjust_for_minor_weakness(self, sample_user_profile):
        from datetime import datetime, timezone

        from ai_edu_common import LearningPathResponse

        current = LearningPathResponse(
            pathId="path_1",
            updatedAt=datetime.now(timezone.utc).isoformat(),
            nodes=[
                PathNode(nodeId="n1", order=1, title="基础", status=PathNodeStatusEnum.PENDING),
            ],
        )
        report = EvaluationReport(
            dimensions=[],
            weakPoints=[WeakPoint(topic="小问题", severity=1, description="轻微")],
            suggestions=[],
        )
        adjuster = PathAdjuster()
        adjusted = await adjuster.adjust(current, report, sample_user_profile)
        # severity<3 不加节点，数量不变
        assert len(adjusted.nodes) == 1


# ───────── 业务编排（get_or_create + adjust）─────────
class TestPathPlannerService:
    @pytest.mark.asyncio
    async def test_get_or_create_then_adjust(self, sample_user_profile, sample_resources):
        from src.services.llm_service import MockLlmService

        svc = PathPlannerService(llm=MockLlmService())
        # 先注入上下文，再按 sessionId 获取/生成
        await svc.set_context("sess_1", sample_user_profile, sample_resources)
        path1 = await svc.get_or_create_path("sess_1")
        assert path1 is not None
        # 再次获取应命中缓存（同一 pathId）
        path2 = await svc.get_or_create_path("sess_1")
        assert path2.pathId == path1.pathId

        # 调整
        report = EvaluationReport(
            dimensions=[],
            weakPoints=[WeakPoint(topic="RNN", severity=5, description="薄弱")],
            suggestions=[],
        )
        adjusted = await svc.adjust_path("sess_1", report, sample_user_profile)
        assert adjusted is not None
        assert any("RNN" in n.title for n in adjusted.nodes)

    @pytest.mark.asyncio
    async def test_adjust_nonexistent_path(self, sample_user_profile):
        from src.services.llm_service import MockLlmService

        svc = PathPlannerService(llm=MockLlmService())
        report = EvaluationReport(dimensions=[], weakPoints=[], suggestions=[])
        result = await svc.adjust_path("sess_nope", report, sample_user_profile)
        assert result is None
