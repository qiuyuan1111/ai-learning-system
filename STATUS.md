# 📊 项目全局任务状态表

> 最后更新：2026-06-15
>
> 完成一个板块后，将对应 `[ ]` 改为 `[x]`，并更新进度百分比。

---

## 一、总体进度

| 板块 | 完成度 | 状态 |
|------|:------:|:----:|
| **🟢 agents/profile/** — 画像智能体 | █░░░░░░░░░ **0%** | ❌ 未开始 |
| **🔵 agents/tutor/** — 辅导智能体 | █░░░░░░░░░ **0%** | ❌ 未开始 |
| **🟠 agents/evaluator/** — 评估智能体 | █░░░░░░░░░ **0%** | ❌ 未开始 |
| **🟣 agents/safety/** — 安全与防幻觉 | █░░░░░░░░░ **0%** | ❌ 未开始 |
| **⚪ common/** — 共享 DTO | █░░░░░░░░░ **0%** | ❌ 未开始 |
| **📋 配置与基础设施** | ████████░░ **80%** | ✅ 基座完成 |
| | **总计** | █░░░░░░░░░ **~3%** |

---

## 二、基础设施

| # | 项 | 状态 | 说明 |
|---|----|:----:|------|
| 1 | `.gitignore` | ✅ 完成 | 全局 + 各模块独立 |
| 2 | `README.md` | ✅ 完成 | 项目首页 |
| 3 | `.env.example` | ✅ 完成 | 环境变量模板 |
| 4 | `push.sh` | ✅ 完成 | 各模块独立推送脚本 |
| 5 | `STATUS.md` | ✅ 完成 | 本进度表 |
| 6 | 目录结构创建 | ✅ 完成 | agents/*/src/... |
| 7 | GitHub 远程配置 | ✅ 完成 | Token 已存凭据 |

---

## 三、画像智能体 — `agents/profile/`

**目标：** 用户画像构建与增量更新（WebSocket: 8081）

### 3.1 任务列表

| 编号 | 任务 | 优先级 | 状态 | 完成日期 |
|------|------|:------:|:----:|:--------:|
| B-PR-01 | 画像 Schema 定义与校验 | P0 | ❌ | — |
| B-PR-02 | 对话式画像构建（多轮追问） | P0 | ❌ | — |
| B-PR-03 | 画像增量更新 | P0 | ❌ | — |
| B-PR-04 | 画像持久化 | P1 | ❌ | — |

### 3.2 文件清单

| 路径 | 状态 | 说明 |
|------|:----:|------|
| `src/main.py` | ❌ | FastAPI + WebSocket 端点 |
| `src/config.py` | ❌ | 配置 |
| `src/models/schema.py` | ❌ | Pydantic 画像模型 |
| `src/models/dto.py` | ❌ | 消息 DTO |
| `src/services/profile_builder.py` | ❌ | 画像构建核心 |
| `src/services/profile_updater.py` | ❌ | 画像增量更新 |
| `src/services/llm_service.py` | ❌ | 大模型调用 |
| `src/prompts/build.txt` | ❌ | 构建提示词 |
| `src/prompts/update.txt` | ❌ | 更新提示词 |
| `src/db/repository.py` | ❌ | 数据持久化 |
| `src/db/memory.py` | ❌ | 对话记忆 |
| `src/ws/handler.py` | ❌ | WS 消息处理 |
| `tests/test_profile_builder.py` | ❌ | 单元测试 |
| `tests/test_schema.py` | ❌ | 单元测试 |
| `push.sh` | ✅ | 推送脚本 |

---

## 四、辅导智能体 — `agents/tutor/`

**目标：** 个性化答疑与辅助教学（WebSocket: 8082）

### 4.1 任务列表

| 编号 | 任务 | 优先级 | 状态 | 完成日期 |
|------|------|:------:|:----:|:--------:|
| B-TU-01 | 个性化问答引擎 | P0 | ❌ | — |
| B-TU-02 | 基于画像的答案定制 | P0 | ❌ | — |
| B-TU-03 | 多模态输入处理 | P1 | ❌ | — |
| B-TU-04 | 对话上下文管理 | P0 | ❌ | — |

### 4.2 文件清单

| 路径 | 状态 | 说明 |
|------|:----:|------|
| `src/main.py` | ❌ | FastAPI + WebSocket 端点 |
| `src/config.py` | ❌ | 配置 |
| `src/models/context.py` | ❌ | 对话上下文模型 |
| `src/models/dto.py` | ❌ | 消息 DTO |
| `src/services/tutor_engine.py` | ❌ | 辅导引擎核心 |
| `src/services/answer_generator.py` | ❌ | 答案生成 |
| `src/services/context_manager.py` | ❌ | 上下文管理 |
| `src/services/llm_service.py` | ❌ | 大模型调用 |
| `src/prompts/system.txt` | ❌ | 系统提示词 |
| `src/prompts/adapt.txt` | ❌ | 画像适配提示词 |
| `src/db/chat_history.py` | ❌ | 对话历史存储 |
| `src/ws/handler.py` | ❌ | WS 消息处理 |
| `tests/test_tutor_engine.py` | ❌ | 单元测试 |
| `tests/test_answer_generator.py` | ❌ | 单元测试 |
| `push.sh` | ✅ | 推送脚本 |

---

## 五、评估智能体 — `agents/evaluator/`

