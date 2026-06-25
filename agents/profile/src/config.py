"""应用配置"""

import os
from dataclasses import dataclass, field


@dataclass
class Settings:
    # 大模型配置
    llm_api_key: str = field(default_factory=lambda: os.getenv("LLM_API_KEY", ""))
    llm_model: str = field(default_factory=lambda: os.getenv("LLM_MODEL", "gpt-4o"))
    llm_base_url: str = field(default_factory=lambda: os.getenv("LLM_BASE_URL", ""))

    # 数据库配置
    db_url: str = field(default_factory=lambda: os.getenv("DB_URL", "sqlite:///./profile.db"))

    # 服务配置
    host: str = field(default_factory=lambda: os.getenv("HOST", "0.0.0.0"))
    port: int = int(os.getenv("PORT", "8000"))
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"

    # 画像构建配置
    min_confidence: float = 0.7
    max_build_rounds: int = 20
    dialogue_history_size: int = 50

    # WebSocket
    ws_heartbeat_interval: int = 30

    def validate(self) -> None:
        """校验必要配置是否存在"""
        if not self.llm_api_key:
            raise ValueError("LLM_API_KEY 未配置")
        if not self.db_url:
            raise ValueError("DB_URL 未配置")


settings = Settings()
