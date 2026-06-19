"""resource-gen 测试公共夹具。"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# 让 tests 能 import src.*
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


@pytest.fixture
def tmp_storage(tmp_path, monkeypatch):
    """把文件存储重定向到临时目录，避免污染。"""
    from src import config

    monkeypatch.setattr(config.settings, "FILE_STORAGE_PATH", tmp_path)
    monkeypatch.setattr(config.settings, "PUBLIC_BASE_URL", "http://test/files")
    config.settings.ensure_storage_dir()
    return tmp_path


@pytest.fixture
def container(tmp_storage):
    """每个测试用全新容器，避免状态串扰。"""
    from src.dependencies import Container

    c = Container()
    return c


@pytest.fixture
def sample_profile():
    return {
        "sessionId": "sess_demo",
        "dimensions": {
            "knowledgeBase": {
                "level": "intermediate",
                "tags": ["Python", "机器学习"],
                "confidence": 0.8,
            },
            "weaknessPreferences": [
                {"weakTags": ["注意力机制"], "confidence": 0.7}
            ],
            "interestAreas": [{"areas": ["NLP"], "depth": 3, "confidence": 0.6}],
            "targetDifficulty": {"level": 7, "confidence": 0.5},
        },
        "updatedAt": "2026-06-15T10:00:00Z",
        "version": 1,
    }
