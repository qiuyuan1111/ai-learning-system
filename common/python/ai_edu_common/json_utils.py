"""JSON 工具函数 —— 与 TS 版 JsonUtils 对应。

内部辅助工具，不参与对外请求/响应契约。
"""
from __future__ import annotations

import json
from typing import Any, Optional, Type, TypeVar

T = TypeVar("T")


class JsonUtils:
    @staticmethod
    def safe_parse(text: Optional[str], fallback: Any = None, *, as_type: Type[T] = dict) -> Any:
        """安全解析 JSON 字符串，失败时返回 fallback，绝不抛异常。"""
        if text is None or text == "":
            return fallback
        try:
            return json.loads(text)
        except (ValueError, TypeError):
            return fallback

    @staticmethod
    def safe_stringify(value: Any) -> str:
        """安全序列化为 JSON 字符串，遇循环引用等返回兜底串。"""
        try:
            return json.dumps(value, ensure_ascii=False)
        except (TypeError, ValueError):
            return json.dumps({"error": "unable_to_serialize"})

    @staticmethod
    def pretty(value: Any) -> str:
        """美化输出（2 空格缩进）。"""
        try:
            return json.dumps(value, ensure_ascii=False, indent=2)
        except (TypeError, ValueError):
            return str(value)
