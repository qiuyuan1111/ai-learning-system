"""ai_edu_common (Python) —— 契约一致性测试。

验证 Python 版 DTO/枚举/工具与 TS 版 @ai-edu/common 的字段、取值、ID 格式一致。
"""
from __future__ import annotations

import re
import uuid

import pytest
from ai_edu_common import (
    ErrorCodeEnum,
    IdGenerator,
    JsonUtils,
    Resource,
    ResourceTypeEnum,
    TaskStatusEnum,
    UserProfile,
    error,
    paginated,
    success,
)
from ai_edu_common.models import ApiResponse


# ───────── ID 生成格式（与 TS 版 IdGenerator 对齐）─────────
class TestIdGenerator:
    _HEX16 = re.compile(r"^[0-9a-f]{16}$")

    def test_session_id_format(self):
        sid = IdGenerator.session_id()
        assert sid.startswith("sess_")
        assert self._HEX16.match(sid[5:])

    def test_resource_id_format(self):
        rid = IdGenerator.resource_id()
        assert rid.startswith("res_")
        assert self._HEX16.match(rid[4:])

    def test_task_id_format(self):
        tid = IdGenerator.task_id()
        assert tid.startswith("task_")
        assert self._HEX16.match(tid[5:])

    def test_path_id_format(self):
        pid = IdGenerator.path_id()
        assert pid.startswith("path_")
        assert self._HEX16.match(pid[5:])

    def test_request_id_is_uuid(self):
        rid = IdGenerator.request_id()
        # 应为合法 UUID v4
        u = uuid.UUID(rid)
        assert u.version == 4

    def test_uniqueness(self):
        ids = {IdGenerator.session_id() for _ in range(1000)}
        assert len(ids) == 1000  # 无碰撞


# ───────── 枚举取值（与 TS 版 / api.md 严格一致）─────────
class TestEnums:
    def test_resource_types(self):
        assert {e.value for e in ResourceTypeEnum} == {
            "ppt", "pdf", "doc", "mindmap", "video"
        }

    def test_task_statuses(self):
        assert {e.value for e in TaskStatusEnum} == {
            "pending", "processing", "completed", "failed"
        }

    def test_error_codes(self):
        # 关键错误码数值与 api.md 3.2 一致
        assert ErrorCodeEnum.SUCCESS == 0
        assert ErrorCodeEnum.PARAM_ERROR == 1001
        assert ErrorCodeEnum.SESSION_NOT_FOUND == 1002
        assert ErrorCodeEnum.TASK_NOT_FOUND == 2001
        assert ErrorCodeEnum.RESOURCE_GEN_FAILED == 2002
        assert ErrorCodeEnum.CONTENT_SAFETY_VIOLATION == 3001
        assert ErrorCodeEnum.HALLUCINATION_DETECTED == 3002
        assert ErrorCodeEnum.AGENT_TIMEOUT == 4001
        assert ErrorCodeEnum.UNKNOWN_ERROR == 5000


# ───────── 响应体构造（契约核心）─────────
class TestResponseBuilders:
    def test_success_shape(self):
        resp = success({"sessionId": "sess_demo"})
        assert resp.code == 0
        assert resp.message == "success"
        assert resp.data == {"sessionId": "sess_demo"}
        assert resp.requestId  # 自动生成
        # 序列化为 JSON 后字段名必须是 camelCase
        d = resp.model_dump()
        assert set(d.keys()) == {"code", "message", "data", "requestId"}

    def test_success_with_explicit_request_id(self):
        resp = success(None, "req_xxx")
        assert resp.requestId == "req_xxx"

    def test_error_shape(self):
        resp = error(ErrorCodeEnum.TASK_NOT_FOUND, "任务不存在")
        assert resp.code == 2001
        assert resp.data is None
        assert resp.requestId

    def test_paginated_auto_total_pages(self):
        data = paginated([1, 2, 3], page=1, page_size=20, total=55)
        assert data.pageInfo.totalPages == 3  # ceil(55/20)
        assert data.pageInfo.total == 55


# ───────── 模型校验（脏数据防御）─────────
class TestModelValidation:
    def test_resource_accepts_valid_type(self):
        r = Resource(
            resourceId="res_1",
            type=ResourceTypeEnum.PPT,
            title="t",
            url="u",
            createdAt="2026-06-15T10:00:00Z",
        )
        assert r.type == ResourceTypeEnum.PPT

    def test_resource_rejects_invalid_type(self):
        with pytest.raises(Exception):
            Resource(
                resourceId="res_1",
                type="mp4",  # 非法类型
                title="t",
                url="u",
                createdAt="2026-06-15T10:00:00Z",
            )

    def test_extra_field_forbidden(self):
        # extra=forbid：多传字段必须拒绝
        with pytest.raises(Exception):
            ApiResponse.model_validate(
                {"code": 0, "message": "x", "data": None, "requestId": "r", "extra": 1}
            )

    def test_profile_optional_dimensions(self):
        # 初始画像维度可全为空
        p = UserProfile(
            sessionId="sess_1",
            dimensions={},
            updatedAt="2026-06-15T10:00:00Z",
        )
        assert p.dimensions.knowledgeBase is None


# ───────── JSON 工具 ─────────
class TestJsonUtils:
    def test_safe_parse_valid(self):
        assert JsonUtils.safe_parse('{"a":1}') == {"a": 1}

    def test_safe_parse_invalid_returns_fallback(self):
        assert JsonUtils.safe_parse("not json") is None
        assert JsonUtils.safe_parse("not json", fallback=[]) == []

    def test_safe_stringify_circular(self):
        a = {}
        a["self"] = a
        # 不抛异常
        s = JsonUtils.safe_stringify(a)
        assert "unable_to_serialize" in s
