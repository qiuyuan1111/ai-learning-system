"""画像构建核心逻辑（流式 + 抽取解耦版）

满足 api.md §5.2「对话回答首字<2s、全程流式」：回复走流式（chat_stream），
维度抽取与回复解耦——不再把"回复+抽取+完成标志"塞进同一次 response_format=
json_object 强约束调用（那是慢/60s 超时的元凶，且无法流式）。改为：回复流式产出，
抽取在回复流完后单独跑一次纯文本 JSON 调用。上下文管理（历史摘要 + 滑动窗口）
沿用本文件下半部分的实现，回复与抽取都复用，避免重复追问。
完成判定：纯代码——所有 6 维置信度 >= min_confidence。
"""

import json
import logging
import os
from typing import AsyncGenerator, List, Optional

logger = logging.getLogger(__name__)

from ..models.schema import (
    CognitiveStyle,
    CognitiveStyleDim,
    InterestArea,
    KnowledgeBase,
    KnowledgeLevel,
    LearningPace,
    LearningPaceDim,
    ProfileDimensions,
    TargetDifficulty,
    UserProfile,
    WeaknessPreference,
)
from ..models.dto import ProfileBuildResult
from ..config import settings
from .llm_service import LLMService


def _safe_enum(enum_cls, value, default):
    """安全地将字符串转换为 Enum，无效值时使用默认值"""
    if value is None or not isinstance(value, str):
        return default
    try:
        return enum_cls(value)
    except ValueError:
        return default

# 系统提示词模板 — 优先从文件加载，支持定制
_PROMPT_FILE = os.path.join(os.path.dirname(__file__), "..", "prompts", "build.txt")


