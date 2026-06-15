---
name: prepare-workspace
description: 项目工作区初始化 — 从分析原始文档到完成模块结构、Git配置、推送脚本和进度跟踪的完整工作流
---

# Prepare Workspace — 项目初始化工作流

## 触发方式

在项目根目录执行：
```
/prepare-workspace
```

或在其他项目中使用：
```
/prepare-workspace <path/to/root-doc.md>
```

## 工作流概述

将一份原始项目文档（如 `work-person-b.md`）拆解为解耦的板块，创建对应的目录结构，配置 Git 远程和认证，为每个模块准备独立的推送能力，最终生成全局进度跟踪表。

---

## 工作流步骤

### 第 1 步：读取并分析原始文档

读取指定的 `.md` 文件，识别以下结构：

1. **元信息** — 负责人、模块范围、协作对象
2. **技术栈** — 编程语言、框架、依赖
3. **任务列表** — 按优先级分组（P0/P1）
4. **项目结构树** — 每个模块的目录结构（`src/`、`tests/`、`Dockerfile` 等）
5. **任务详解** — 每个模块的核心服务类、API 定义、数据模型
6. **开发步骤** — Git 分支策略和提交计划
7. **附录** — 端口分配、提示词模板

### 第 2 步：拆分为解耦的板块

保持内容不变，按自然边界拆分为独立的 `.md` 文件：

| # | 板块 | 内容 |
|---|------|------|
| 01 | `*-01-overview.md` | 元信息 + 技术栈 + 任务总览 |
| 02 | `*-02-<module-a>.md` | 模块 A 任务详解 |
| 03 | `*-03-<module-b>.md` | 模块 B 任务详解 |
| 04 | `*-04-<module-c>.md` | 模块 C 任务详解 |
| 05 | `*-05-<module-d>.md` | 模块 D 任务详解 |
| 06 | `*-06-core-dto.md` | 共享 DTO 数据模型 |
| 07 | `*-07-dev-steps.md` | 开发步骤与 Git 计划 |
| 08 | `*-08-appendix.md` | 附录 |

拆分原则：
- **按职责边界切割** — 每个智能体/模块独立成文件
- **不做任何内容修改** — 代码、表格、注释、格式均保持原样
- **每个文件自包含** — 可独立查阅，不依赖其他文件

### 第 3 步：创建项目目录结构

根据文档中的项目结构树，使用 `mkdir -p` 创建完整目录：

```bash
# 示例：画像智能体
mkdir -p agents/profile/src/{models,services,prompts,db,ws}
mkdir -p agents/profile/tests

# 示例：辅导智能体
mkdir -p agents/tutor/src/{models,services,prompts,db,ws}
mkdir -p agents/tutor/tests

# 示例：评估智能体
mkdir -p agents/evaluator/src/{models,services,prompts,db}
mkdir -p agents/evaluator/tests

# 示例：安全模块
mkdir -p agents/safety/src/{prompts,tests}

# 共享 DTO
mkdir -p common
```

### 第 4 步：放置板块文档

将拆分的 `.md` 文件移入对应模块目录：

```bash
mv *-02-<module-a>.md agents/<module-a>/
mv *-03-<module-b>.md agents/<module-b>/
mv *-04-<module-c>.md agents/<module-c>/
mv *-05-<module-d>.md agents/<module-d>/
mv *-06-core-dto.md common/
```

项目总览、开发步骤、附录保留在根目录。

### 第 5 步：写好 GitHub 提交配置

为项目根目录和各模块创建完整的提交配置。

#### 5a. 根级配置文件

| 文件 | 用途 |
|------|------|
| `.gitignore` | Python 项目过滤规则（`__pycache__/`, `.env`, `venv/`, `.idea/` 等），`.env.example` 需用 `!.env.example` 排除 |
| `README.md` | 项目首页：架构图、模块说明、技术栈、快速开始、分支策略 |
| `.env.example` | 环境变量模板（不含真实密钥） |
| `docker-compose.yml` | 本地多服务编排（可选） |

#### 5b. 各模块 `requirements.txt`

根据模块职责确定依赖：

```txt
# 通用
fastapi>=0.115.0
uvicorn[standard]>=0.32.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
openai>=1.0.0
python-dotenv>=1.0.0
-e ../../common    # 共享 DTO 包引用

# WebSocket 模块额外加
websockets>=12.0

# 文件上传模块额外加
python-multipart>=0.0.9

# Dev
pytest>=8.0.0
pytest-asyncio>=0.24.0
httpx>=0.27.0
```

#### 5c. 各模块 `pyproject.toml`

