"""
辅导智能体配置

从环境变量读取配置项，提供运行时参数。
"""

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AppConfig:
    """应用配置"""

    # ---- FastAPI ----
    host: str = os.getenv("TUTOR_HOST", "0.0.0.0")
    port: int = int(os.getenv("TUTOR_PORT", "8082"))

    # ---- 大模型 ----
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    llm_model: str = os.getenv("LLM_MODEL", "gpt-4o")
    llm_base_url: Optional[str] = os.getenv("LLM_BASE_URL") or None

    # ---- 画像服务（REST 调用） ----
    profile_service_url: str = os.getenv(
        "PROFILE_SERVICE_URL",
        "http://localhost:8081",
    )
    profile_service_timeout: int = int(os.getenv("PROFILE_SERVICE_TIMEOUT", "10"))

    # ---- 安全过滤器（REST 调用，可选） ----
    safety_service_url: Optional[str] = os.getenv("SAFETY_SERVICE_URL")

    # ---- 对话上下文 ----
    max_context_rounds: int = int(os.getenv("MAX_CONTEXT_ROUNDS", "10"))
    context_summary_model: str = os.getenv(
        "CONTEXT_SUMMARY_MODEL",
        "gpt-4o-mini",
    )

    # ---- 数据存储 ----
    data_dir: str = os.getenv("TUTOR_DATA_DIR", "./data")

    # ---- 生成参数 ----
    temperature: float = float(os.getenv("TUTOR_TEMPERATURE", "0.7"))
    max_tokens: int = int(os.getenv("TUTOR_MAX_TOKENS", "2048"))

    # ---- 附件支持 ----
    max_image_size_mb: int = int(os.getenv("MAX_IMAGE_SIZE_MB", "10"))
    image_description_model: str = os.getenv(
        "IMAGE_DESCRIPTION_MODEL",
        "gpt-4o-mini",
    )

    @property
    def is_multimodal_model(self) -> bool:
        """当前模型是否支持多模态输入"""
        return "gpt-4o" in self.llm_model or "gpt-4-turbo" in self.llm_model


@dataclass
class ProfileServiceRoutes:
    """画像服务 REST 路由"""

    get_profile: str = "/api/v1/profile/{session_id}"


# 全局单例
config = AppConfig()
profile_routes = ProfileServiceRoutes()
