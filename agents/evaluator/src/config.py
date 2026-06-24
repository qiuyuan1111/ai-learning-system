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
    host: str = field(default_factory=lambda: os.getenv("EVALUATOR_HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: int(os.getenv("EVALUATOR_PORT", "8080")))
    debug: bool = field(default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true")

    # 数据库配置
    db_url: str = field(default_factory=lambda: os.getenv("DB_URL", "sqlite:///./evaluator.db"))

    # 画像服务调用（REST 调用，可选）
    profile_service_url: str = field(default_factory=lambda: os.getenv("PROFILE_SERVICE_URL", "http://localhost:8081"))
    profile_service_timeout: int = field(default_factory=lambda: int(os.getenv("PROFILE_SERVICE_TIMEOUT", "10")))

    # 评估维度权重（总和为 1.0）
    weight_knowledge_mastery: float = 0.30
    weight_understanding_depth: float = 0.25
    weight_application_ability: float = 0.20
    weight_learning_efficiency: float = 0.15
    weight_engagement: float = 0.10

    # 评分阈值
    high_score_threshold: float = 0.8
    medium_score_threshold: float = 0.6

    # 薄弱点分析
    max_weak_points: int = 5
    weakness_severity_threshold: int = 3  # 严重度 >= 3 才列入报告

    # 对话历史
    max_dialogue_rounds: int = 50

    def validate(self) -> None:
        """校验必要配置是否存在"""
        if not self.llm_api_key:
            raise ValueError("LLM_API_KEY 未配置")
        total_weight = (
            self.weight_knowledge_mastery
            + self.weight_understanding_depth
            + self.weight_application_ability
            + self.weight_learning_efficiency
            + self.weight_engagement
        )
        if abs(total_weight - 1.0) > 0.01:
            raise ValueError(f"评估维度权重之和应为 1.0，当前为 {total_weight}")


settings = Settings()