def _format_build_prompt(existing_profile: str, missing_dims: str) -> str:
    """加载并格式化画像构建提示词（文件中的 { } 为字面大括号，仅替换已知模板变量）"""
    try:
        with open(_PROMPT_FILE, encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        content = _BUILD_PROMPT_FALLBACK
    return content.replace("{existing_profile}", existing_profile) \
                   .replace("{missing_dims}", missing_dims)


_BUILD_PROMPT_FALLBACK = """你是一个友好的用户画像构建助手。你的任务是通过自然对话了解用户，
构建包含以下 6 个维度的画像：
1. knowledge_base（知识基础）：用户的学历、专业、已掌握技能标签
2. cognitive_style（认知风格）：理论推导型 / 实践应用型 / 视觉图像型 / 语言阅读型
3. learning_pace（学习节奏）：慢 / 中等 / 快
4. weakness_preferences（易错点偏好）：用户觉得自己薄弱的知识点
5. interest_areas（兴趣领域）：用户感兴趣的领域和深度
6. target_difficulty（目标难度等级）：用户希望的学习目标难度 (1-10)

当前已有信息：{existing_profile}
当前缺失维度：{missing_dims}

规则：
- 每次对话最多追问 1-2 个维度
- 问题要自然、友好，像真人聊天而不是填表
- 根据用户回答更新对应的维度信息
- 当你认为某个维度的信息足够时，设置其置信度 >= 0.7

请分析用户的回复，以 JSON 格式返回：
{{
    "extracted": {{  // 本次提取到的维度信息，只包含有更新的维度
        "knowledge_base": {{"level": "beginner|intermediate|advanced", "tags": [...], "confidence": 0.0-1.0}} | null,
        "cognitive_style": {{"style": "theoretical|practical|visual|verbal", "detail": "...", "confidence": 0.0-1.0}} | null,
        "learning_pace": {{"pace": "slow|moderate|fast", "preferred_session_minutes": 30, "confidence": 0.0-1.0}} | null,
        "weakness_preferences": [{{"weak_tags": [...], "description": "...", "confidence": 0.0-1.0}}] | null,
        "interest_areas": [{{"areas": [...], "depth": 1-5, "confidence": 0.0-1.0}}] | null,
        "target_difficulty": {{"level": 1-10, "description": "...", "confidence": 0.0-1.0}} | null
    }},
    "reply": "对用户的回复",  // 友好的回应，接着追问下一个问题
    "is_complete": false  // 是否所有维度都已覆盖且置信度达标
}}
"""


# 抽取专用提示词：只产维度 JSON，不产回复（回复由 stream_reply 单独流式生成，二者解耦）。
# 注意：本字符串不经过 .format()，下面的 { } 即字面大括号。
_EXTRACT_PROMPT = """你是用户画像信息抽取器。根据【已有画像】【近期对话】和【用户最新消息】，
抽取可以更新到画像维度的新信息。只输出一个 JSON 对象，不要任何解释、markdown 或多余文字。

6 个维度的字段约定（仅本次"有新信息"的维度给出对象/数组，无更新的填 null）：
{
  "knowledge_base": {"level": "beginner|intermediate|advanced", "tags": ["..."], "confidence": 0.0-1.0},
  "cognitive_style": {"style": "theoretical|practical|visual|verbal", "detail": "...", "confidence": 0.0-1.0},
  "learning_pace": {"pace": "slow|moderate|fast", "preferred_session_minutes": 30, "confidence": 0.0-1.0},
  "weakness_preferences": [{"weak_tags": ["..."], "description": "...", "confidence": 0.0-1.0}],
  "interest_areas": [{"areas": ["..."], "depth": 1-5, "confidence": 0.0-1.0}],
  "target_difficulty": {"level": 1-10, "description": "...", "confidence": 0.0-1.0}
}

规则：
- 信息不充分时对应维度填 null，绝不臆测。
- 已在【已有画像】中且置信度 >= 0.7 的维度，除非用户本次明确改变，否则填 null。
- confidence 实事求是：用户明确陈述 >= 0.8；合理推断 0.5-0.7；含糊 < 0.5。
- 输出必须是合法 JSON，最外层就是上面的对象本身（不要再用 "extracted" 包一层，不要含 reply/is_complete）。
"""


class ProfileBuilder:
    """画像构建服务（流式 + 抽取解耦版）

    由 WS handler 驱动三步：
      1. stream_reply(profile, user_text) -> 异步生成回复文本增量（流式）；
      2. extract(profile, user_text) -> 抽取维度更新（纯文本 JSON）；
      3. finalize(profile, user_text, full_reply, extracted) -> 合并、落库、算完成度。

    回复与抽取都复用 _build_messages_with_context（带历史摘要 + 最近 N 轮），
    避免重复追问。完成判定为纯代码：所有 6 维置信度 >= min_confidence。
    """

    def __init__(self, llm_service: LLMService):
        self.llm = llm_service

    async def stream_reply(
        self,
        profile: UserProfile,
        user_text: str,
    ) -> AsyncGenerator[str, None]:
        """流式生成自然语言回复（带历史上下文，避免重复追问）。

        复用 _build_messages_with_context：system(构建提示) + 历史摘要 + 最近 N 轮 + 当前问题。
        yield 文本增量，由 WS handler 逐帧推送（满足 api.md §5.2 全程流式）。
        此时 raw_dialogue 仅含历史轮次，当前 user_text 作为最后一条 user 消息，不会重复送。
        """
        existing = self._serialize_existing(profile.dimensions)
        missing = profile.dimensions.missing_dimensions()
        sys_prompt = _format_build_prompt(
            json.dumps(existing, ensure_ascii=False),
            ", ".join(missing) if missing else "无",
        )
        messages = self._build_messages_with_context(sys_prompt, profile, user_text)
        async for delta in self.llm.chat_stream(messages):
            yield delta

    async def extract(self, profile: UserProfile, user_text: str) -> dict:
        """从已有画像 + 近期对话 + 最新消息抽取维度更新（纯文本 JSON，无 json_object 强约束）。

        与回复解耦：回复由 stream_reply 流式产出，抽取单独跑一次结构化调用。
        失败时返回 {}（不阻塞回复主流程，本次跳过维度更新）。
        """
        existing = self._serialize_existing(profile.dimensions)
        recent = self._raw_to_rounds(profile.raw_dialogue)[-settings.context_recent_turns:]
        history_lines = []
        if profile.dialogue_summary:
            history_lines.append(f"[摘要] {profile.dialogue_summary}")
        for q, a in recent:
            history_lines.append(f"用户: {q}\n助手: {a}")
        history = "\n".join(history_lines) or "（无）"
        messages = [
            {"role": "system", "content": _EXTRACT_PROMPT},
            {
                "role": "user",
                "content": (
                    f"【已有画像】\n{json.dumps(existing, ensure_ascii=False)}\n\n"
                    f"【近期对话】\n{history}\n\n"
                    f"【用户最新消息】\n{user_text}\n\n请输出抽取 JSON。"
                ),
            },
        ]
        try:
            return await self.llm.chat_structured(messages, temperature=0.2)
        except Exception as e:
            logger.warning("画像抽取失败，跳过本次维度更新: %s", e)
            return {}

    async def finalize(
        self,
        profile: UserProfile,
        user_text: str,
        full_reply: str,
        extracted: dict,
    ) -> ProfileBuildResult:
        """合并抽取结果、落本轮对话、滑动窗口压缩、算完成度，返回构建结果。

        在 stream_reply / extract 之后再调用：此时 raw_dialogue 仍只含历史轮次，
        本方法把本轮 user/assistant 原文追加进去，供下一轮可见。
        """
        if isinstance(extracted, dict):
            self._merge_dimensions(profile.dimensions, extracted)

        profile.raw_dialogue.append(f"user: {user_text}")
        profile.raw_dialogue.append(f"assistant: {full_reply}")

        # 滑动窗口：超过保留上限时，把更早的轮次压缩进摘要，仅留最近 N 轮原文
        await self._maybe_compress_dialogue(profile)

        profile.version += 1
        missing = profile.dimensions.missing_dimensions()
        is_complete = profile.dimensions.is_complete(settings.min_confidence)

        return ProfileBuildResult(
            updated_profile=profile,
            reply_text=full_reply,
            is_complete=is_complete,
            missing_dimensions=missing,
        )

    # ------------------------------------------------------------------
    # 上下文管理：摘要压缩 + 滑动窗口（思路与 tutor 的 ContextManager 一致，
    # 但复用 profile 自身的 UserProfile 持久化，不引入额外 store）
    # ------------------------------------------------------------------
    def _raw_to_rounds(self, raw_dialogue: List[str]) -> List[tuple]:
        """把 'user: ...' / 'assistant: ...' 交替串配对成 (question, answer) 轮次"""
        items = [r for r in raw_dialogue if isinstance(r, str)]
        rounds = []
        i = 0
        while i + 1 < len(items):
            u, a = items[i], items[i + 1]
            q = u[len("user:"):].strip() if u.startswith("user:") else u
            ans = a[len("assistant:"):].strip() if a.startswith("assistant:") else a
            rounds.append((q, ans))
            i += 2
        return rounds

    def _build_messages_with_context(
        self,
        system_prompt: str,
        profile: UserProfile,
        user_text: str,
    ) -> List[dict]:
        """构建带上下文的消息列表：system(构建提示) + 历史摘要 + 最近 N 轮 + 当前问题"""
        messages: List[dict] = [{"role": "system", "content": system_prompt}]

        # 早期对话摘要
        if profile.dialogue_summary:
            messages.append(
                {
                    "role": "system",
                    "content": f"[历史对话摘要]\n{profile.dialogue_summary}",
                }
            )

        # 最近 N 轮对话原文（滑动窗口）
        keep = settings.context_recent_turns
        recent = self._raw_to_rounds(profile.raw_dialogue)[-keep:] if keep > 0 else []
        for q, a in recent:
            messages.append({"role": "user", "content": q})
            messages.append({"role": "assistant", "content": a})

        # 当前用户问题
        messages.append({"role": "user", "content": user_text})
        return messages

    async def _maybe_compress_dialogue(self, profile: UserProfile) -> None:
        """滑动窗口压缩：轮数超过保留上限时，把更早的轮次压缩进摘要，仅留最近 N 轮"""
        keep = settings.context_recent_turns
        rounds = self._raw_to_rounds(profile.raw_dialogue)
        if keep <= 0 or len(rounds) <= keep:
            return

        to_summarize = rounds[:-keep]
        if not to_summarize:
            return

        profile.dialogue_summary = await self._summarize_rounds(
            to_summarize, existing_summary=profile.dialogue_summary
        )
        profile.summary_turns += len(to_summarize)
        # 仅保留最近 keep 轮原文
        kept = rounds[-keep:]
        profile.raw_dialogue = [
            token for q, a in kept for token in (f"user: {q}", f"assistant: {a}")
        ]

    async def _summarize_rounds(
        self,
        rounds: List[tuple],
        existing_summary: Optional[str] = None,
    ) -> str:
        """对话摘要（画像场景：重点保留用户已明确的事实，避免后续重复询问）"""
        if not rounds:
            return existing_summary or ""

        dialogue_text = "\n".join(f"用户: {q}\n助手: {a}" for q, a in rounds)
        previous = f"\n已有摘要:\n{existing_summary}\n\n" if existing_summary else "\n"
        messages = [
            {
                "role": "system",
                "content": (
                    "你是对话摘要助手。请把以下画像构建对话浓缩为一段连贯摘要，"
                    "重点保留用户已经明确表达的事实（专业、年级、基础、目标、"
                    "薄弱点、兴趣、偏好节奏等），以便后续不再重复询问。"
                ),
            },
            {
                "role": "user",
                "content": (
                    f"{previous}需要摘要的新对话:\n{dialogue_text}\n\n"
                    f"请输出整合后的完整摘要："
                ),
            },
        ]
        try:
            return await self.llm.chat(messages, temperature=0.3, max_tokens=512)
        except Exception:
            # 兜底：摘要失败绝不影响主流程，退化为截断拼接
            base = f"{existing_summary}\n{dialogue_text}" if existing_summary else dialogue_text
            return base[:500]

    def _merge_dimensions(self, dims: ProfileDimensions, extracted: dict) -> None:
        """将大模型提取的维度信息合并到现有画像中。

        容错：GLM 偶尔把对象/对象数组返回成字符串（如兴趣领域返回 "机器学习"
        而非 {"areas":["机器学习"]}），直接 .get() 会 AttributeError。这里统一处理。
        """
        def _coerce(v, list_key=None):
            # dict：清洗 null 值（GLM 常返回 {"level": null}，直接删掉，
            #       这样后续 .get(key, default) 才能正确走 default，而非拿到 None）；
            # 字符串元素按 list_key 包装成 {list_key:[v]} 保留语义；
            # 其它类型返回 {}（后续 if 跳过）。
            if isinstance(v, dict):
                return {k: val for k, val in v.items() if val is not None}
            if isinstance(v, str) and list_key:
                return {list_key: [v]}
            return {}

        kb = _coerce(extracted.get("knowledge_base"))
        if kb:
            level = _safe_enum(KnowledgeLevel, kb.get("level"), KnowledgeLevel.BEGINNER)
            dims.knowledge_base = KnowledgeBase(
                level=level,
                tags=kb.get("tags", []),
                confidence=kb.get("confidence", 0.5),
            )

        cs = _coerce(extracted.get("cognitive_style"))
        if cs:
            style = _safe_enum(CognitiveStyle, cs.get("style"), CognitiveStyle.VERBAL)
            dims.cognitive_style = CognitiveStyleDim(
                style=style,
                detail=cs.get("detail", ""),
                confidence=cs.get("confidence", 0.5),
            )

        lp = _coerce(extracted.get("learning_pace"))
        if lp:
            pace = _safe_enum(LearningPace, lp.get("pace"), LearningPace.MODERATE)
            dims.learning_pace = LearningPaceDim(
                pace=pace,
                preferred_session_minutes=lp.get("preferred_session_minutes", 30),
                confidence=lp.get("confidence", 0.5),
            )

        wp_list = extracted.get("weakness_preferences")
        if wp_list:
            raw = wp_list if isinstance(wp_list, list) else [wp_list]
            dims.weakness_preferences = [
                WeaknessPreference(
                    weak_tags=w.get("weak_tags", []),
                    description=w.get("description", ""),
                    confidence=w.get("confidence", 0.5),
                )
                for w in (_coerce(it, "weak_tags") for it in raw)
                if w
            ]

        ia_list = extracted.get("interest_areas")
        if ia_list:
            raw = ia_list if isinstance(ia_list, list) else [ia_list]
            dims.interest_areas = [
                InterestArea(
                    areas=ia.get("areas", []),
                    depth=ia.get("depth", 3),
                    confidence=ia.get("confidence", 0.5),
                )
                for ia in (_coerce(it, "areas") for it in raw)
                if ia
            ]

        td = _coerce(extracted.get("target_difficulty"))
        if td:
            dims.target_difficulty = TargetDifficulty(
                level=td.get("level", 5),
                description=td.get("description", ""),
                confidence=td.get("confidence", 0.5),
            )

    def _serialize_existing(self, dims: ProfileDimensions) -> dict:
        """将现有维度序列化为 JSON 兼容 dict，用于填入提示词"""
        return json.loads(dims.model_dump_json(exclude_none=True))
