"""应用配置"""

import os
from dataclasses import dataclass, field


def _env_bool(key: str, default: bool = False) -> bool:
    return os.getenv(key, str(default)).lower() in ("1", "true", "yes", "on")


@dataclass
class Settings:
    # 大模型配置
    llm_api_key: str = field(default_factory=lambda: os.getenv("LLM_API_KEY", ""))
    llm_model: str = field(default_factory=lambda: os.getenv("LLM_MODEL", "gpt-4o"))
    llm_base_url: str = field(default_factory=lambda: os.getenv("LLM_BASE_URL", ""))
    # Mock 开关：未配置 key 时自动降级到 Mock，保证无 API Key 也可运行（对齐 resource-gen）
    llm_use_mock: bool = field(
        default_factory=lambda: _env_bool("LLM_USE_MOCK", True) or not os.getenv("LLM_API_KEY", "")
    )

    # 数据库配置
    db_url: str = field(default_factory=lambda: os.getenv("DB_URL", "sqlite:///./profile.db"))

    # 服务配置
    host: str = field(default_factory=lambda: os.getenv("HOST", "0.0.0.0"))
    port: int = int(os.getenv("PORT", "8081"))
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"

    # 画像构建配置
    min_confidence: float = 0.7
    max_build_rounds: int = 20
    dialogue_history_size: int = 50
    # 上下文管理：滑动窗口保留最近 N 轮原文，更早的轮次压缩进 dialogue_summary
    context_recent_turns: int = 6

    # WebSocket
    ws_heartbeat_interval: int = 30

    def validate(self) -> None:
        """校验必要配置是否存在。

        Mock 模式（LLM_USE_MOCK=true 或未配置 key）下不要求 LLM_API_KEY，
        保证无 Key 也可启动，便于开发/测试/演示。
        """
        if not self.llm_use_mock and not self.llm_api_key:
            raise ValueError("LLM_API_KEY 未配置（或设置 LLM_USE_MOCK=true 使用 Mock 模式）")
        if not self.db_url:
            raise ValueError("DB_URL 未配置")


settings = Settings()
