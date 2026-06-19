"""大模型调用封装"""

import json
import logging
from typing import AsyncGenerator, List, Optional

from openai import AsyncOpenAI, APIError, APIConnectionError, RateLimitError

from ..config import settings

logger = logging.getLogger(__name__)


class LLMServiceError(Exception):
    """LLM 服务通用错误"""
    pass


class LLMService:
    """大模型调用封装"""

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
        try:
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
        except (APIError, APIConnectionError, RateLimitError) as e:
            raise LLMServiceError(f"LLM API 流式调用失败: {e}") from e
