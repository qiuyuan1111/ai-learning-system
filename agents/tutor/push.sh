#!/bin/bash
# ============================================
# 辅导智能体 - 独立推送脚本
# 使用: bash push.sh "提交说明"
# 示例: bash push.sh "feat: 实现个性化问答引擎"
# ============================================

REPO_URL="https://github.com/qiuyuan1111/ai-learning-system.git"
BRANCH="feature/agent-tutor"
COMMIT_MSG="${1:-feat(tutor): update}"

cd "$(dirname "$0")"

if [ ! -d ".git" ]; then
    git init
    git remote add origin "$REPO_URL"
fi

git add -A
git commit -m "$COMMIT_MSG"
git push -u origin HEAD:"$BRANCH"

echo "✅ 已推送到 $BRANCH 分支"
