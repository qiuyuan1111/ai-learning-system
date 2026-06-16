"""
大模型调用封装

提供统一的对话完成 / 流式完成接口，封装 OpenAI API 调用。
与画像智能体的 LLMService 模式保持一致。
"""

import json
from typing import Any, AsyncGenerator, Dict, List, Optional

from openai import AsyncOpenAI

from src.config import config


class LLMService:
    """
    大模型调用封装

    封装 OpenAI API 调用，提供统一的完成 / 流式完成接口。
    支持提示词模板渲染和对话历史管理。
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.client = AsyncOpenAI(
            api_key=api_key or config.llm_api_key,
            base_url=base_url or config.llm_base_url,
        )
        self.model = model or config.llm_model

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """
        非流式对话完成

        参数:
            messages: [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]
            temperature: 生成温度
            max_tokens: 最大输出 Token 数

        返回: 模型生成的文本
        """
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
    ) -> AsyncGenerator[str, None]:
        """
        流式对话完成（用于 WS 推送）

        逐 token 生成，通过 WS 实时推送 type=text 消息

        Yields: 文本片段
        """
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

    async def chat_with_tools(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]],
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """
        带工具调用的对话完成

        参数:
            messages: 消息列表
            tools: OpenAI 工具定义列表
            temperature: 生成温度

        返回: 包含 choice 信息的完整响应
        """
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            temperature=temperature,
        )
        choice = response.choices[0]
        return {
            "message": choice.message,
            "tool_calls": choice.message.tool_calls,
            "finish_reason": choice.finish_reason,
        }

    async def generate_structured(
        self,
        messages: List[Dict[str, str]],
        response_format: type,
        temperature: float = 0.3,
    ) -> Any:
        """
        结构化输出生成（JSON mode）

        参数:
            messages: 消息列表
            response_format: Pydantic model 类（用于 response_format）
            temperature: 生成温度

        返回: 解析后的结构化数据
        """
        response = await self.client.beta.chat.completions.parse(
            model=self.model,
            messages=messages,
            response_format=response_format,
            temperature=temperature,
        )
        return response.choices[0].message.parsed
