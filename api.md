作为科大讯飞产品经理，针对第十五届软件杯A组赛题“基于大模型的个性化资源生成与学习多智能体系统”，制定本接口规范与协作开发指南。本文档旨在统一前后端、多智能体间的通信契约，实现各功能层充分解耦，支持多名开发者并行研发、独立提交并通过GitHub高效合并。

---

# 个性化资源学习多智能体系统 — API接口规范与协作开发指南 v1.0

| 文档版本 | 1.0 |
|---------|-----|
| 发布日期 | 2026-06-15 |
| 制定人 | 科大讯飞 产品经理 |
| 适用范围 | 前端、画像智能体、资源生成智能体、路径规划智能体、辅导智能体、评估智能体、网关 |

---

## 1. 基础信息

### 1.1 系统概述
系统采用“1个前端入口 + 1个API网关 + N个智能体微服务”的架构。外部客户端（Web/移动/小程序）通过网关访问统一的REST API和WebSocket，网关负责鉴权、路由、流控，并将请求转发至对应的智能体服务。智能体服务之间通过内部REST或消息队列协作，所有对外契约均以本文档为准。

### 1.2 通信协议
- 外部API：HTTPS + JSON，字符编码UTF-8
- 流式交互：Server-Sent Events (SSE) 或 WebSocket（统一采用 `/ws` 端点，消息格式为JSON帧）
- 内部服务间：HTTP/2 + JSON（或gRPC，需在同源文档中单独约定，不影响对外规范）

### 1.3 统一基础路径
```
https://{domain}/api/v1
```

### 1.4 认证方式
采用“学习会话令牌”机制：
- 首次进入系统调用 `POST /sessions` 获取 `sessionToken`
- 后续请求在 HTTP Header 中携带：`Authorization: Bearer <sessionToken>`
- WebSocket 连接参数：`?token=<sessionToken>`

### 1.5 通用响应格式
所有非流式接口统一返回以下 JSON 结构：
```json
{
  "code": 0,
  "message": "success",
  "data": { ... },
  "requestId": "uuid"
}
```
- `code`：业务状态码，0 表示成功，非 0 表示异常（见异常章节）
- `message`：提示信息
- `data`：具体返回数据，可为对象、数组或 null
- `requestId`：请求追踪ID

分页响应在 `data` 内增加 `pageInfo`：
```json
"data": {
  "list": [ ... ],
  "pageInfo": {
    "page": 1,
    "pageSize": 20,
    "total": 100,
    "totalPages": 5
  }
}
```

### 1.6 流式响应格式 (SSE)
```
event: message
data: {"type":"text","content":"这是流式文本","msgId":"..."}

event: resource
data: {"type":"resource_card","resourceType":"ppt","url":"...","title":"..."}

event: done
data: {"type":"done","msgId":"..."}
```
客户端根据 `type` 渲染对应的 Markdown 文本、卡片或进度状态。

---

## 2. 接口定义

### 2.1 会话管理

#### 2.1.1 创建学习会话
**POST** `/sessions`

请求体：
```json
{
  "nickname": "小明",
  "major": "人工智能",
  "grade": "本科三年级"
}
```
> 仅需极少量信息，其余画像通过对话补全。

响应 `data`：
```json
{
  "sessionId": "sess_abc123",
  "token": "eyJ...",
  "profile": { ... }        // 初始画像（维度可能不全）
}
```

---

### 2.2 对话式学习画像与智能辅导（统一聊天接口）

采用 WebSocket 建立长连接，实现多轮对话。该通道同时承担：画像构建、资源生成指令下达、智能辅导、学习路径问询等功能。前端通过同一连接发送不同的 `intent` 区分业务。

**WS连接地址**：`/ws/chat?token=<token>`

