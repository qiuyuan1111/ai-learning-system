# GitHub 协作配置指南

> **项目：** 个性化资源生成与学习多智能体系统  
> **团队：** 3 人  
> **版本：** v1.0

---

## 1. 前置准备（每人各自操作）

```bash
# ① 安装 Git → https://git-scm.com/downloads

# ② 生成 SSH 密钥并添加到 GitHub
ssh-keygen -t ed25519 -C "your_email@example.com"
cat ~/.ssh/id_ed25519.pub                    # 复制输出
# 打开 https://github.com/settings/keys → New SSH Key → 粘贴 → 保存

ssh -T git@github.com                        # 验证：看到 "Hi xxx" 即成功

# ③ 配置用户信息
git config --global user.name "你的名字"
git config --global user.email "your_email@example.com"
```

---

## 2. 创建仓库（队长操作）

```bash
# ① 浏览器打开 https://github.com/new
#    Repository name: ai-learning-system
#    勾选 Add a README → .gitignore: Python → Create repository

# ② 克隆到本地并推送
git clone git@github.com:队长用户名/ai-learning-system.git
cd ai-learning-system

# ③ 邀请成员：Settings → Collaborators → Add people（输入另两人的 GitHub 账号）
```

---

## 3. Git 分支规范

```
main          ← 稳定可演示版本，严格保护
  └─ develop  ← 集成开发分支，所有 PR 合并至此
       ├─ feature/frontend-xxx      # 人员 A
       ├─ feature/gateway-xxx
       ├─ feature/agent-profile     # 人员 B
       ├─ feature/agent-tutor
       ├─ feature/agent-evaluator
       ├─ feature/agent-safety
       ├─ feature/common-lib        # 人员 C
       ├─ feature/agent-resource-gen
       └─ feature/agent-path-planner
```

---

## 4. 日常协作流程

```bash
# 每天开始工作前
git checkout develop && git pull origin develop          # 拉取最新
git checkout -b feature/模块名                            # 创建功能分支

# 开发过程中的提交
git add <文件>
git commit -m "feat(模块): 描述"
git push -u origin feature/模块名

# 合并 develop 到自己的分支（每天至少 1 次，避免冲突堆积）
git merge develop
# 有冲突 → 手动解决 → git add → git commit → git push

# 功能完成后提 PR
# 浏览器打开 GitHub → Pull requests → New pull request
# base: develop  ←  compare: feature/xxx
# 标题: [Feature] 功能描述
# 指派另一人 Review → 至少 1 人 Approve → Squash and merge → 删除 feature 分支

# 合并后拉取最新 develop
git checkout develop && git pull origin develop
```

---

## 5. Commit Message 规范

```
<type>(<scope>): <描述>

type: feat | fix | refactor | docs | test | chore | ci
scope: profile | tutor | evaluator | resource-gen | path-planner | gateway | frontend | common

示例:
feat(profile): 添加多轮画像构建逻辑
fix(gateway): 修复 WS 连接超时
chore: 配置 ESLint
```

---

## 6. 冲突处理

```bash
git merge develop
# 提示 CONFLICT → 打开冲突文件，手动合并 → 删除 <<<<< ===== >>>>> 标记
git add <冲突文件>
git commit
git push
```

> **预防冲突：** 每天拉取 develop、避免多人同时改 `common/`、改公共文件前群里通知。

---

## 7. 环境变量与 API 密钥配置

### 7.1 各服务所需环境变量一览

| 服务 | 所需变量 | 提供方 |
|------|---------|--------|
| **网关** | `JWT_SECRET`、`PORT` | 人员 A |
| **画像智能体** | `OPENAI_API_KEY`、`OPENAI_MODEL` | 人员 B |
| **辅导智能体** | `OPENAI_API_KEY`、`OPENAI_MODEL` | 人员 B |
| **评估智能体** | `OPENAI_API_KEY`、`OPENAI_MODEL` | 人员 B |
| **资源生成编排器** | `OPENAI_API_KEY`、`OPENAI_MODEL`、`FILE_STORAGE_PATH` | 人员 C |
| **路径规划智能体** | `OPENAI_API_KEY`、`OPENAI_MODEL` | 人员 C |

### 7.2 获取 OpenAI API Key（每人各自操作）

```bash
# ① 注册/登录 OpenAI → https://platform.openai.com
# ② 进入 API keys 页面 → https://platform.openai.com/api-keys
# ③ 点击 "Create new secret key" → 复制并保存（关闭后不再显示）

# 推荐模型（按成本/效果排序）:
# GPT-4o        → 效果最好，适合复杂对话和评估
# GPT-4o-mini   → 性价比高，适合画像构建、大纲生成等常规任务
# text-embedding-3-small → 嵌入模型，适合语义搜索和资源匹配
```

