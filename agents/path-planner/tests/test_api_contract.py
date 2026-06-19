"""path-planner —— HTTP 接口契约测试。"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.main import create_app


@pytest.fixture
def client():
    return TestClient(create_app())


def _profile_body():
    """构造合法 profile（用于上下文注入）。"""
    return {
        "sessionId": "sess_demo",
        "dimensions": {
            "knowledgeBase": {
                "level": "intermediate",
                "tags": ["Python"],
                "confidence": 0.8,
            },
            "weaknessPreferences": [
                {"weakTags": ["注意力机制"], "confidence": 0.7}
            ],
            "interestAreas": [{"areas": ["NLP"], "depth": 3, "confidence": 0.6}],
            "targetDifficulty": {"level": 7, "confidence": 0.5},
        },
        "updatedAt": "2026-06-15T10:00:00Z",
        "version": 1,
    }


def _assert_envelope(j):
    assert set(j.keys()) == {"code", "message", "data", "requestId"}


def _inject_context(client, session_id, profile=None):
    """注入上下文（内部接口）。

    资源标题「核心原理详解」刻意匹配 Mock 生成的节点「核心原理」，
    以验证资源绑定逻辑（Jaccard 关键词重合 >= 阈值）。
    """
    client.post(
        f"/api/v1/sessions/{session_id}/path-context",
        json={
            "profile": profile or {**_profile_body(), "sessionId": session_id},
            "resources": [
                {
                    "resourceId": "res_1",
                    "type": "ppt",
                    "title": "核心原理",
                    "url": "http://x/core.pptx",
                    "createdAt": "2026-06-15T10:00:00Z",
                }
            ],
        },
    )


class TestLearningPath:
    def test_get_learning_path_after_context(self, client):
        # 先注入上下文
        _inject_context(client, "sess_demo")
        # GET（无 body）取路径
        resp = client.get(
            "/api/v1/sessions/sess_demo/learning-path",
            headers={"X-Request-Id": "req_pp_1"},
        )
        assert resp.status_code == 200
        body = resp.json()
        _assert_envelope(body)
        assert body["code"] == 0
        assert body["requestId"] == "req_pp_1"
        data = body["data"]
        # LearningPathResponse 契约
        assert set(data.keys()) == {"pathId", "updatedAt", "nodes"}
        assert data["pathId"].startswith("path_")
        assert isinstance(data["nodes"], list)
        assert len(data["nodes"]) >= 1
        node = data["nodes"][0]
        assert set(node.keys()) >= {"nodeId", "order", "title", "status"}
        assert node["order"] == 1
        # 资源已绑定（注意力机制匹配 res_1）
        bound = [n for n in data["nodes"] if n.get("resource")]
        assert bound, "至少有一个节点应绑定资源"

    def test_get_without_context_uses_default_profile(self, client):
        """未注入上下文时，GET 仍可用默认画像生成。"""
        resp = client.get("/api/v1/sessions/sess_default/learning-path")
        body = resp.json()
        _assert_envelope(body)
        assert body["code"] == 0
        assert len(body["data"]["nodes"]) >= 1

    def test_idempotent(self, client):
        """同一 session 两次 GET 返回同 pathId（缓存命中）。"""
        _inject_context(client, "sess_idem")
        r1 = client.get("/api/v1/sessions/sess_idem/learning-path").json()
        r2 = client.get("/api/v1/sessions/sess_idem/learning-path").json()
        assert r1["data"]["pathId"] == r2["data"]["pathId"]


class TestRecommend:
    def test_trigger_recommend(self, client):
        resp = client.post("/api/v1/sessions/sess_demo/recommend")
        body = resp.json()
        _assert_envelope(body)
        assert body["code"] == 0
        assert body["data"] is None  # 响应为空，实际走 WS


class TestAdjust:
    def test_adjust_path(self, client):
        # 先生成一条路径
        _inject_context(client, "sess_adj")
        client.get("/api/v1/sessions/sess_adj/learning-path")
        # 再调整
        resp = client.post(
            "/api/v1/sessions/sess_adj/path/adjust",
            json={
                "profile": {**_profile_body(), "sessionId": "sess_adj"},
                "report": {
                    "dimensions": [],
                    "weakPoints": [
                        {"topic": "梯度消失", "severity": 4, "description": "薄弱"}
                    ],
                    "suggestions": [],
                },
            },
        )
        body = resp.json()
        _assert_envelope(body)
        assert body["code"] == 0
        titles = [n["title"] for n in body["data"]["nodes"]]
        assert any("梯度消失" in t for t in titles)

    def test_adjust_without_path(self, client):
        """路径未生成时调整，应返回会话不存在。"""
        resp = client.post(
            "/api/v1/sessions/sess_nope/path/adjust",
            json={
                "profile": _profile_body(),
                "report": {"dimensions": [], "weakPoints": [], "suggestions": []},
            },
        )
        body = resp.json()
        assert body["code"] == 1002  # SESSION_NOT_FOUND