**目标：** 学习评估与薄弱点分析（REST: 8080）

### 5.1 任务列表

| 编号 | 任务 | 优先级 | 状态 | 完成日期 |
|------|------|:------:|:----:|:--------:|
| B-EV-01 | 评估数据提交 REST API | P0 | ❌ | — |
| B-EV-02 | 评估报告生成 REST API | P0 | ❌ | — |
| B-EV-03 | 多维度评价模型 | P0 | ❌ | — |
| B-EV-04 | 薄弱知识点分析 | P0 | ❌ | — |
| B-EV-05 | 路径调整建议输出 | P1 | ❌ | — |
| B-EV-06 | 行为数据收集与分析 | P1 | ❌ | — |

### 5.2 文件清单

| 路径 | 状态 | 说明 |
|------|:----:|------|
| `src/main.py` | ❌ | FastAPI + REST 端点 |
| `src/config.py` | ❌ | 配置 |
| `src/models/evaluation.py` | ❌ | 评估模型 |
| `src/models/dto.py` | ❌ | 请求/响应 DTO |
| `src/services/evaluator.py` | ❌ | 评估引擎核心 |
| `src/services/quiz_grader.py` | ❌ | 答题评分 |
| `src/services/behavior_analyzer.py` | ❌ | 行为分析 |
| `src/services/weakness_finder.py` | ❌ | 薄弱点发现 |
| `src/services/llm_service.py` | ❌ | 大模型调用 |
| `src/prompts/grade.txt` | ❌ | 评分提示词 |
| `src/prompts/analyze.txt` | ❌ | 分析提示词 |
| `src/db/repository.py` | ❌ | 数据持久化 |
| `tests/*` | ❌ | 单元测试 |
| `push.sh` | ✅ | 推送脚本 |

---

## 六、安全与防幻觉 — `agents/safety/`

**目标：** 内容安全过滤 + 事实核查（REST 内部: 8083）

### 6.1 任务列表

| 编号 | 任务 | 优先级 | 状态 | 完成日期 |
|------|------|:------:|:----:|:--------:|
| B-SF-01 | 内容安全过滤器 | P0 | ❌ | — |
| B-SF-02 | 事实核查/防幻觉 | P0 | ❌ | — |

### 6.2 文件清单

| 路径 | 状态 | 说明 |
|------|:----:|------|
| `src/main.py` ❌ | REST API 入口 |
| `src/config.py` ❌ | 配置 |
| `src/safety_filter.py` ❌ | 内容安全过滤器 |
| `src/hallucination_guard.py` ❌ | 防幻觉校验 |
| `src/llm_service.py` ❌ | 大模型调用 |
| `prompts/*` | ❌ | 提示词 |
| `tests/*` | ❌ | 单元测试 |
| `push.sh` | ✅ | 推送脚本 |

---

## 七、共享 DTO — `common/`

**目标：** 各模块共享的数据模型与工具

### 7.1 文件清单

| 路径 | 状态 | 说明 |
|------|:----:|------|
| `__init__.py` | ❌ | 包初始化 |
| `ws_dto.py` | ❌ | WS 消息帧 DTO |
| `api_response.py` | ❌ | REST 响应体 |
| `evaluation_dto.py` | ❌ | 评估数据模型 |
| `push.sh` | ✅ | 推送脚本 |

---

## 八、开发阶段进度

| 阶段 | 时间 | 状态 | 说明 |
|------|:----:|:----:|------|
| 第 0 步 | 仓库初始化 | ✅ 完成 | .gitignore + README + 远程配置 |
| 第 1 步 | Day 1 | ❌ | 项目初始化 + 公共库协作 |
| 第 2 步 | Day 2 | ❌ | 大模型调用封装 |
| 第 3 步 | Day 3-5 | ❌ | 画像智能体核心 |
| 第 4 步 | Day 5-6 | ❌ | 画像智能体 WebSocket 接入 |
| 第 5 步 | Day 6-9 | ❌ | 辅导智能体（可与第 4 步并行） |
| 第 6 步 | Day 9-12 | ❌ | 评估智能体 |
| 第 7 步 | Day 12-14 | ❌ | 安全与防幻觉模块 |
| 第 8 步 | Day 14-18 | ❌ | 三方联调 |
| 第 9 步 | Day 19-21 | ❌ | 最终交付 |

---

## 九、Git 分支状态

| 分支 | 用途 | 状态 | 最新提交 |
|------|------|:----:|---------|
| `main` | 生产就绪 | ✅ 已推送 | 初始提交 |
| `develop` | 集成开发 | ✅ 已推送 | 与 main 同步 |
| `feature/agent-profile` | 画像智能体 | ❌ 未创建 | — |
| `feature/agent-tutor` | 辅导智能体 | ❌ 未创建 | — |
| `feature/agent-evaluator` | 评估智能体 | ❌ 未创建 | — |
| `feature/agent-safety` | 安全模块 | ❌ 未创建 | — |
| `feature/common-dto` | 共享 DTO | ❌ 未创建 | — |

---

## 📝 更新指南

完成一个任务后，执行以下操作：

```bash
# 1. 编辑 STATUS.md，将对应 [ ] 改为 [x]
# 2. 提交并推送更新
git add STATUS.md
git commit -m "chore: update progress - 完成 XXX 任务"
git push
```

或者直接说：**"帮我更新进度 — 完成了 XXX"**
