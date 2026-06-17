"""ID 生成器 —— 与 TS 版 IdGenerator 严格对应（见 work-person-c.md 3.4）。

格式约定：
    会话 ID → sess_ + 16 位随机串
    资源 ID → res_  + 16 位随机串
    任务 ID → task_ + 16 位随机串
    路径 ID → path_ + 16 位随机串
    请求 ID → UUID v4
"""
from __future__ import annotations

import secrets
import uuid


def _random_hex(length: int = 16) -> str:
    """生成指定位数的随机十六进制字符串。"""
    return secrets.token_hex((length + 1) // 2)[:length]


def _prefixed(prefix: str, length: int = 16) -> str:
    return f"{prefix}_{_random_hex(length)}"


class IdGenerator:
    """统一 ID 生成器（全部为静态方法）。"""

    @staticmethod
    def session_id() -> str:
        return _prefixed("sess")

    @staticmethod
    def resource_id() -> str:
        return _prefixed("res")

    @staticmethod
    def task_id() -> str:
        return _prefixed("task")

    @staticmethod
    def path_id() -> str:
        return _prefixed("path")

    @staticmethod
    def request_id() -> str:
        return str(uuid.uuid4())
