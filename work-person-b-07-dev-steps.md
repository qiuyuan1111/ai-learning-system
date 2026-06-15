## 8. 开发步骤与 Git 提交计划

### 第 0 步：仓库初始化（开工前必做）

```
GitHub 仓库: https://github.com/qiuyuan1111/ai-learning-system (空仓库)

操作顺序:
1. 在项目根目录初始化 git
   → git init
   → git add .gitignore README.md .env.example
   → git commit -m "chore: initial project setup with .gitignore and README"

2. 关联远程仓库并推送 main 分支
   → git remote add origin https://github.com/qiuyuan1111/ai-learning-system.git
   → git branch -M main
   → git push -u origin main

3. 创建 develop 分支（所有 feature 分支从此切出）
   → git checkout -b develop main
   → git push -u origin develop

✅ 完成后，GitHub 上应看到:
   - main 分支: .gitignore + README.md + .env.example
   - develop 分支（与 main 同步）
   - 后续所有 feature 分支从 develop 创建
```

### 第 1 步：项目初始化 + 公共库协作（Day 1）

```
操作顺序:
1. 从 develop 分支创建 feature/agent-profile 分支
   → git checkout -b feature/agent-profile develop

2. 创建 agents/profile/ 项目结构
   → mkdir -p agents/profile/src/{models,services,prompts,db,ws}
   → mkdir -p agents/profile/tests

3. 安装 Python 依赖
   → cd agents/profile
   → pip install fastapi uvicorn websockets pydantic openai pytest
   → pip freeze > requirements.txt

4. 与人员 C 协作定义画像 Schema（放入 common/）
   - 确定 ProfileDimensions 的 6 个维度
   - 确定字段命名、类型、校验规则
   - 确定序列化格式

5. 实现 models/schema.py（完整的 Pydantic 模型）

✅ Git 提交：
   git add agents/profile/ common/
   git commit -m "feat(profile): init agent profile project with schema definition"
   git push -u origin feature/agent-profile
```

### 第 2 步：大模型调用封装（Day 2）

```
操作顺序:
1. 实现 services/llm_service.py
   - 封装 OpenAI API 调用
   - 实现 chat() 和 chat_stream() 方法
   - 配置从环境变量读取 API 密钥

2. 编写测试
   → pytest tests/test_llm_service.py

✅ Git 提交：
   git add .
   git commit -m "feat(profile): add LLM service with OpenAI API integration"
   git push
```

### 第 3 步：画像智能体核心（Day 3-5）

```
操作顺序:
1. 实现 services/profile_builder.py
   - ProfileBuilder 类
   - process_message() 方法
   - _extract_profile_info() — 从文本提取画像
   - _generate_question() — 追问生成
   - _assess_completeness() — 完整性判断

2. 实现 services/profile_updater.py
   - 增量更新逻辑
   - dialogue → profile 映射
   - evaluation → profile 映射

3. 实现 prompts/build.txt 和 prompts/update.txt
   - 精心设计提示词模板
   - 多次测试优化

4. 编写单元测试
   → pytest tests/test_profile_builder.py

✅ Git 提交（建议分多次）：
   git add . && git commit -m "feat(profile): implement profile builder with multi-turn dialogue"
   git add . && git commit -m "feat(profile): implement profile incremental updater"
   git add . && git commit -m "test(profile): add unit tests for profile builder"
   git push
```

### 第 4 步：画像智能体 WebSocket 接入（Day 5-6）

```
操作顺序:
1. 实现 ws/handler.py
   - 处理 WS 消息
   - 解析 intent=profile_build
   - 调用 ProfileBuilder
   - 组装响应帧

2. 实现 main.py（FastAPI + WebSocket）
   - WebSocket 端点 /ws/chat
   - 按 intent 路由
   - 启动脚本

3. 本地测试（配合网关 Mock 或直连）

✅ Git 提交：
   git add .
   git commit -m "feat(profile): add WebSocket endpoint for profile building"
   git push

   → 创建 PR 到 develop → 请求 Review → 合并
```

### 第 5 步：辅导智能体（Day 6-9，可与第 4 步并行）

