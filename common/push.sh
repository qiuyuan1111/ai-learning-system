#!/bin/bash
# ============================================
# 共享 DTO 包 - 独立推送脚本
# 使用: bash push.sh "提交说明"
# 示例: bash push.sh "feat: 更新评估数据模型"
# ============================================

REPO_URL="https://github.com/qiuyuan1111/ai-learning-system.git"
BRANCH="feature/common-dto"
COMMIT_MSG="${1:-feat(common): update}"

cd "$(dirname "$0")"

if [ ! -d ".git" ]; then
    git init
    git remote add origin "$REPO_URL"
fi

git add -A
git commit -m "$COMMIT_MSG"
git push -u origin HEAD:"$BRANCH"

echo "✅ 已推送到 $BRANCH 分支"
