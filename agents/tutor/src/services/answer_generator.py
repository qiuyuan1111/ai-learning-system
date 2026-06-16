"""
答案生成服务

结合用户画像，生成个性化的辅导回答。
支持多模态输入处理和画像维度适配。
"""

from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple

from src.config import config
from src.models.dto import Attachment
from src.models.context import DialogueContext
from src.services.llm_service import LLMService


class AnswerGenerator:
    """
    答案生成服务

    职责：
    结合用户画像，生成个性化的辅导回答。

    核心策略：
    1. 根据画像中的 knowledge_base 调整回答深度
    2. 根据 cognitive_style 调整呈现方式（理论推导/代码示例/图解）
    3. 根据 learning_pace 调整语速和信息密度
    4. 关联 weakness_preferences 对薄弱点着重讲解
    5. 关联 interest_areas 使用用户感兴趣的例子
    """

    def __init__(self, llm_service: LLMService):
        self.llm = llm_service

    async def generate_stream(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        question: str,
        attachments: List[Attachment],
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式生成回答

        Yields:
            {"type": "text", "content": {"markdown": chunk}}
            ...
            {"type": "done", "content": {}}
        """
        # 处理附件（图片等）
        processed_messages = await self._process_attachments(messages, attachments)

        # 流式生成
        full_content = ""
        async for chunk in self.llm.chat_stream(processed_messages, temperature=config.temperature):
            full_content += chunk
            yield {
                "type": "text",
                "content": {"markdown": chunk},
            }

        yield {"type": "done", "content": {}}

    async def _process_attachments(
        self,
        messages: List[Dict[str, str]],
        attachments: List[Attachment],
    ) -> List[Dict[str, Any]]:
        """
        处理附件消息

        如果有多模态附件（图片等），根据模型能力选择处理方式：
        - 支持多模态 → 直接传入 image_url
        - 不支持多模态 → 先使用图片描述模型生成文本描述再传入
        """
        if not attachments:
            return messages

        # 找到最后一个 user 消息，追加附件内容
        image_attachments = [a for a in attachments if a.mimeType.startswith("image/")]

        if not image_attachments:
            return messages

        if config.is_multimodal_model:
            return self._build_multimodal_messages(messages, image_attachments)

        # 非多模态模型：用描述替代
        return await self._build_described_messages(messages, image_attachments)

    def _build_multimodal_messages(
        self,
        messages: List[Dict[str, str]],
        images: List[Attachment],
    ) -> List[Dict[str, Any]]:
        """
        构建多模态消息（GPT-4o 原生支持图片理解）

        将最后一条 user 消息扩展为多模态 content 数组。
        无图片时保持原始消息格式不变。
        """
        if not images:
            return messages

        result: List[Dict[str, Any]] = []
        for msg in messages[:-1]:
            result.append(dict(msg))

        last_msg = messages[-1]
        content: List[Dict[str, Any]] = [{"type": "text", "text": last_msg["content"]}]

        for img in images:
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": img.url,
                    "detail": "high",
                },
            })

        result.append({"role": "user", "content": content})
        return result

    async def _build_described_messages(
        self,
        messages: List[Dict[str, str]],
        images: List[Attachment],
    ) -> List[Dict[str, str]]:
        """
        非多模态模型的降级处理

        用一个轻量模型先描述图片内容，然后用文本描述替代。
        这里复用 llm_service 但使用更便宜的模型。
        """
        descriptions = []
        for img in images:
            desc = await self._describe_image(img)
            descriptions.append(desc)

        desc_text = "\n\n[用户上传了以下图片]:\n" + "\n---\n".join(descriptions)

        result = [dict(msg) for msg in messages[:-1]]
        last_msg = messages[-1]
        result.append({
            "role": "user",
            "content": last_msg["content"] + desc_text,
        })
        return result

    async def _describe_image(self, attachment: Attachment) -> str:
        """用轻量模型描述图片内容"""
        try:
            response = await self.llm.client.chat.completions.create(
                model=config.image_description_model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "请用中文详细描述这张图片的内容。"},
                            {
                                "type": "image_url",
                                "image_url": {"url": attachment.url, "detail": "low"},
                            },
                        ],
                    },
                ],
                max_tokens=300,
            )
            return response.choices[0].message.content or "（图片描述失败）"
        except Exception:
            return f"（图片：{attachment.url}，无法自动描述）"

    def get_attachment_summary(self, attachments: List[Attachment]) -> str:
        """生成附件摘要（用于日志或调试）"""
        if not attachments:
            return ""
        parts = [f"{a.type}({a.mimeType})" for a in attachments]
        return f" [附件: {', '.join(parts)}]"
