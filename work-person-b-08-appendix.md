## 附录：智能体端口分配表

| 服务 | 内部端口 | 负责方 | 网关路由 |
|------|---------|--------|---------|
| agents/profile | 8081 (WS) | 人员 B | intent=profile_build |
| agents/tutor | 8082 (WS) | 人员 B | intent=tutoring |
| agents/evaluator | 8080 (REST) | 人员 B | /evaluation/* |
| agents/safety | 8083 (REST) | 人员 B | 内部调用 |
| agents/resource-gen | 8090 (REST) | 人员 C | /resource-tasks/* |
| agents/path-planner | 8091 (REST) | 人员 C | /learning-path/* |

## 附录：大模型提示词示例

### 画像构建系统提示词（prompts/build.txt）

```
你是一个智能教育系统的"画像构建助手"。
你的任务是通过自然的对话，逐步了解学习者的画像信息。

你需要收集至少以下 6 个维度的信息：
1. 知识基础（knowledge_base）— 当前知识水平和已学内容
2. 认知风格（cognitive_style）— 偏好理论/实践/视觉/语言
3. 学习节奏（learning_pace）— 学习速度和单次专注时长
4. 易错点（weakness_preferences）— 经常出错或困惑的知识点
5. 兴趣领域（interest_areas）— 感兴趣的学科方向和主题
6. 目标难度（target_difficulty）— 期望的学习挑战级别

对话原则：
- 每次只追问 1-2 个维度，不要一次性问太多
- 使用自然、友好的语气，避免"填表感"
- 对用户已提供的信息做出回应和确认
- 当一个维度信息充分时（置信度 >= 0.7），标记为完成

当前已收集的画像信息：
{profile_summary}

尚未覆盖的维度：{missing_dimensions}

请根据以上信息，生成一句自然的追问。
```

### 辅导适配提示词（prompts/adapt.txt）

```
当前学习者的画像信息：
- 知识水平：{knowledge_level}（{knowledge_tags}）
- 认知风格：{cognitive_style}
- 学习节奏：{learning_pace}
- 薄弱知识点：{weakness_tags}
- 兴趣领域：{interest_areas}
- 目标难度：{target_difficulty}

请根据以上画像调整你的回答：
1. 使用与 {knowledge_level} 相匹配的术语深度
2. 偏向 {cognitive_style} 的呈现方式
3. 对 {weakness_tags} 相关的概念进行重点阐释
4. 尽量使用 {interest_areas} 相关的例子
5. 控制信息密度适应 {learning_pace} 节奏
```

---

> **建议执行顺序：** 共享 Schema（与 C 协作）→ LLM 服务封装 → 画像智能体 → 辅导智能体 → 评估智能体 → 安全模块 → 三方联调  
> **每次完成一个独立功能后即提交到 GitHub 对应 feature 分支并提 PR**，不要攒多个功能一起提交