```
操作顺序:
1. 从 develop 创建 feature/agent-tutor 分支
   → git checkout -b feature/agent-tutor develop

2. 创建 agents/tutor/ 项目结构
3. 复用 llm_service.py（或提取为公共模块）

4. 实现 services/context_manager.py
   - 对话记忆存储
   - 上下文截断和摘要

5. 实现 services/tutor_engine.py
   - _build_system_prompt() — 画像注入
   - _build_messages() — 消息组装
   - generate_answer() — 流式生成

6. 实现 prompts/
   - system.txt — 系统角色设定
   - adapt.txt — 画像适配模板

7. 实现 ws/handler.py + main.py

✅ Git 提交：
   git add . && git commit -m "feat(tutor): init tutor agent project"
   git add . && git commit -m "feat(tutor): implement tutor engine with profile-aware answers"
   git add . && git commit -m "feat(tutor): add WebSocket endpoint for tutoring"
   git add . && git commit -m "test(tutor): add tutor engine tests"
   git push -u origin feature/agent-tutor
   → 创建 PR → Review → 合并到 develop
```

### 第 6 步：评估智能体（Day 9-12）

```
操作顺序:
1. 从 develop 创建 feature/agent-evaluator 分支
   → git checkout -b feature/agent-evaluator develop

2. 创建 agents/evaluator/ 项目结构

3. 实现 services/quiz_grader.py
   - 选择题自动评分
   - 简答题大模型评分

4. 实现 services/behavior_analyzer.py
   - 行为数据 → 学习效率指标
   - 专注度评分

5. 实现 services/weakness_finder.py
   - 从错误中提取薄弱点
   - 从对话中提取困惑主题

6. 实现 services/evaluator.py（主评估引擎）
   - 综合评分
   - 报告生成

7. 实现 REST API（main.py）
   - POST /evaluation/submit
   - GET /sessions/{sessionId}/evaluation-report

✅ Git 提交：
   git add . && git commit -m "feat(evaluator): init evaluator agent project"
   git add . && git commit -m "feat(evaluator): implement quiz grading service"
   git add . && git commit -m "feat(evaluator): implement behavior analysis"
   git add . && git commit -m "feat(evaluator): implement weakness finder"
   git add . && git commit -m "feat(evaluator): implement evaluation engine and REST APIs"
   git add . && git commit -m "test(evaluator): add evaluator tests"
   git push -u origin feature/agent-evaluator
   → 创建 PR → Review → 合并到 develop
```

### 第 7 步：安全与防幻觉模块（Day 12-14，穿插进行）

```
操作顺序:
1. 从 develop 创建 feature/agent-safety 分支
   → git checkout -b feature/agent-safety develop

2. 创建 agents/safety/ 项目（或作为独立 Python 包）

3. 实现 ContentSafetyFilter
   - 敏感词库
   - 大模型审核接口
   - 拦截逻辑

4. 实现 HallucinationGuard
   - 引用核查
   - 置信度评估
   - 返回友好提示

5. 集成到各智能体中
   - 在画像、辅导、评估的输出前添加安全过滤步骤

✅ Git 提交：
   git add .
   git commit -m "feat(safety): implement content safety filter"
   git commit -m "feat(safety): implement hallucination guard"
   git commit -m "feat(safety): integrate safety checks into all agents"
   git push -u origin feature/agent-safety
   → 创建 PR → Review → 合并到 develop
```

### 第 8 步：三方联调（Day 14-18）

```
操作顺序:
1. 在本地启动 3 个智能体服务
   - agents/profile: 端口 8081
   - agents/tutor: 端口 8082
   - agents/evaluator: 端口 8080

2. 配合人员 A 的网关进行 WS 消息路由测试:
   - WS → profile_build → 画像智能体 ✓
   - WS → tutoring → 辅导智能体 ✓
   - REST → evaluation → 评估智能体 ✓

3. 配合人员 C 的共享 DTO 做序列化/反序列化测试

4. 修复集成问题

✅ Git 提交：
   git add .
   git commit -m "fix: resolve integration issues with gateway"
   git push
```

### 第 9 步：最终交付（Day 19-21）

```
✅ Git 操作：
   git checkout develop
   git merge feature/agent-profile
   git merge feature/agent-tutor
   git merge feature/agent-evaluator
   git merge feature/agent-safety
   git checkout main
   git merge develop
   git tag v1.0.0
   git push origin main --tags
```

---
