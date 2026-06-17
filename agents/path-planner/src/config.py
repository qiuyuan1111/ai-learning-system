"""路径规划智能体 —— 全局配置（对齐 resource-gen 的配置风格）。"""
from __future__ import annotations

import os


def _env_bool(key: str, default: bool = False) -> bool:
    return os.getenv(key, str(default)).lower() in ("1", "true", "yes", "on")


class Settings:
    SERVICE_NAME: str = "agent-path-planner"
    PORT: int = int(os.getenv("PORT", "8091"))

    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    LLM_USE_MOCK: bool = _env_bool("LLM_USE_MOCK", True) or not bool(OPENAI_API_KEY)

    # 资源绑定匹配阈值
    BIND_MATCH_THRESHOLD: float = float(os.getenv("BIND_MATCH_THRESHOLD", "0.3"))

    GATEWAY_PUSH_URL: str = os.getenv("GATEWAY_PUSH_URL", "")


settings = Settings()
