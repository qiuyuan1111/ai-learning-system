"""大模型调用服务 —— 双实现策略（见 README 关键决策）。

    LlmService（抽象）
        ├── RealLlmService  调用 OpenAI 兼容接口（需要 API Key）
        └── MockLlmService  返回确定性预设内容（无需 Key，用于测试/演示/离线）

根据 config.settings.LLM_USE_MOCK 自动选择。Mock 的输出是确定性的，
使端到端测试可重复。
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Optional

from ..config import settings

logger = logging.getLogger(__name__)


class LlmService:
    """大模型服务抽象基类。"""

    async def chat(self, prompt: str, *, system: Optional[str] = None) -> str:
        raise NotImplementedError

    async def chat_json(self, prompt: str, *, system: Optional[str] = None) -> Any:
        """调用大模型并解析为 JSON。子类可覆盖以获得更稳健的解析。"""
        text = await self.chat(prompt, system=system)
        return _extract_json(text)


def _extract_json(text: str) -> Any:
    """从可能含 markdown 代码块的文本中提取首个 JSON 对象/数组。"""
    text = text.strip()
    if text.startswith("```"):
        # 去掉 ```json ... ``` 包裹
        text = text.split("```", 2)
        if len(text) >= 2:
            inner = text[1]
            if inner.lower().startswith("json"):
                inner = inner[4:]
            text = inner.strip()
    start = text.find("{")
    alt_start = text.find("[")
    candidates = [i for i in (start, alt_start) if i != -1]
    if not candidates:
        raise ValueError(f"LLM 输出未包含 JSON: {text[:120]}")
    start = min(candidates)
    decoder = json.JSONDecoder()
    obj, _ = decoder.raw_decode(text[start:])
    return obj


class MockLlmService(LlmService):
    """Mock 大模型：根据 prompt 关键词返回确定性结构化内容。

    通过识别 prompt 中的任务标记（OUTLINE / CONTENT / PATH 等）给出对应形状的输出，
    保证管线各阶段都能拿到合法数据。
    """

    async def chat(self, prompt: str, *, system: Optional[str] = None) -> str:
        upper = prompt.upper()

        if "[OUTLINE]" in upper or "大纲" in prompt or "SECTIONS" in upper:
            topic = _guess_topic(prompt)
            return json.dumps(
                {
                    "title": f"{topic} 学习大纲",
                    "sections": [
                        {
                            "order": 1,
                            "title": f"{topic} 基础概念",
                            "description": "介绍核心概念与背景",
                            "estimatedMinutes": 15,
                            "subsections": [
                                {"order": 1.1, "title": "核心定义", "estimatedMinutes": 8},
                                {"order": 1.2, "title": "发展背景", "estimatedMinutes": 7},
                            ],
                        },
                        {
                            "order": 2,
                            "title": f"{topic} 关键原理",
                            "description": "深入讲解核心原理",
                            "estimatedMinutes": 20,
                        },
                        {
                            "order": 3,
                            "title": f"{topic} 应用与对比",
                            "description": "实际案例与横向对比",
                            "estimatedMinutes": 15,
                        },
                    ],
                },
                ensure_ascii=False,
            )

        if "[CONTENT]" in upper or "撰写" in prompt:
            title = _extract_field(prompt, "章节") or _extract_field(prompt, "title") or "本节"
            return f"## {title}\n\n本节系统讲解 {title} 的核心要点。\n\n- 要点一：基本定义与直觉理解\n- 要点二：关键公式与推导\n- 要点三：典型应用场景\n\n> 示例：通过具体例子加深理解。\n"

        if "[PATH_NODES]" in upper or "学习路径" in prompt:
            return json.dumps(
                {
                    "nodes": [
                        {"title": "基础回顾", "description": "夯实前置知识", "resourceType": "doc"},
                        {"title": "核心原理", "description": "理解关键机制", "resourceType": "ppt"},
                        {"title": "实战练习", "description": "动手巩固", "resourceType": "doc"},
                        {"title": "综合应用", "description": "融会贯通", "resourceType": "ppt"},
                    ]
                },
                ensure_ascii=False,
            )

        # 兜底：普通文本回答
        return f"[Mock 回答] 针对您的请求已生成关于「{_guess_topic(prompt)}」的说明内容。"


class RealLlmService(LlmService):
    """真实大模型服务：调用 OpenAI 兼容 Chat Completions 接口。"""

    def __init__(self) -> None:
        try:
            from openai import AsyncOpenAI  # 延迟导入，Mock 模式无需安装
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("使用真实 LLM 需安装 openai：pip install openai") from exc
        # 智谱是国内服务，禁用系统代理（trust_env=False），避免走 VPN/代理导致连不上
        import httpx
        self._client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL,
            http_client=httpx.AsyncClient(trust_env=False),
        )

    async def chat(self, prompt: str, *, system: Optional[str] = None) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        # 智谱账户有 RPM/TPM 限流；内容撰写阶段会并行调多次，易触发 429。
        # 这里对 429/5xx/网络错误做指数退避重试，瞬时限流会自动恢复。
        last_exc: Optional[Exception] = None
        for attempt in range(4):  # 首次 + 最多 3 次重试
            try:
                resp = await self._client.chat.completions.create(
                    model=settings.OPENAI_MODEL,
                    messages=messages,
                    temperature=0.7,
                )
                return resp.choices[0].message.content or ""
            except Exception as exc:  # noqa: BLE001  兼容 openai 各类异常
                last_exc = exc
                if not _is_retryable(exc):
                    raise
                wait = 2 ** attempt  # 1s, 2s, 4s
                logger.warning(
                    "LLM 调用失败(status=%s)，%ds 后重试(%d/3): %s",
                    getattr(exc, "status_code", None), wait, attempt + 1, exc,
                )
                await asyncio.sleep(wait)
        # 重试用尽，抛出最后一个异常
        raise last_exc  # type: ignore[misc]


def get_llm_service() -> LlmService:
    """工厂方法：按配置选择实现。"""
    if settings.LLM_USE_MOCK:
        logger.info("LLM 使用 Mock 模式（无 API Key 或显式开启 LLM_USE_MOCK）")
        return MockLlmService()
    logger.info("LLM 使用真实模式 model=%s", settings.OPENAI_MODEL)
    return RealLlmService()


def _is_retryable(exc: Exception) -> bool:
    """判断 LLM 调用异常是否值得重试：限流(429)、服务端 5xx、网络层错误。"""
    status = getattr(exc, "status_code", None)
    if status in (408, 425, 429, 500, 502, 503, 504):
        return True
    # openai 的连接/超时类异常通常无 status_code，按类型名兜底
    name = type(exc).__name__
    return name in (
        "APIConnectionError",
        "APITimeoutError",
        "APIError",
        "TimeoutError",
        "ConnectionError",
    )


# ── Mock 辅助 ──────────────────────────────────────
def _guess_topic(prompt: str) -> str:
    """从 prompt 中粗略提取主题词，清理换行/控制字符避免污染文件名。"""
    for kw in ("生成", "讲解", "关于"):
        if kw in prompt:
            idx = prompt.find(kw)
            # 截到首个换行（多行 prompt 的首段即主题），再去掉标点空白
            tail = prompt[idx + len(kw) :].split("\n", 1)[0].strip(" :：的，,。.")
            return tail[:12] if tail else "指定主题"
    # 直接取 prompt 首行前 8 字符
    return prompt.split("\n", 1)[0].strip()[:8] or "指定主题"


def _extract_field(prompt: str, key: str) -> Optional[str]:
    """简单提取「key: value」形式的字段值。"""
    marker = f"{key}:"
    low = prompt.lower()
    pos = low.find(marker.lower())
    if pos == -1:
        return None
    rest = prompt[pos + len(marker) :].strip()
    return rest.split("\n", 1)[0].strip()
