# 🌐 API 网关服务 (Gateway)

本模块作为整个个性化学习智能体系统的入口网关，负责请求分发、身份认证、API限流以及 WebSocket 双向通信代理。

## 🛠️ 技术栈
- **语言/运行时**: TypeScript / Node.js
- **Web 框架**: Express
- **WebSocket 库**: `ws` / `http`

## 📦 核心功能

1. **统一路由代理 (Proxy)**:
   - 自动将前端的 REST API 请求代理分发至对应的后端微服务（如资源生成 `resource-gen`、路径规划 `path-planner` 等）。
2. **身份认证 (JWT Auth)**:
   - 在 WebSocket 握手或特定的 REST API 调用时，校验请求携带的 JWT 令牌，保障通信安全。
3. **API 限流 (Rate Limiting)**:
   - 增加基于 IP 的滑动窗口速率限制（`rateLimiterMiddleware`），默认限制单 IP 每分钟最多 100 次请求，超出时返回 `429 Too Many Requests`。
4. **WebSocket 意图代理 (Intent Proxy)**:
   - 前端与网关建立一条单一的 WebSocket 连接。
   - 网关根据客户端发来的消息意图 (`intent`)，动态将流量转发给不同的智能体微服务：
     - `profile_build` / `profile_update` ➡️ 转发给 **用户画像智能体 (Profile Agent)**，并在 URL 附加 `session_id`。
     - `tutoring` ➡️ 转发给 **答疑辅导智能体 (Tutor Agent)**。
5. **内部消息推送 (Internal Push)**:
   - 提供 `POST /api/v1/internal/sessions/:sessionId/push` 接口，允许后端异步微服务（如资源生成）将任务进度主动推送到对应的用户 WebSocket 客户端。

## 🚀 本地开发与运行

### 1. 安装依赖
```bash
npm install
```

### 2. 配置文件
网关会读取根目录下的 `.env` 文件。确保以下变量配置正确：
```env
PORT=3000                                 # 网关端口
JWT_SECRET=ai-learning-system-secret      # JWT 密钥
MOCK_MODE=true                            # 是否开启 Mock 模式 (本地开发调试推荐)
PROFILE_SERVICE_URL=ws://localhost:8081    # 用户画像智能体 WS 地址
TUTOR_SERVICE_URL=ws://localhost:8082      # 答疑辅导智能体 WS 地址
```

### 3. 启动服务
```bash
# 启动开发服务器（支持热重载）
npm run dev

# 编译项目
npm run build

# 运行生产版本
npm start
```
