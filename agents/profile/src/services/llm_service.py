"""大模型调用封装"""

import asyncio
import json
import logging
import re
from typing import Any, AsyncGenerator, List, Optional

import httpx
from openai import AsyncOpenAI, APIError, APIConnectionError, RateLimitError
from ..config import settings

logger = logging.getLogger(__name__)


class LLMServiceError(Exception):
    """LLM 服务通用错误"""
    pass


def _extract_json_object(text: str) -> Optional[Any]:
    """从模型纯文本输出中抠出首个 JSON 对象，解析为 dict。

    不再依赖 response_format=json_object（该强约束让 GLM「憋完整棵 JSON 树」才吐
    第一个字，首字延迟极大、易超时）。改为让模型用纯文本返回 JSON，本端容错解析：
      1. 直接 json.loads；
      2. 剥 ```json ... ``` 围栏后解析；
      3. 大括号配平，定位首个平衡的 {...} 解析（跳过字符串内的括号）。
    任一成功即返回；全失败返回 None。
    """
    s = text.strip()
    # 1. 直接解析
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        pass
    # 2. 剥围栏
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", s, re.DOTALL)
    if fence:
        try:
            return json.loads(fence.group(1))
        except json.JSONDecodeError:
            pass
    # 3. 大括号配平（跳过字符串内的 { } 与转义）
    start = s.find("{")
    if start == -1:
        return None
    depth = 0
    in_str = False
    escape = False
    for i in range(start, len(s)):
        c = s[i]
        if in_str:
            if escape:
                escape = False
            elif c == "\\":
                escape = True
            elif c == '"':
                in_str = False
        else:
            if c == '"':
                in_str = True
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(s[start:i + 1])
                    except json.JSONDecodeError:
                        return None
    return None


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


