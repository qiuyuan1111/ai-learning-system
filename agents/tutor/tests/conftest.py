"""
测试共享 Fixtures 和配置

自动被 pytest 加载，所有测试文件共享。
"""

import os
import sys
import tempfile

# 确保 src/ 可导入
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# 设置测试环境变量（避免依赖真实配置）
os.environ.setdefault("TUTOR_HOST", "127.0.0.1")
os.environ.setdefault("TUTOR_PORT", "18010")
os.environ.setdefault("LLM_API_KEY", "test-key")
os.environ.setdefault(
    "TUTOR_DATA_DIR",
    os.path.join(tempfile.gettempdir(), "tutor-test-data"),
)
os.environ.setdefault("PROFILE_SERVICE_URL", "http://localhost:18000")