**客户端发送消息帧**：
```json
{
  "msgId": "client_uuid",
  "intent": "profile_build",        // 意图：profile_build | resource_generate | tutoring | path_query | evaluate
  "content": {
    "text": "我最近在学习 Transformer，总感觉注意力机制理解不到位。",
    "attachments": [                // 可选多模态附件
      {
        "type": "image",
        "url": "https://...",
        "mimeType": "image/png"
      }
    ]
  },
  "context": {                      // 可选上下文
    "resourceId": "res_123",        // 针对某个资源提问时传入
    "courseId": "ai_basic"
  }
}
```

**服务端推送帧**（统一格式）：
```json
{
  "msgId": "srv_uuid",
  "replyTo": "client_uuid",
  "intent": "profile_build",
  "type": "text",                  // text | resource_card | progress | done | error
  "content": { ... }
}
```
当 `type` 为 `"progress"` 时，`content` 包含进度百分比和描述，用于资源生成等长耗时任务的白屏等待优化。
`"done"` 表示本轮对话逻辑结束，可附带汇总卡片。

**常见 content 示例**：
- 文本解答：`{ "markdown": "注意力机制的核心是..." }`
- 资源卡片：
```json
{
  "resourceType": "mindmap",
  "title": "Transformer注意力机制思维导图",
  "url": "https://cdn.xxx/mindmap.html",
  "description": "覆盖Self-Attention、Multi-Head等"
}
```
- 学习路径卡片：
```json
{
  "pathId": "path_uuid",
  "nodes": [ { "order":1, "title":"...", "resourceId":"...", "type":"doc" } ]
}
```

> **解耦说明**：WebSocket 网关只做消息路由，根据 `intent` 将消息转发至画像智能体、辅导智能体或资源生成编排器等；每个智能体可以独立开发、部署，只要遵守上述帧格式。

---

### 2.3 个性化资源生成（异步任务）

当对话意图为 `resource_generate` 且涉及复杂多模态资源时，系统可能转为异步任务。此时服务端推送 `type: "progress"` 并附带 `taskId`，前端可选择性通过 REST 接口查询进度与结果。

#### 2.3.1 查询任务状态
**GET** `/resource-tasks/{taskId}`

响应 `data`：
```json
{
  "taskId": "task_xyz",
  "status": "processing",          // pending | processing | completed | failed
  "progress": 65,
  "result": {                      // 完成后返回
    "resources": [
      {
        "resourceId": "res_001",
        "type": "ppt",
        "title": "卷积神经网络入门",
        "url": "https://...",
        "metadata": { ... }
      }
    ]
  }
}
```

#### 2.3.2 获取已生成资源列表
**GET** `/sessions/{sessionId}/resources?type=ppt&page=1&pageSize=20`

用于资源库界面展示。

---

### 2.4 个性化学习路径规划与推送

#### 2.4.1 获取当前学习路径
**GET** `/sessions/{sessionId}/learning-path`

返回完整的动态学习路径树，节点已排序，并附推荐资源摘要。
```json
{
  "pathId": "path_uuid",
  "updatedAt": "2026-06-15T10:00:00Z",
  "nodes": [
    {
      "nodeId": "node1",
      "order": 1,
      "title": "数学基础回顾",
      "resource": { "resourceId": "...", "type": "doc", "url": "..." },
      "status": "completed"
    }
  ]
}
```

#### 2.4.2 触发资源推送
学习路径更新后，网关自动通过 WebSocket 推送资源卡片（无需单独REST接口）。前端亦可调用 `POST /sessions/{sessionId}/recommend` 强制触发一次推送，响应为空，实际内容通过WS下发。

---

### 2.5 学习效果评估（可选加分项）

#### 2.5.1 提交评估数据
**POST** `/evaluation/submit`
```json
{
  "sessionId": "sess_abc",
  "quizId": "quiz_01",
  "answers": [ { "questionId":"q1", "answer":"B", "timeSpent":45 } ],
  "behaviors": [ { "action":"video_pause", "resourceId":"...", "timestamp":"..." } ]
}
```