```toml
[project]
name = "agent-<name>"
version = "0.1.0"
description = "<模块描述>"
requires-python = ">=3.11"
dependencies = []

[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.backends._legacy:_Backend"
```

#### 5d. 各模块 `Dockerfile`

```dockerfile
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends gcc \
    && rm -rf /var/lib/apt/lists/*
COPY common/ /app/common/
RUN pip install -e /app/common/
COPY agents/<module>/requirements.txt /app/agents/<module>/
RUN pip install --no-cache-dir -r /app/agents/<module>/requirements.txt
COPY agents/<module>/src/ /app/agents/<module>/src/
EXPOSE <port>
CMD ["uvicorn", "agents.<module>.src.main:app", "--host", "0.0.0.0", "--port", "<port>"]
```

`Dockerfile` 要点：
- `context: .`（从项目根构建，而非模块内），以便 COPY common/
- `WORKDIR /app` 保证路径统一

#### 5e. 各模块 `.dockerignore`

```
__pycache__/
*.pyc
.venv/
venv/
.env
*.egg-info/
.git/
```

#### 5f. 各模块 `.gitignore`（模块级）

```
__pycache__/
*.py[cod]
*.pyo
*.egg-info/
dist/
build/
.env
.venv/
venv/
*.db
*.sqlite3
```

### 第 6 步：GitHub 认证配置

```bash
# 方案 A：Personal Access Token（推荐）
git remote set-url origin https://<TOKEN>@github.com/<user>/<repo>.git

# 或者存储到全局凭据（更安全）
git config credential.helper store
echo "https://<user>:<TOKEN>@github.com" >> ~/.git-credentials

# 方案 B：GitHub CLI
gh auth login
```

Token 说明：
- 必须是 Fine-grained PAT，开启 `Contents: Read and Write` 权限
- 存储到 `~/.git-credentials` 后，各模块独立推送时自动复用

### 第 7 步：独立推送脚本 `push.sh`

为每个模块创建推送脚本：

```bash
#!/bin/bash
REPO_URL="https://github.com/<user>/<repo>.git"
BRANCH="feature/<module-name>"
COMMIT_MSG="${1:-feat(<module>): update}"

cd "$(dirname "$0")"

if [ ! -d ".git" ]; then
    git init
    git remote add origin "$REPO_URL"
fi

git add -A
git commit -m "$COMMIT_MSG"
git push -u origin HEAD:"$BRANCH"

echo "✅ 已推送到 $BRANCH 分支"
```

每个模块的推送分支对应：

| 模块 | 推送分支 |
|------|---------|
| `agents/profile/` | `feature/agent-profile` |
| `agents/tutor/` | `feature/agent-tutor` |
| `agents/evaluator/` | `feature/agent-evaluator` |
| `agents/safety/` | `feature/agent-safety` |
| `common/` | `feature/common-dto` |

使用方式：
```bash
cd agents/profile
bash push.sh "feat(profile): add profile builder core logic"
```

### 第 8 步：全局任务状态表 `STATUS.md`

创建全局进度跟踪文件，包含：

1. **总体进度** — 各板块完成度 + 进度条
2. **基础设施** — `.gitignore`、`README`、`push.sh` 等配置状态
3. **各模块任务** — 按原文档编号（B-PR-01 等），含优先级、状态、完成日期
4. **各模块文件清单** — 每个需要实现的文件（`src/*.py`、`tests/*.py` 等）
5. **开发阶段进度** — 各阶段状态
6. **Git 分支状态** — 各分支创建和推送情况
7. **更新指南** — 如何修改进度

格式示例：
```markdown
| 编号 | 任务 | 优先级 | 状态 | 完成日期 |
|------|------|:------:|:----:|:--------:|
| B-PR-01 | 画像 Schema 定义 | P0 | ❌ | — |
| B-PR-02 | 对话式画像构建 | P0 | ✅ | 2026-06-15 |
```

---

## 技能依赖

- 环境：`bash`、`git`、`mkdir`、`chmod`
- 认证：GitHub PAT（Fine-grained, Contents: Read/Write）
- 可选：`gh` CLI

## 注意事项

- 所有配置文件使用 LF 换行符（`.gitattributes` 可配置）
- Token 不要硬编码在脚本中，应存入 `~/.git-credentials`
- 各模块目录结构已在文档中定义，严格按文档创建
- 拆分文档时 **不做任何内容修改**，保持代码/表格/格式原样
- 各模块的 `push.sh` 使用独立 git init（嵌套仓库），不依赖根目录 `.git`
