"""profile agent tests — 自动将 src 加入 Python 路径"""

import sys
import os
from pathlib import Path

# 确保 src 目录在 sys.path 中，使 `from src.models...` 导入可用
_root = str(Path(__file__).resolve().parent.parent)
if _root not in sys.path:
    sys.path.insert(0, _root)