#### 2.5.2 获取评估报告
**GET** `/sessions/{sessionId}/evaluation-report`

返回多维度评价、薄弱知识点、建议调整的学习路径节点等。

---

## 3. 异常规范

### 3.1 HTTP状态码
- 200：业务处理完成（具体看 `code`）
- 400：请求参数错误
- 401：未认证或 token 过期
- 403：无权限
- 404：资源不存在
- 500：系统内部异常

### 3.2 业务错误码
| code | 说明 |
|------|------|
| 0 | 成功 |
| 1001 | 参数缺失或格式错误 |
| 1002 | 会话不存在 |
| 2001 | 资源生成任务不存在 |
| 2002 | 资源生成失败（含原因） |
| 3001 | 内容安全审核未通过 |
| 3002 | 防幻觉校验未通过，未生成回答 |
| 4001 | 智能体服务超时 |
| 5000 | 系统未知错误 |

错误响应示例：
```json
{
  "code": 3001,
  "message": "生成内容包含违规信息，已拦截",
  "data": null,
  "requestId": "..."
}
```

---

## 4. 业务场景与接口调用示例

### 场景一：新用户进入系统，构建画像
1. 前端 `POST /sessions` 创建会话，获得 token。
2. 建立 WebSocket，发送 `intent=profile_build` 的消息：“我是人工智能大三学生，刚学完吴恩达机器学习，想深入NLP。”
3. 画像智能体流式追问2-3轮（如“你更喜欢理论推导还是代码实战？”），同时逐步更新画像。
4. 前端收到多条 `type=text` 和最后 `type=done`，画像构建完成。

### 场景二：请求生成个性化PPT
1. 用户在聊天框输入：“帮我生成一份BERT模型的讲解PPT，要包含对比CNN的内容。”
2. 前端发送 `intent=resource_generate`，服务端立即返回 `type=progress`，`taskId`。
3. 资源生成编排器调用多个智能体：大纲智能体→内容撰写智能体→PPT渲染智能体→审核智能体（防幻觉、内容安全）。
4. 前端可选择展示进度条，同时可自由进行其他对话。
5. 生成完成后，服务端通过WS推送 `type=resource_card`，前端直接展示下载卡片。

### 场景三：学习路径查询与动态调整
1. 用户点击“学习路径”页面，前端调用 `GET /sessions/{sessionId}/learning-path`。
2. 路径规划智能体根据最新画像和已生成资源返回有序节点。
3. 用户完成某个节点后，评估智能体收集行为数据，重新计算画像，路径自动调整，服务端通过WS推送更新后的路径卡片。

---

## 5. 约束与边界条件

### 5.1 防幻觉与内容安全
- 所有智能体在生成最终答案前，必须过“内容安全过滤器”与“事实核查模块”。
- 当检测到生成内容存在高风险幻觉或违规时，应返回错误码 `3001` 或 `3002`，并推送一条 `type=text` 友好提示：“该问题暂无法提供准确答案”。
- 学术资源生成需标注参考来源，禁止输出无根据的虚假引用。

### 5.2 响应时间要求
- 简单对话回答：首字延迟 < 2秒，全程流式输出。
- 资源生成任务：3秒内必须返回 `taskId` 和初始 `progress`，随后每隔5秒推送进度更新。
- 复杂多模态资源（视频/动画）：整体生成不超过3分钟，需提供“生成进度追踪” UI。

### 5.3 多模态内容格式
- Markdown 文本：遵循 CommonMark 规范，支持数学公式（LaTeX）。
- 图片：提供 HTTPS URL，支持 JPEG/PNG/GIF。
- PPT/PDF：提供下载 URL 及在线预览链接。
- 视频/动画：提供 mp4/webm URL，可选缩略图。

### 5.4 画像维度底线
初始画像和每次更新至少包含6个维度：知识基础、认知风格、学习节奏、易错点偏好、兴趣领域、目标难度等级。系统内部使用统一的画像Schema（JSON），所有智能体共享此定义。

