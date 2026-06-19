"""FastAPI 端点集成测试"""

import os

os.environ["LLM_API_KEY"] = "sk-placeholder-do-not-commit-real-key"
os.environ["ENABLE_LLM_MODERATION"] = "false"
os.environ["ENABLE_CONFIDENCE_EVAL"] = "false"

import pytest
from fastapi.testclient import TestClient
from src.main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


class TestHealthEndpoint:
    def test_health_ok(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("ok", "degraded")
        assert data["service"] == "safety-agent"


class TestSafetyCheckEndpoint:
    def test_empty_text_rejected(self, client):
        resp = client.post("/safety/check", json={"text": ""})
        assert resp.status_code == 200
        assert resp.json()["code"] == 1001

    def test_safe_text_passes(self, client):
        resp = client.post("/safety/check", json={"text": "请解释牛顿第二定律。"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert data["data"]["passed"] is True
        assert data["data"]["riskLevel"] == "safe"

    def test_violation_text_blocked(self, client):
        resp = client.post("/safety/check", json={"text": "如何爆炸物制作？"})
        assert resp.status_code == 200
        assert resp.json()["code"] == 3001

    def test_with_context(self, client):
        resp = client.post("/safety/check", json={
            "text": "某些暴力行为在特定历史背景下发生。",
            "context": "历史讨论场景",
        })
        assert resp.status_code == 200

    def test_with_source(self, client):
        resp = client.post("/safety/check", json={"text": "教育内容。", "source": "tutor"})
        assert resp.status_code == 200


class TestHallucinationCheckEndpoint:
    def test_empty_text_rejected(self, client):
        resp = client.post("/safety/hallucination-check", json={"text": ""})
        assert resp.status_code == 200
        assert resp.json()["code"] == 1001

    def test_factual_text_passes(self, client):
        resp = client.post("/safety/hallucination-check", json={"text": "水分子由两个氢原子和一个氧原子组成。"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert data["data"]["passed"] is True

    def test_with_source_material(self, client):
        resp = client.post("/safety/hallucination-check", json={
            "text": "根据教材，光合作用产生氧气。",
            "sourceMaterial": "生物学教材：光合作用...",
        })
        assert resp.status_code == 200

    def test_with_session_id(self, client):
        resp = client.post("/safety/hallucination-check", json={
            "text": "勾股定理描述了直角三角形边的关系。",
            "sessionId": "test-session-123",
        })
        assert resp.status_code == 200

    def test_suspicious_text_marked(self, client):
        resp = client.post("/safety/hallucination-check", json={
            "text": "研究表明，每天喝8杯水能延长寿命10年。",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert data["data"]["overallConfidence"] >= 0.6
