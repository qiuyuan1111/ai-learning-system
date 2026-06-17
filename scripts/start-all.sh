#!/usr/bin/env bash
# 一键启动人员 C 负责的服务（开发模式）
#   - common(Python)：已 pip install -e，无需进程
#   - resource-gen  : 端口 8090
#   - path-planner  : 端口 8091
#
# 用法：bash scripts/start-all.sh
# 退出：Ctrl+C 终止全部
set -e

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# 探测 Python（优先 PYTHON 变量，其次 conda ai_edu，最后系统 python）
if [ -n "${PYTHON:-}" ]; then
  PY_CMD=("$PYTHON")
elif command -v conda >/dev/null 2>&1 && conda env list 2>/dev/null | grep -q "ai_edu"; then
  PY_CMD=(conda run -n ai_edu --no-capture-output python)
else
  PY_CMD=(python)
fi

echo "=== 个性化学习系统（人员 C 服务）开发环境 ==="
echo "使用 Python: ${PY_CMD[*]}"
"${PY_CMD[@]}" --version
echo ""

# 0. 确保共享库已安装
echo "[0/3] 安装/更新 Python 共享库 ai_edu_common..."
( cd "$ROOT/common/python" && "${PY_CMD[@]}" -m pip install -e . -q )

# 1. 资源生成编排器
echo "[1/3] 启动 resource-gen (端口 8090)..."
( cd "$ROOT/agents/resource-gen" && \
  "${PY_CMD[@]}" -m uvicorn src.main:app --host 0.0.0.0 --port 8090 ) &
PID_RG=$!

# 2. 路径规划智能体
echo "[2/3] 启动 path-planner (端口 8091)..."
( cd "$ROOT/agents/path-planner" && \
  "${PY_CMD[@]}" -m uvicorn src.main:app --host 0.0.0.0 --port 8091 ) &
PID_PP=$!

# 3. 就绪提示
echo "[3/3] 服务启动中。"
echo "  resource-gen : http://localhost:8090/docs"
echo "  path-planner : http://localhost:8091/docs"
echo ""
echo "按 Ctrl+C 停止全部服务。"

trap 'echo ""; echo "停止服务..."; kill $PID_RG $PID_PP 2>/dev/null; exit 0' INT TERM
wait
