"""应用配置"""

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Settings:
    # 大模型配置
    llm_api_key: str = field(default_factory=lambda: os.getenv("LLM_API_KEY", ""))
    llm_model: str = field(default_factory=lambda: os.getenv("LLM_MODEL", "gpt-4o"))
    llm_base_url: Optional[str] = field(default_factory=lambda: os.getenv("LLM_BASE_URL") or None)

    # 服务配置
    host: str = field(default_factory=lambda: os.getenv("SAFETY_HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: int(os.getenv("SAFETY_PORT", "8083")))
    debug: bool = field(default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true")

    # 内容安全配置
    enable_keyword_filter: bool = field(default_factory=lambda: os.getenv("ENABLE_KEYWORD_FILTER", "true").lower() == "true")
    enable_llm_moderation: bool = field(default_factory=lambda: os.getenv("ENABLE_LLM_MODERATION", "true").lower() == "true")
    enable_rule_engine: bool = field(default_factory=lambda: os.getenv("ENABLE_RULE_ENGINE", "true").lower() == "true")

    # 防幻觉配置
    enable_citation_check: bool = field(default_factory=lambda: os.getenv("ENABLE_CITATION_CHECK", "true").lower() == "true")
    enable_fact_consistency: bool = field(default_factory=lambda: os.getenv("ENABLE_FACT_CONSISTENCY", "true").lower() == "true")
    enable_confidence_eval: bool = field(default_factory=lambda: os.getenv("ENABLE_CONFIDENCE_EVAL", "true").lower() == "true")
    hallucination_confidence_threshold: float = field(
        default_factory=lambda: float(os.getenv("HALLUCINATION_CONFIDENCE_THRESHOLD", "0.6"))
    )

    # 画像服务调用（可选）
    profile_service_url: str = field(default_factory=lambda: os.getenv("PROFILE_SERVICE_URL", "http://localhost:8081"))
    profile_service_timeout: int = field(default_factory=lambda: int(os.getenv("PROFILE_SERVICE_TIMEOUT", "10")))

    # 关键词过滤配置
    keyword_filter_path: str = field(default_factory=lambda: os.getenv("KEYWORD_FILTER_PATH", ""))
    custom_sensitive_words: str = field(default_factory=lambda: os.getenv("CUSTOM_SENSITIVE_WORDS", ""))

    def validate(self) -> None:
        """校验必要配置是否存在"""
        if not self.llm_api_key:
            raise ValueError("LLM_API_KEY 未配置")


settings = Settings()
