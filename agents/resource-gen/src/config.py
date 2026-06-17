"""资源生成编排器 —— 全局配置。

所有可调参数通过环境变量注入（见 github-collaboration-guide.md 7.3 的 .env 模板）。
未设置时使用安全默认值，确保无 .env 也能启动（开发友好）。
"""
from __future__ import annotations

import os
from pathlib import Path


def _env_bool(key: str, default: bool = False) -> bool:
    return os.getenv(key, str(default)).lower() in ("1", "true", "yes", "on")


class Settings:
    """运行时配置（单例式读取环境变量）。"""

    # 服务
    SERVICE_NAME: str = "agent-resource-gen"
    PORT: int = int(os.getenv("PORT", "8090"))

    # 大模型（未配置 key 时自动降级到 Mock，保证可独立运行/测试）
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    LLM_USE_MOCK: bool = _env_bool("LLM_USE_MOCK", True) or not bool(OPENAI_API_KEY)

    # 文件存储
    FILE_STORAGE_PATH: Path = Path(os.getenv("FILE_STORAGE_PATH", "./storage"))
    PUBLIC_BASE_URL: str = os.getenv("PUBLIC_BASE_URL", "http://localhost:8090/files")

    # 安全审核
    ENABLE_SAFETY_CHECK: bool = _env_bool("ENABLE_SAFETY_CHECK", True)

    # 网关内部推送地址（WS 通知走网关转发，见 api.md 2.2）
    GATEWAY_PUSH_URL: str = os.getenv("GATEWAY_PUSH_URL", "")

    def ensure_storage_dir(self) -> Path:
        """确保存储目录存在。读取实例属性，便于测试期 monkeypatch 替换路径。"""
        Path(self.FILE_STORAGE_PATH).mkdir(parents=True, exist_ok=True)
        return Path(self.FILE_STORAGE_PATH)


settings = Settings()