class LLMService:
    """大模型调用封装，提供统一的完成 / 流式完成接口"""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        # 智谱是国内服务，禁用系统代理（trust_env=False），避免走 VPN/代理导致连不上
        # timeout=120：json_object 模式生成完整 6 维度 JSON 偶尔 >60s，调宽避免误判超时
        self.client = AsyncOpenAI(
            api_key=api_key or settings.llm_api_key,
            base_url=settings.llm_base_url or None,
            timeout=120.0,
            max_retries=2,
            http_client=httpx.AsyncClient(trust_env=False),
        )
        self.model = model or settings.llm_model

    async def chat(
        self,
        messages: List[dict],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        response_format: Optional[dict] = None,
    ) -> str:
        """非流式对话完成（带指数退避重试）

        参数:
            messages: [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]
            temperature: 生成温度
            max_tokens: 最大输出 Token 数
            response_format: 可选的结构化输出格式，如 {"type": "json_object"}

        返回: 模型生成的文本

        抛出:
            LLMServiceError: API 调用失败时（重试用尽）
        """
        kwargs = dict(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        if response_format:
            kwargs["response_format"] = response_format

        last_exc: Optional[Exception] = None
        for attempt in range(4):  # 首次 + 最多 3 次重试
            try:
                resp = await self.client.chat.completions.create(**kwargs)
                return resp.choices[0].message.content or ""
            except (APIError, APIConnectionError, RateLimitError) as exc:
                last_exc = exc
                if not _is_retryable(exc):
                    raise LLMServiceError(f"LLM API 调用失败: {exc}") from exc
                wait = 2 ** attempt  # 1s, 2s, 4s
                # 最后一次不等待，直接抛出
                if attempt < 3:
                    await asyncio.sleep(wait)

        # 重试用尽，抛出最后一个异常
        raise LLMServiceError(f"LLM API 调用失败（重试3次后仍失败）: {last_exc}") from last_exc

    async def chat_structured(
        self,
        messages: List[dict],
        temperature: float = 0.7,
    ) -> dict:
        """结构化输出：让模型用纯文本返回 JSON，本端健壮解析为 dict。

        不再使用 response_format={"type":"json_object"}：该强约束会让 GLM
        「憋完整棵 JSON 树」才吐第一个字，首字延迟极大、易超时（画像构建 60s 超时的
        直接元凶）。改为纯文本输出 + _extract_json_object 容错解析，既快又稳。

        抛出:
            LLMServiceError: API 调用失败、或返回内容里抠不出 JSON 时
        """
        text = await self.chat(messages=messages, temperature=temperature)
        if not text.strip():
            raise LLMServiceError("LLM 返回了空响应")
        parsed = _extract_json_object(text)
        if parsed is None:
            raise LLMServiceError(f"LLM 返回了非 JSON 内容: {text[:200]}")
        return parsed

    async def chat_stream(
        self,
        messages: List[dict],
        temperature: float = 0.7,
    ) -> AsyncGenerator[str, None]:
        """流式对话完成，逐 token 生成（带指数退避重试）

        通过 async for token in llm.chat_stream(messages): 消费
        """
        last_exc: Optional[Exception] = None
        for attempt in range(4):  # 首次 + 最多 3 次重试
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
                return  # 成功完成，退出重试循环
            except (APIError, APIConnectionError, RateLimitError) as exc:
                last_exc = exc
                if not _is_retryable(exc):
                    raise LLMServiceError(f"LLM API 调用失败: {exc}") from exc
                # 最后一次不等待，直接抛出
                if attempt < 3:
                    wait = 2 ** attempt  # 1s, 2s, 4s
                    await asyncio.sleep(wait)

        # 重试用尽，抛出最后一个异常
        raise LLMServiceError(f"LLM API 调用失败（重试3次后仍失败）: {last_exc}") from last_exc


class MockLLMService:
    """Mock 大模型：返回确定性预设内容，无需 API Key。

    用于开发/测试/演示（LLM_USE_MOCK=true 或未配置 key）。输出是确定性的，
    使端到端流程可重复验证。接口与 LLMService（真实）完全一致：
      - chat(messages) -> str
      - chat_structured(messages) -> dict
      - chat_stream(messages) -> AsyncGenerator[str, None]

    识别 messages 中的任务标记（画像构建对话 / 维度抽取 / 画像更新 / 摘要）给出对应形状的输出。
    """

    async def chat(
        self,
        messages: List[dict],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        response_format: Optional[dict] = None,
    ) -> str:
        """非流式对话完成（Mock 版）。"""
        blob = "\n".join(m.get("content", "") for m in messages)
        return self._mock_text(blob)

    async def chat_structured(
        self,
        messages: List[dict],
        temperature: float = 0.7,
    ) -> dict:
        """结构化输出（Mock 版）：直接返回 dict，不走字符串解析。

        - 画像增量更新（update_from_dialogue / update_from_evaluation）：
          返回 {should_update, updates, reason}，按对话内容里能识别到的弱项/兴趣给出更新。
        - 维度抽取（profile_builder.extract）：返回 6 维度抽取对象。
        其余情况返回空抽取。
        """
        blob = "\n".join(m.get("content", "") for m in messages)

        # 画像更新：update prompt 含 "should_update" / "更新来源"
        if "should_update" in blob or "更新来源" in blob or "更新提示" in blob:
            return self._mock_update_result(blob)

        # 维度抽取：extract prompt 含 "信息抽取器" / "抽取可以更新"
        if "信息抽取器" in blob or "抽取可以更新" in blob:
            return self._mock_extract_result(blob)

        # 兜底：空抽取
        return {}

    async def chat_stream(
        self,
        messages: List[dict],
        temperature: float = 0.7,
    ) -> AsyncGenerator[str, None]:
        """流式对话完成（Mock 版）：把预设回复按标点分段 yield，模拟逐 token 流式。"""
        blob = "\n".join(m.get("content", "") for m in messages)
        text = self._mock_text(blob)
        for piece in self._split_to_stream(text):
            yield piece
            await asyncio.sleep(0)  # 让出事件循环，模拟真实流式节奏

    # ------------------------------------------------------------------
    # Mock 文案与结构化数据
    # ------------------------------------------------------------------
    def _mock_text(self, blob: str) -> str:
        """画像构建对话的 Mock 回复：自然地追问下一个维度。"""
        if any(k in blob for k in ("专业", "学历", "背景")) or "knowledge_base" not in blob:
            return "你好！很高兴认识你。为了给你定制个性化学习方案，先问一下：你的专业背景是什么？目前是几年级呢？"
        if "cognitive_style" not in blob and "认知风格" not in blob:
            return "了解了。你平时学新东西时，更喜欢先看理论推导，还是直接上手实践？"
        if "learning_pace" not in blob:
            return "好的。你希望自己用多快的节奏学习？是慢慢打基础，还是中等速度往前推进？"
        return "谢谢你的回答！我已经对你的学习画像有了比较完整的了解，接下来就可以为你生成专属的学习资源和路径了。"

    def _mock_extract_result(self, blob: str) -> dict:
        """维度抽取 Mock：从对话文本里识别到的关键词填到对应维度，其余 null。"""
        result: Dict[str, Any] = {
            "knowledge_base": None,
            "cognitive_style": None,
            "learning_pace": None,
            "weakness_preferences": None,
            "interest_areas": None,
            "target_difficulty": None,
        }
        if any(k in blob for k in ("计算机", "软件", "专业")):
            result["knowledge_base"] = {
                "level": "intermediate",
                "tags": ["编程基础"],
                "confidence": 0.7,
            }
        if any(k in blob for k in ("实践", "上手", "动手")):
            result["cognitive_style"] = {"style": "practical", "detail": "偏好实践", "confidence": 0.6}
        if "慢" in blob:
            result["learning_pace"] = {"pace": "slow", "preferred_session_minutes": 40, "confidence": 0.6}
        elif "快" in blob:
            result["learning_pace"] = {"pace": "fast", "preferred_session_minutes": 20, "confidence": 0.6}
        return result

    def _mock_update_result(self, blob: str) -> dict:
        """画像更新 Mock：默认从答疑对话里识别到一个薄弱点并更新（version 会 +1）。"""
        updates: Dict[str, Any] = {}
        # 若对话里出现困惑/不会等信号，记为新的薄弱点
        if any(k in blob for k in ("不懂", "不会", "没理解", "难", "困惑")):
            updates["weakness_preferences"] = [
                {"weak_tags": ["待巩固知识点"], "description": "答疑中暴露的薄弱点", "confidence": 0.6}
            ]
        if updates:
            return {
                "should_update": True,
                "updates": updates,
                "reason": "Mock：从答疑对话中识别到可更新的画像维度",
            }
        # 无明确信号时，不更新（should_update=False，version 不变）
        return {"should_update": False, "updates": None, "reason": "Mock：本次对话无需更新画像"}

    @staticmethod
    def _split_to_stream(text: str) -> List[str]:
        """把文本按标点切成小块，模拟流式增量输出。"""
        pieces = re.split(r"(?<=[。！？!?，,；;])", text)
        return [p for p in pieces if p]


def get_llm_service():
    """工厂方法：按配置选择 LLM 实现。

    - settings.llm_use_mock 为真（LLM_USE_MOCK=true 或未配置 key）→ MockLLMService
    - 否则 → LLMService（真实，调用 OpenAI 兼容接口）
    """
    if settings.llm_use_mock:
        logger.info("LLM 使用 Mock 模式（无 API Key 或显式开启 LLM_USE_MOCK）")
        return MockLLMService()
    logger.info("LLM 使用真实模式 model=%s", settings.llm_model)
    return LLMService()