### 5.5 工具与开源标注
使用讯飞星火大模型等科大讯飞AI工具作为核心模型，若引入其他开源项目（如LangChain、Dify等），须在代码和文档显著位置标注来源与协议。

---

## 6. 命名统一约定

- **API路径**：小写字母 + 连字符，资源名用复数（`/sessions`, `/resource-tasks`）
- **JSON字段**：camelCase（`sessionId`, `resourceType`, `learningPath`）
- **枚举值**：小写下划线（`profile_build`, `resource_generate`, `in_progress`）
- **智能体内部服务名**：`agent-profile`, `agent-resource-gen`, `agent-path-planner`, `agent-tutor`, `agent-evaluator`
- **Git分支**：`feature/agent-profile`, `feature/frontend-chat` 等（见下一章）

---

## 7. 协作开发与GitHub集成规范

### 7.1 代码仓库结构（Monorepo）
```
/
├── frontend/                # 前端应用（React/Vue/小程序）
├── gateway/                 # API网关（路由、鉴权、WS管理）
├── agents/
│   ├── profile/             # 画像智能体
│   ├── resource-gen/        # 资源生成编排器+子智能体
│   ├── path-planner/        # 路径规划智能体
│   ├── tutor/               # 智能辅导智能体
│   └── evaluator/           # 评估智能体
├── common/                  # 共享库（DTO定义、工具类、画像Schema）
├── docs/                    # 接口文档（本规范）、架构图
├── scripts/                 # 本地启动、构建脚本
└── .github/
    ├── workflows/           # CI/CD（lint、test）
    └── PULL_REQUEST_TEMPLATE.md
```

### 7.2 分支策略
- `main`：稳定可演示版本，严格保护
- `develop`：集成开发分支，各功能分支合并至此
- `feature/<模块名>`：新功能开发，如 `feature/agent-resource-gen`
- `fix/<问题描述>`：Bug修复
- `docs/<内容>`：文档更新

### 7.3 开发流程与合并规则
1. **认领任务**：团队成员从赛题功能清单中认领模块，创建对应 `feature` 分支。
2. **本地开发**：严格遵循本文档接口定义，使用 `common` 中的 DTO 进行序列化/反序列化；自行编写单元测试。
3. **接口联调**：启动本地全部服务或使用 Mock Server，验证与网关的交互。网关提供统一的 Mock 模式。
4. **提交PR**：完成后向 `develop` 发起 Pull Request，标题格式 `[Feature] 添加资源生成智能体`。PR必须通过：
   - 自动化接口契约测试（对比 API 文档）
   - 至少1名队员 Code Review
5. **合并与集成**：评审通过后压缩合并至 `develop`，CI自动构建并部署到测试环境。所有模块集成后，由队长合并 `develop` 到 `main` 并打 tag 发布。

### 7.4 冲突解决
- 多人修改同一配置文件（如网关路由表）需及时沟通，优先合并最先通过的 PR，后者手动解决冲突。
- `common` 库变更需单独 PR 并通知全员，避免大面积冲突。
- 接口定义升级时，必须同时更新 `docs/` 中的规范文档，确保代码与文档一致。

### 7.5 代码规范与工具
- 统一使用 ESLint + Prettier（前端），Pylint/Black（Python后端），或各语言社区主流规范。
- Commit 信息遵循 [Conventional Commits](https://www.conventionalcommits.org/)，如 `feat(profile): 添加对话画像更新逻辑`。
- 使用科大讯飞 AI Coding 工具（如 iFlyCode）辅助开发时，必须在提交信息中注明“辅助工具：iFlyCode”，并在文档中说明应用场景。

通过以上规范，六名开发者可同时开工：前端1人、网关1人、画像1人、资源生成1人、路径+辅导1人、评估1人（示例）。最终只需按要求提交结构化仓库、文档和演示视频，充分体现多智能体协同与工程化能力。