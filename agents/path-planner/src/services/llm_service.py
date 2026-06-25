"""大模型服务（双实现：Mock + 真实 OpenAI）。

与 resource-gen 同构，保证无 API Key 也能生成路径。
"""
from __future__ import annotations

import json
import logging
from typing import Any, Optional

from ..config import settings

logger = logging.getLogger(__name__)


class LlmService:
    async def chat(self, prompt: str, *, system: Optional[str] = None) -> str:
        raise NotImplementedError

    async def chat_json(self, prompt: str, *, system: Optional[str] = None) -> Any:
        text = await self.chat(prompt, system=system)
        return _extract_json(text)


def _extract_json(text: str) -> Any:
    text = text.strip()
    if text.startswith("```"):
        parts = text.split("```", 2)
        if len(parts) >= 2:
            inner = parts[1]
            if inner.lower().startswith("json"):
                inner = inner[4:]
            text = inner.strip()
    start = min(
        [i for i in (text.find("{"), text.find("[")) if i != -1],
        default=-1,
    )
    if start == -1:
        raise ValueError(f"LLM 输出未包含 JSON: {text[:120]}")
    decoder = json.JSONDecoder()
    obj, _ = decoder.raw_decode(text[start:])
    return obj


class MockLlmService(LlmService):
    async def chat(self, prompt: str, *, system: Optional[str] = None) -> str:
        upper = prompt.upper()
        if "[PATH_NODES]" in upper or "学习路径" in prompt or "节点" in prompt:
            return json.dumps(
                {
                    "nodes": [
                        {"title": "基础回顾", "description": "夯实前置知识", "resourceType": "doc"},
                        {"title": "核心原理", "description": "理解关键机制", "resourceType": "ppt"},
                        {"title": "薄弱点专项", "description": "针对薄弱知识加练", "resourceType": "doc"},
                        {"title": "综合应用", "description": "融会贯通", "resourceType": "ppt"},
                        {"title": "拓展提升", "description": "兴趣方向深入", "resourceType": "doc"},
                    ]
                },
                ensure_ascii=False,
            )
        if "[ADJUST]" in upper or "调整" in prompt:
            return json.dumps({"adjustments": []}, ensure_ascii=False)
        return "[Mock] 已根据画像规划学习路径。"


class RealLlmService(LlmService):
    def __init__(self) -> None:
        try:
            from openai import AsyncOpenAI
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("使用真实 LLM 需安装 openai") from exc
        self._client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY, base_url=settings.OPENAI_BASE_URL
        )

    async def chat(self, prompt: str, *, system: Optional[str] = None) -> str:  # pragma: no cover
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        resp = await self._client.chat.completions.create(
            model=settings.OPENAI_MODEL, messages=messages, temperature=0.6
        )
        return resp.choices[0].message.content or ""


def get_llm_service() -> LlmService:
    if settings.LLM_USE_MOCK:
        logger.info("LLM(Mock) 模式")
        return MockLlmService()
    return RealLlmService()
