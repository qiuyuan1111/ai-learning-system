"""大模型调用封装

复用与 profile agent 相同的 openai 客户端模式，提供评估专用的调用接口。
"""

import json
from typing import AsyncGenerator, List, Optional

from openai import AsyncOpenAI, APIError, APIConnectionError, RateLimitError

from ..config import settings


class LLMServiceError(Exception):
    """LLM 服务通用错误"""
    pass


class LLMService:
    """大模型调用封装，提供评估场景所需的完成接口"""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.client = AsyncOpenAI(
            api_key=api_key or settings.llm_api_key,
            base_url=settings.llm_base_url or None,
            timeout=60.0,
            max_retries=2,
        )
        self.model = model or settings.llm_model

    async def chat(
        self,
        messages: List[dict],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        response_format: Optional[dict] = None,
    ) -> str:
        """非流式对话完成

        参数:
            messages: [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]
            temperature: 生成温度
            max_tokens: 最大输出 Token 数
            response_format: 可选的结构化输出格式，如 {"type": "json_object"}

        返回: 模型生成的文本

        抛出:
            LLMServiceError: API 调用失败时
        """
        kwargs = dict(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        if response_format:
            kwargs["response_format"] = response_format

        try:
            resp = await self.client.chat.completions.create(**kwargs)
            return resp.choices[0].message.content or ""
        except (APIError, APIConnectionError, RateLimitError) as e:
            raise LLMServiceError(f"LLM API 调用失败: {e}") from e

    async def chat_structured(
        self,
        messages: List[dict],
        temperature: float = 0.7,
    ) -> dict:
        """结构化输出（JSON mode），自动解析为 dict

        内部使用 response_format={"type": "json_object"} 强制模型输出合法 JSON。

        抛出:
            LLMServiceError: API 调用或 JSON 解析失败时
        """
        text = await self.chat(
            messages=messages,
            temperature=temperature,
            response_format={"type": "json_object"},
        )
        if not text.strip():
            raise LLMServiceError("LLM 返回了空响应")
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            raise LLMServiceError(f"LLM 返回了非 JSON 内容: {e}") from e

    async def chat_stream(
        self,
        messages: List[dict],
        temperature: float = 0.7,
    ) -> AsyncGenerator[str, None]:
        """流式对话完成，逐 token 生成"""
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.content:
                yield delta.content