> **费用预估：** GPT-4o-mini 约 $0.15/百万输入Token，开发阶段每人日均消耗约 $0.5-2，建议每人各自充值 $10-20。

### 7.3 `.env` 配置文件模板

#### 网关 `.env`（人员 A — `gateway/.env`）

```env
# 服务端口
PORT=3000

# JWT 密钥（任意随机字符串，生产环境需复杂）
JWT_SECRET=your-jwt-secret-change-in-production

# 后端服务地址（开发环境默认 localhost）
PROFILE_SERVICE_URL=http://localhost:8081
TUTOR_SERVICE_URL=http://localhost:8082
EVALUATOR_SERVICE_URL=http://localhost:8080
RESOURCE_GEN_SERVICE_URL=http://localhost:8090
PATH_PLANNER_SERVICE_URL=http://localhost:8091

# Mock 模式（true 时使用内置 Mock 数据，不需要后端服务）
MOCK_MODE=true

# 日志级别
LOG_LEVEL=debug
```

#### 画像智能体 `.env`（人员 B — `agents/profile/.env`）

```env
# OpenAI 配置
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_MODEL=gpt-4o-mini
OPENAI_BASE_URL=https://api.openai.com/v1
# 如使用国内代理/中转服务，替换上面的 BASE_URL 即可

# 服务端口
PORT=8081

# 数据库（可选，开发阶段用内存存储）
DATABASE_URL=sqlite:///data/profile.db
```

#### 辅导智能体 `.env`（人员 B — `agents/tutor/.env`）

```env
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_MODEL=gpt-4o
OPENAI_BASE_URL=https://api.openai.com/v1
PORT=8082
DATABASE_URL=sqlite:///data/chat_history.db
```

#### 评估智能体 `.env`（人员 B — `agents/evaluator/.env`）

```env
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_MODEL=gpt-4o-mini
OPENAI_BASE_URL=https://api.openai.com/v1
PORT=8080
DATABASE_URL=sqlite:///data/evaluation.db
```

#### 资源生成编排器 `.env`（人员 C — `agents/resource-gen/.env`）

```env
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_MODEL=gpt-4o
OPENAI_BASE_URL=https://api.openai.com/v1
PORT=8090

# 文件存储路径（生成的 PPT/PDF/MD 存放目录）
FILE_STORAGE_PATH=./storage

# 内容安全审核（可配合 OpenAI Moderation API）
ENABLE_SAFETY_CHECK=true
```

#### 路径规划智能体 `.env`（人员 C — `agents/path-planner/.env`）

```env
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_MODEL=gpt-4o-mini
OPENAI_BASE_URL=https://api.openai.com/v1
PORT=8091
DATABASE_URL=sqlite:///data/path.db
```

### 7.4 注意事项

```bash
# ① .env 文件必须加入 .gitignore，严禁提交到 GitHub
echo ".env" >> .gitignore
echo ".env.local" >> .gitignore

# ② 每人用自己的 API Key，各自创建 .env 文件
# ③ API Key 不要发到群里/聊天记录，防止泄露
# ④ 如果使用国内 API 中转服务，只需修改 OPENAI_BASE_URL
# ⑤ 如 API Key 泄露，立即到 OpenAI 后台 revoke 并重新生成
```

### 7.5 环境变量加载方式

各服务在代码中统一通过环境变量读取配置：

```python
# Python 示例（使用 python-dotenv）
from dotenv import load_dotenv
import os

load_dotenv()  # 自动读取 .env 文件

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # 带默认值
```

```typescript
// TypeScript 示例（使用 dotenv）
import dotenv from 'dotenv'
dotenv.config()

const JWT_SECRET = process.env.JWT_SECRET
const PORT = parseInt(process.env.PORT || '3000')
```

---

## 7. 最终发布（队长操作）

```bash
git checkout main && git pull origin main
git merge develop
git tag v1.0.0
git push origin main --tags
# GitHub → Releases → 填写版本说明 → Publish release
```

---

## 8. 常用命令速查

| 场景 | 命令 |
|------|------|
| 查看当前分支 | `git branch` |
| 创建并切换分支 | `git checkout -b feature/xxx` |
| 查看状态 | `git status` |
| 提交 | `git add . && git commit -m "type(scope): desc"` |
| 推送 | `git push` |
| 合并 develop | `git merge develop` |
| 放弃本地修改 | `git checkout -- <文件>` |
| 撤回上次提交（未推送） | `git reset --soft HEAD~1` |
| 撤回上次提交（已推送） | `git revert HEAD && git push` |
