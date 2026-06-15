#!/bin/bash
# ============================================
# 画像智能体 - 独立推送脚本
# 使用: bash push.sh "提交说明"
# 示例: bash push.sh "feat: 实现画像构建核心逻辑"
# ============================================

REPO_URL="https://github.com/qiuyuan1111/ai-learning-system.git"
BRANCH="feature/agent-profile"
COMMIT_MSG="${1:-feat(profile): update}"

# 切换到脚本所在目录
cd "$(dirname "$0")"

# 初始化 git（如果尚未初始化）
if [ ! -d ".git" ]; then
    git init
    git remote add origin "$REPO_URL"
fi

# 添加所有文件
git add -A

# 提交
git commit -m "$COMMIT_MSG"

# 推送到远程分支
git push -u origin HEAD:"$BRANCH"

echo "✅ 已推送到 $BRANCH 分支"
