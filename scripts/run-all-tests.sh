#!/usr/bin/env bash
# 运行全部测试（人员 C 负责的模块）
#   - common (TypeScript)：npm test
#   - common (Python)   ：pytest
#   - resource-gen      ：pytest
#   - path-planner      ：pytest
#
# 用法：
#   bash scripts/run-all-tests.sh
#
# Python 解释器探测顺序：
#   1. 环境变量 PYTHON（若已 export）
#   2. conda run -n ai_edu（若存在该环境）
#   3. 系统 python
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONIOENCODING=utf-8
FAILED=0

# ── 探测 Python ──────────────────────────────────────
if [ -n "${PYTHON:-}" ]; then
  PY_CMD=("$PYTHON")
elif command -v conda >/dev/null 2>&1 && conda env list 2>/dev/null | grep -q "ai_edu"; then
  PY_CMD=(conda run -n ai_edu --no-capture-output python)
else
  PY_CMD=(python)
fi
echo "使用 Python: ${PY_CMD[*]}"
"${PY_CMD[@]}" --version

run() {
  echo ""
  echo "════════════════════════════════════════"
  echo "  $1"
  echo "════════════════════════════════════════"
}

# 1) common (TypeScript)
run "[1/4] common (TypeScript)"
( cd "$ROOT/common" && npm run build >/dev/null 2>&1 && npm test ) || FAILED=1

# 2) common (Python)
run "[2/4] common (Python)"
( cd "$ROOT/common/python" && "${PY_CMD[@]}" -m pytest -q ) || FAILED=1

# 3) resource-gen
run "[3/4] agents/resource-gen"
( cd "$ROOT/agents/resource-gen" && "${PY_CMD[@]}" -m pytest -q ) || FAILED=1

# 4) path-planner
run "[4/4] agents/path-planner"
( cd "$ROOT/agents/path-planner" && "${PY_CMD[@]}" -m pytest -q ) || FAILED=1

echo ""
if [ "$FAILED" -eq 0 ]; then
  echo "✅ 全部测试通过"
else
  echo "❌ 存在失败，请查看上方输出"
fi
exit $FAILED
