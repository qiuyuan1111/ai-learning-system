#!/usr/bin/env bash
# ============================================================
# 全量联调启动脚本（开发模式）—— 一键拉起全部服务
#   启动：  bash scripts/dev-all.sh
#   停止：  Ctrl+C
#
# 服务清单（safety 未实现，自动跳过）：
#   Python (ai_edu):
#     evaluator    8080 REST [B]    profile      8081 WS   [B]
#     tutor        8082 WS   [B]    resource-gen 8090 REST [你/C]
#     path-planner 8091 REST [你/C]
#   Node:
#     gateway      3000      [A]    frontend     5173      [A]
#
# 日志：logs/<服务>.log（每次运行旧日志归档到 logs/archive/<时间戳>/，不覆盖）
# 实时看：tail -f logs/resource-gen.log
#
# 用真 GLM：先 export LLM_API_KEY=你的智谱key 再跑（脚本自动配端点/模型/两套变量名）
# 输出故意全用英文，避免 Windows 控制台中文乱码。
# ============================================================

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# ── 探测 ai_edu 的 python 全路径 ──
if [ -n "${PYTHON:-}" ]; then
  AI_EDU_PY="$PYTHON"
elif command -v conda >/dev/null 2>&1 && conda env list 2>/dev/null | grep -q "ai_edu"; then
  AI_EDU_PY="$(conda run -n ai_edu python -c 'import sys; print(sys.executable)' 2>/dev/null)"
fi
# Windows (Git Bash): conda 返回 C:\.. 反斜杠路径，作为变量执行时找不到；
# 必须用 cygpath 转成 /c/.. 才能跑（Linux/Mac 无 cygpath 则原样保留）
if [ -n "${AI_EDU_PY:-}" ] && command -v cygpath >/dev/null 2>&1; then
  AI_EDU_PY="$(cygpath -u "$AI_EDU_PY")"
fi
# 校验：能跑 --version 才算可用（比 -x 可靠，避开 Windows 路径格式坑）
if [ -z "${AI_EDU_PY:-}" ] || ! "$AI_EDU_PY" --version >/dev/null 2>&1; then
  echo "[ERROR] Cannot find/run ai_edu python."
  echo "        Fix: 'conda activate ai_edu' first, OR"
  echo "        export PYTHON=/c/Users/20900/miniconda3/envs/ai_edu/python.exe"
  exit 1
fi

# ── 日志目录 + 归档上一次日志（不覆盖，保留联调历史）──
mkdir -p logs
[ -f logs/.gitignore ] || echo '*' > logs/.gitignore
if ls logs/*.log >/dev/null 2>&1; then
  TS=$(date +%Y%m%d-%H%M%S)
  mkdir -p "logs/archive/$TS"
  mv logs/*.log "logs/archive/$TS/" 2>/dev/null
  echo "[log] last logs archived to logs/archive/$TS/"
fi

# ── 统一 LLM 配置（代码不加载 .env，这里用环境变量注入；B/C 变量名不同，两套都设）──
# 默认假 key：B 能过启动校验（调 LLM 会失败），C 走 mock。
# 用真 key：先 export LLM_API_KEY=你的key，脚本自动配端点/模型/两套变量名 + 关 mock。
LLM_KEY="${LLM_API_KEY:-sk-dev-mock}"
if [ "$LLM_KEY" = "sk-dev-mock" ]; then
  echo "[LLM] No real key (sk-dev-mock). B starts but LLM calls fail; C uses mock."
  echo "[LLM] To use real LLM: export LLM_API_KEY=your-api-key then rerun."
  export LLM_API_KEY="$LLM_KEY" OPENAI_API_KEY="$LLM_KEY"
else
  LLM_URL="${LLM_BASE_URL:-https://api.deepseek.com/v1}"
  LLM_MDL="${LLM_MODEL:-deepseek-v4-flash}"
  echo "[LLM] REAL mode: base_url=$LLM_URL  model=$LLM_MDL  key=***"
  export LLM_API_KEY="$LLM_KEY"    OPENAI_API_KEY="$LLM_KEY" \
         LLM_BASE_URL="$LLM_URL"   OPENAI_BASE_URL="$LLM_URL" \
         LLM_MODEL="$LLM_MDL"      OPENAI_MODEL="$LLM_MDL" \
         LLM_USE_MOCK="false"
fi

# ── 服务间调用地址（B 的 tutor/evaluator 用 REST 调 profile；默认值已对齐 8081，这里再 export 一份双保险）──
export PROFILE_SERVICE_URL="${PROFILE_SERVICE_URL:-http://localhost:8081}"
export SAFETY_SERVICE_URL="${SAFETY_SERVICE_URL:-http://localhost:8083}"

PIDS=()

# 启动一个 Python 服务（-m uvicorn src.main:app，而非 src/main.py：避免相对导入错误）
start_py() {   # start_py <名字> <目录> <端口>
  local name="$1" dir="$2" port="$3"
  echo "[START] $name (:${port}) -> logs/${name}.log"
  ( cd "$ROOT/$dir" && exec "$AI_EDU_PY" -m uvicorn src.main:app --host 0.0.0.0 --port "$port" > "$ROOT/logs/${name}.log" 2>&1 ) &
  PIDS+=("$!")
}

# 启动一个 Node 服务
start_node() { # start_node <名字> <目录>
  local name="$1" dir="$2"
  echo "[START] $name -> logs/${name}.log"
  ( cd "$ROOT/$dir" && exec npm run dev > "$ROOT/logs/${name}.log" 2>&1 ) &
  PIDS+=("$!")
}

echo "============================================================"
echo "  AI-Edu System - Full Stack Dev (all services)"
  "$AI_EDU_PY" --version | sed 's/^/  Python: /'
echo "  ai_edu python: $AI_EDU_PY"
echo "============================================================"

# Python 智能体
start_py evaluator    agents/evaluator      8080
start_py profile      agents/profile        8081
start_py tutor        agents/tutor          8082
start_py resource-gen agents/resource-gen   8090
start_py path-planner agents/path-planner   8091

# 网关 + 前端
start_node gateway    gateway               # 3000
start_node frontend   frontend              # 5173

echo ""
echo "============================================================"
echo "  [OK] All services launched in background."
echo "  Logs: logs/*.log"
echo "------------------------------------------------------------"
echo "  evaluator    http://localhost:8080/docs   REST  (B)"
echo "  profile      ws://localhost:8081          WS    (B)"
echo "  tutor        ws://localhost:8082          WS    (B)"
echo "  resource-gen http://localhost:8090/docs   REST  (you)"
echo "  path-planner http://localhost:8091/docs   REST  (you)"
echo "  gateway      http://localhost:3000        gw    (A)"
echo "  frontend     http://localhost:5173        web   (A)"
echo "============================================================"
echo "  Live log:  tail -f logs/resource-gen.log"
echo "  Stop all:  Ctrl+C"
echo ""

trap 'echo ""; echo "Stopping all services..."; for p in "${PIDS[@]}"; do kill "$p" 2>/dev/null; done; sleep 1; echo "Done. (port still in use? close this window or taskkill)"; exit 0' INT TERM
wait
