"""resource-gen —— HTTP 接口契约测试（TestClient）。

逐字段验证响应体是否符合 api.md / work-person-c.md 的对外契约。
这是「不改请求体/响应体」承诺的硬性校验。
"""
from __future__ import annotations

import time

import pytest
from fastapi.testclient import TestClient

from src.main import create_app


@pytest.fixture
def client():
    return TestClient(create_app())


# 统一响应体外层契约
def _assert_envelope(resp_json):
    """校验外层 ApiResponse 结构。"""
    assert set(resp_json.keys()) == {"code", "message", "data", "requestId"}
    assert isinstance(resp_json["code"], int)
    assert isinstance(resp_json["message"], str)
    assert isinstance(resp_json["requestId"], str)


class TestHealth:
    def test_health(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"


class TestGenerateAndQuery:
    def test_generate_then_query(self, client):
        """POST 生成 → 轮询 GET 任务状态，最终 completed。"""
        # 1. 触发生成
        resp = client.post(
            "/api/v1/sessions/sess_demo/resources/generate",
            json={"text": "生成BERT讲解PPT", "resourceType": "ppt", "profile": None},
            headers={"X-Request-Id": "req_001"},
        )
        assert resp.status_code == 200
        body = resp.json()
        _assert_envelope(body)
        assert body["code"] == 0
        assert body["requestId"] == "req_001"
        # data 应为 TaskInfo 形状
        data = body["data"]
        assert set(data.keys()) >= {
            "taskId", "status", "progress", "createdAt", "updatedAt"
        }
        assert data["taskId"].startswith("task_")
        task_id = data["taskId"]

        # 2. 轮询直到完成（Mock 管线很快，但为异步）
        final = None
        for _ in range(40):
            q = client.get(f"/api/v1/resource-tasks/{task_id}")
            assert q.status_code == 200
            qbody = q.json()
            _assert_envelope(qbody)
            assert qbody["code"] == 0
            final = qbody["data"]
            assert final["taskId"] == task_id
            if final["status"] in ("completed", "failed"):
                break
            time.sleep(0.1)

        assert final is not None
        assert final["status"] == "completed"
        assert final["progress"] == 100
        assert final["result"] is not None
        assert len(final["result"]["resources"]) == 1
        res = final["result"]["resources"][0]
        # Resource 字段契约
        assert set(res.keys()) >= {
            "resourceId", "type", "title", "url", "createdAt"
        }
        assert res["type"] == "ppt"
        assert res["url"].endswith(".pptx")

    def test_generate_rejects_empty_text(self, client):
        resp = client.post(
            "/api/v1/sessions/sess_demo/resources/generate",
            json={"text": "", "resourceType": "ppt"},
        )
        body = resp.json()
        _assert_envelope(body)
        assert body["code"] == 1001  # PARAM_ERROR
        assert body["data"] is None

    def test_query_nonexistent_task(self, client):
        resp = client.get("/api/v1/resource-tasks/task_nope")
        body = resp.json()
        _assert_envelope(body)
        assert body["code"] == 2001  # TASK_NOT_FOUND
        assert body["data"] is None


class TestResourceList:
    def test_empty_list_pagination(self, client):
        """空资源列表的分页契约。"""
        resp = client.get("/api/v1/sessions/sess_empty/resources?page=1&pageSize=20")
        body = resp.json()
        _assert_envelope(body)
        assert body["code"] == 0
        data = body["data"]
        # PaginatedData 契约
        assert set(data.keys()) == {"list", "pageInfo"}
        assert isinstance(data["list"], list)
        pi = data["pageInfo"]
        assert set(pi.keys()) == {"page", "pageSize", "total", "totalPages"}
        assert pi["total"] == 0
        assert pi["totalPages"] == 0

    def test_list_after_generation(self, client):
        """生成后资源应能被列出（通过注入 repository）。"""
        from src.dependencies import get_container
        from ai_edu_common import Resource
        from ai_edu_common.enums import ResourceTypeEnum

        c = get_container()
        # 注意：TestClient(create_app()) 用的是同一 lru_cache 容器
        c.repository._by_session["sess_list"] = [
            Resource(
                resourceId="res_001",
                type=ResourceTypeEnum.PPT,
                title="BERT",
                url="http://x/bert.pptx",
                createdAt="2026-06-15T10:00:00Z",
            )
        ]
        resp = client.get("/api/v1/sessions/sess_list/resources")
        body = resp.json()
        assert body["code"] == 0
        assert body["data"]["pageInfo"]["total"] == 1
        assert body["data"]["list"][0]["title"] == "BERT"

    def test_invalid_type_filter(self, client):
        resp = client.get("/api/v1/sessions/sess_x/resources?type=mp4")
        body = resp.json()
        assert body["code"] == 1001  # PARAM_ERROR
