#!/bin/bash
# ============================================
# 评估智能体 - 独立推送脚本
# 使用: bash push.sh "提交说明"
# 示例: bash push.sh "feat: 实现评估数据提交API"
# ============================================

REPO_URL="https://github.com/qiuyuan1111/ai-learning-system.git"
BRANCH="feature/agent-evaluator"
COMMIT_MSG="${1:-feat(evaluator): update}"

cd "$(dirname "$0")"

if [ ! -d ".git" ]; then
    git init
    git remote add origin "$REPO_URL"
fi

git add -A
git commit -m "$COMMIT_MSG"
git push -u origin HEAD:"$BRANCH"

echo "✅ 已推送到 $BRANCH 分支"
