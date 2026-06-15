#!/bin/bash
# ============================================
# 安全审核模块 - 独立推送脚本
# 使用: bash push.sh "提交说明"
# 示例: bash push.sh "feat: 实现内容安全过滤器"
# ============================================

REPO_URL="https://github.com/qiuyuan1111/ai-learning-system.git"
BRANCH="feature/agent-safety"
COMMIT_MSG="${1:-feat(safety): update}"

cd "$(dirname "$0")"

if [ ! -d ".git" ]; then
    git init
    git remote add origin "$REPO_URL"
fi

git add -A
git commit -m "$COMMIT_MSG"
git push -u origin HEAD:"$BRANCH"

echo "✅ 已推送到 $BRANCH 分支"
