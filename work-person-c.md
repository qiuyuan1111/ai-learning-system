# 人员 C 工作手册：资源生成 + 路径规划 + 公共库

> **负责模块：** `agents/resource-gen/`（资源生成编排器）+ `agents/path-planner/`（路径规划智能体）+ `common/`（共享库）+ `docs/`（文档）+ `scripts/`（脚本）+ `.github/`（CI/CD）  
> **工作目标：** 实现资源生成管线、学习路径规划、公共基础设施，为 A、B 提供开发基础  
> **主要协作对象：** 人员 A（REST API 对接）、人员 B（画像 Schema 协作、安全模块协作）

---

## 目录

1. [技术栈选型](#1-技术栈选型)
2. [工作任务总览](#2-工作任务总览)
3. [任务详解：公共共享库](#3-任务详解公共共享库)
4. [任务详解：资源生成编排器](#4-任务详解资源生成编排器)
5. [任务详解：路径规划智能体](#5-任务详解路径规划智能体)
6. [任务详解：工程化与文档](#6-任务详解工程化与文档)
7. [核心数据模型（DTO）](#7-核心数据模型dto)
8. [开发步骤与 Git 提交计划](#8-开发步骤与-git-提交计划)

---

## 1. 技术栈选型

| 模块 | 推荐技术 | 备选方案 |
|------|---------|---------|
| **公共库语言** | TypeScript（npm 包）或 Python（pip 包） | 双语言同时维护 |
| **资源生成后端** | Python 3.11 + FastAPI | Node.js |
| **路径规划后端** | Python 3.11 + FastAPI | — |
| **大模型 SDK** | OpenAI API（`openai`） | Anthropic API |
| **文档渲染** | python-pptx（PPT）、reportlab（PDF）、markdown | — |
| **向量数据库** | ChromaDB | FAISS |
| **CI/CD** | GitHub Actions | — |
| **代码规范** | ESLint + Prettier（TS）、Pylint + Black（Python） | — |

> **核心决策：** `common/` 推荐采用 **TypeScript** 编写，因为前端是 TypeScript，后端的 Node.js 服务也直接可用。如果 B 使用 Python，则需要将 `common/` 的核心 DTO 同步为 Python 版本（Pydantic）。

---

## 2. 工作任务总览

### 2.1 公共共享库 common/

| 编号 | 任务 | 优先级 | 说明 |
|------|------|--------|------|
| C-CM-01 | 通用响应体 DTO 定义 | P0 | ApiResponse、PageInfo |
| C-CM-02 | 会话 DTO 定义 | P0 | SessionDTO |
| C-CM-03 | 画像 Schema 定义 | P0 | 与 B 协作完成 |
| C-CM-04 | 资源 DTO 定义 | P0 | ResourceDTO、TaskDTO |
| C-CM-05 | 学习路径 DTO 定义 | P0 | PathDTO |
| C-CM-06 | 评估 DTO 定义 | P0 | EvaluationDTO |
| C-CM-07 | 枚举定义 | P0 | Intent、ResourceType、TaskStatus、ErrorCode |
| C-CM-08 | 工具函数 | P0 | ID 生成器、JSON 工具 |
| C-CM-09 | 发布为 npm/pip 包 | P1 | 供 A、B 安装使用 |

### 2.2 资源生成编排器 agents/resource-gen/

| 编号 | 任务 | 优先级 | 说明 |
|------|------|--------|------|
| C-RG-01 | 编排器框架搭建 | P0 | 管线调度核心 |
| C-RG-02 | 子智能体：大纲生成 | P0 | 生成资源大纲 |
| C-RG-03 | 子智能体：内容撰写 | P0 | 按大纲写详细内容 |
| C-RG-04 | 子智能体：PPT 渲染 | P0 | python-pptx 渲染 |
| C-RG-05 | 子智能体：文档/思维导图渲染 | P1 | PDF/Markdown/mindmap |
| C-RG-06 | 异步任务管理 | P0 | 任务状态 + 进度查询 |
| C-RG-07 | REST API：任务查询 | P0 | GET /resource-tasks/{taskId} |
| C-RG-08 | REST API：资源列表 | P0 | GET /sessions/{sessionId}/resources |
| C-RG-09 | 进度推送（WS） | P0 | 生成进度通过 WS 通知网关 |
| C-RG-10 | 审核集成 | P0 | 调用安全模块审核内容 |

### 2.3 路径规划智能体 agents/path-planner/

| 编号 | 任务 | 优先级 | 说明 |
|------|------|--------|------|
| C-PP-01 | 路径生成引擎 | P0 | 基于画像生成路径树 |
| C-PP-02 | 路径动态调整 | P0 | 根据评估结果调整路径 |
| C-PP-03 | REST API：路径查询 | P0 | GET /sessions/{sessionId}/learning-path |
| C-PP-04 | REST API：推荐触发 | P1 | POST /sessions/{sessionId}/recommend |
| C-PP-05 | WS 路径推送 | P0 | 路径更新后推送资源卡片 |
| C-PP-06 | 节点资源绑定 | P0 | 将已生成资源绑定到路径节点 |

### 2.4 工程化与文档

| 编号 | 任务 | 优先级 | 说明 |
|------|------|--------|------|
| C-EN-01 | CI/CD 配置 | P0 | GitHub Actions lint + test |
| C-EN-02 | PR 模板 | P0 | PULL_REQUEST_TEMPLATE.md |
| C-EN-03 | 本地启动脚本 | P0 | 一键启动所有服务 |
| C-EN-04 | 接口规范文档 | P0 | 维护 api.md 同步 |
| C-EN-05 | Docker 配置 | P1 | Docker Compose 多服务编排 |

---

## 3. 任务详解：公共共享库

### 3.1 项目结构（TypeScript 版本）

```
common/
├── src/
│   ├── index.ts                    # 统一导出
│   ├── dto/
│   │   ├── ApiResponse.ts          # 通用响应体
│   │   ├── PageInfo.ts             # 分页信息
│   │   ├── SessionDTO.ts           # 会话 DTO
│   │   ├── ProfileDTO.ts           # 画像 DTO
│   │   ├── ResourceDTO.ts          # 资源 DTO
│   │   ├── TaskDTO.ts              # 任务 DTO
│   │   ├── PathDTO.ts              # 路径 DTO
│   │   └── EvaluationDTO.ts        # 评估 DTO
│   ├── enums/
│   │   ├── IntentEnum.ts           # 意图枚举
│   │   ├── ResourceTypeEnum.ts     # 资源类型枚举
│   │   ├── TaskStatusEnum.ts       # 任务状态枚举
│   │   ├── PathNodeStatusEnum.ts   # 路径节点状态枚举
│   │   └── ErrorCodeEnum.ts        # 错误码枚举
│   └── utils/
│       ├── IdGenerator.ts          # ID 生成器
│       └── JsonUtils.ts            # JSON 工具
├── package.json                    # name: @ai-edu/common
├── tsconfig.json
└── README.md
```

### 3.2 DTO 详解

#### 3.2.1 通用响应体 — `ApiResponse.ts`

```typescript
/**
 * 通用 API 响应体
 *
 * 所有非流式 REST 接口统一使用此结构返回。
 *
 * @template T - data 字段的具体数据类型
 *
 * 示例:
 *   { code: 0, message: "success", data: { sessionId: "..." }, requestId: "uuid" }
 *   { code: 3001, message: "内容违规已拦截", data: null, requestId: "uuid" }
 */
export interface ApiResponse<T = unknown> {
  /** 业务状态码，0 表示成功，非 0 表示异常 */
  code: number
  /** 提示信息 */
  message: string
  /** 具体返回数据，可为对象、数组或 null */
  data: T | null
  /** 请求追踪 ID，用于链路追踪和日志排查 */
  requestId: string
}

/**
 * 分页信息
 */
export interface PageInfo {
  /** 当前页码，从 1 开始 */
  page: number
  /** 每页记录数 */
  pageSize: number
  /** 总记录数 */
  total: number
  /** 总页数 */
  totalPages: number
}

/**
 * 分页响应数据包装
 */
export interface PaginatedData<T> {
  list: T[]
  pageInfo: PageInfo
}

/**
 * 快捷构造成功响应
 */
export function success<T>(data: T, requestId?: string): ApiResponse<T>

/**
 * 快捷构造错误响应
 */
export function error(code: number, message: string, requestId?: string): ApiResponse<null>
```

#### 3.2.2 会话 DTO — `SessionDTO.ts`

```typescript
/**
 * 创建会话请求
 */
export interface CreateSessionRequest {
  /** 用户昵称 */
  nickname: string
  /** 专业 */
  major: string
  /** 年级，如 "本科三年级" */
  grade: string
}

/**
 * 创建会话响应
 */
export interface CreateSessionResponse {
  /** 会话 ID，格式 sess_xxx */
  sessionId: string
  /** JWT Token */
  token: string
  /** 初始画像（维度可能不全） */
  profile: Record<string, unknown>
}
```

#### 3.2.3 画像 DTO — `ProfileDTO.ts`

```typescript
/**
 * 用户画像 — 6 个维度
 *
 * 所有智能体共享此画像定义。
 * 画像在对话过程中逐步构建，初始可能部分维度为 null。
 */
export interface UserProfile {
  /** 会话 ID */
  sessionId: string
  /** 各维度信息 */
  dimensions: ProfileDimensions
  /** 最近更新时间 */
  updatedAt: string  // ISO8601
  /** 版本号，每次更新递增 */
  version: number
}

export interface ProfileDimensions {
  /** 知识基础 */
  knowledgeBase?: {
    /** 水平: beginner | intermediate | advanced */
    level: string
    /** 已掌握的知识标签，如 ["机器学习", "Python"] */
    tags: string[]
    /** 置信度 0-1 */
    confidence: number
  }
  /** 认知风格: theoretical | practical | visual | verbal */
  cognitiveStyle?: {
    style: string
    detail?: string
    confidence: number
  }
  /** 学习节奏: slow | moderate | fast */
  learningPace?: {
    pace: string
    /** 单次专注时长（分钟） */
    preferredSessionMinutes?: number
    confidence: number
  }
  /** 易错点列表 */
  weaknessPreferences?: Array<{
    /** 薄弱知识点标签 */
    weakTags: string[]
    description?: string
    confidence: number
  }>
  /** 兴趣领域列表 */
  interestAreas?: Array<{
    areas: string[]
    /** 兴趣深度 1-5 */
    depth: number
    confidence: number
  }>
  /** 目标难度 1-10 */
  targetDifficulty?: {
    level: number
    description?: string
    confidence: number
  }
}
```

#### 3.2.4 资源 DTO — `ResourceDTO.ts`

```typescript
/**
 * 资源对象
 */
export interface Resource {
  resourceId: string
  type: ResourceType
  title: string
  url: string
  thumbnailUrl?: string
  description?: string
  metadata?: Record<string, unknown>
  createdAt: string  // ISO8601
}

/**
 * REST API: 获取资源列表请求参数
 */
export interface GetResourcesParams {
  /** 筛选资源类型，不传则查全部 */
  type?: ResourceType
  page: number
  pageSize: number
}

/**
 * REST API: 获取资源列表响应
 * 外层包 ApiResponse<PaginatedData<Resource>>
 */
```

#### 3.2.5 任务 DTO — `TaskDTO.ts`

```typescript
/**
 * 异步任务定义
 *
 * 资源生成等耗时操作采用异步任务模式，
 * 客户端轮询 GET /resource-tasks/{taskId} 获取最新状态。
 */
export interface TaskInfo {
  taskId: string
  status: TaskStatus
  /** 进度百分比 0-100 */
  progress: number
  /** 进度描述文字 */
  progressDescription?: string
  /** 任务完成后返回的资源列表 */
  result?: {
    resources: Resource[]
  }
  /** 任务失败时的错误信息 */
  error?: {
    code: number
    message: string
  }
  createdAt: string
  updatedAt: string
}

/**
 * WS 推送的任务进度消息 content 部分
 */
export interface TaskProgressContent {
  taskId: string
  progress: number
  description: string
}
```

#### 3.2.6 路径 DTO — `PathDTO.ts`

```typescript
/**
 * 学习路径节点
 */
export interface PathNode {
  nodeId: string
  /** 排序序号，从 1 开始 */
  order: number
  title: string
  description?: string
  /** 绑定的学习资源 */
  resource?: {
    resourceId: string
    type: ResourceType
    url: string
  }
  /** 完成状态 */
  status: PathNodeStatus
}

/**
 * 学习路径完整响应
 */
export interface LearningPathResponse {
  pathId: string
  updatedAt: string
  nodes: PathNode[]
}
```

#### 3.2.7 评估 DTO — `EvaluationDTO.ts`

```typescript
/**
 * 评估提交请求
 */
export interface SubmitEvaluationRequest {
  sessionId: string
  quizId: string
  answers: AnswerItem[]
  behaviors: BehaviorItem[]
}

export interface AnswerItem {
  questionId: string
  answer: string
  timeSpent: number  // 秒
}

export interface BehaviorItem {
  action: string  // video_pause | video_forward | video_rewind | resource_view
  resourceId: string
  timestamp: string
}

/**
 * 评估报告
 */
export interface EvaluationReport {
  dimensions: EvaluationDimension[]
  weakPoints: WeakPoint[]
  suggestions: string[]
}

export interface EvaluationDimension {
  name: string
  score: number
  maxScore: number
}

export interface WeakPoint {
  topic: string
  severity: number  // 1-5
  description: string
  suggestion?: string
}
```

### 3.3 枚举定义

```typescript
// enums/IntentEnum.ts
export const IntentEnum = {
  PROFILE_BUILD: 'profile_build',
  RESOURCE_GENERATE: 'resource_generate',
  TUTORING: 'tutoring',
  PATH_QUERY: 'path_query',
  EVALUATE: 'evaluate',
} as const
export type Intent = typeof IntentEnum[keyof typeof IntentEnum]

// enums/ResourceTypeEnum.ts
export const ResourceTypeEnum = {
  PPT: 'ppt',
  PDF: 'pdf',
  DOC: 'doc',
  MINDMAP: 'mindmap',
  VIDEO: 'video',
} as const
export type ResourceType = typeof ResourceTypeEnum[keyof typeof ResourceTypeEnum]

// enums/TaskStatusEnum.ts
export const TaskStatusEnum = {
  PENDING: 'pending',
  PROCESSING: 'processing',
  COMPLETED: 'completed',
  FAILED: 'failed',
} as const
export type TaskStatus = typeof TaskStatusEnum[keyof typeof TaskStatusEnum]

// enums/PathNodeStatusEnum.ts
export const PathNodeStatusEnum = {
  PENDING: 'pending',
  IN_PROGRESS: 'in_progress',
  COMPLETED: 'completed',
} as const
export type PathNodeStatus = typeof PathNodeStatusEnum[keyof typeof PathNodeStatusEnum]

// enums/ErrorCodeEnum.ts
export const ErrorCodeEnum = {
  SUCCESS: 0,
  PARAM_ERROR: 1001,
  SESSION_NOT_FOUND: 1002,
  TASK_NOT_FOUND: 2001,
  RESOURCE_GEN_FAILED: 2002,
  CONTENT_SAFETY_VIOLATION: 3001,
  HALLUCINATION_DETECTED: 3002,
  AGENT_TIMEOUT: 4001,
  UNKNOWN_ERROR: 5000,
} as const
```

### 3.4 工具函数

```typescript
// utils/IdGenerator.ts
/**
 * ID 生成器
 *
 * 生成格式化的唯一 ID:
 * - 会话 ID: sess_ + 16位随机字符串
 * - 资源 ID: res_ + 16位随机字符串
 * - 任务 ID: task_ + 16位随机字符串
 * - 路径 ID: path_ + 16位随机字符串
 * - requestId: uuid v4
 *
 * 工具: nanoid 或 crypto.randomUUID
 */
export class IdGenerator {
  static sessionId(): string
  static resourceId(): string
  static taskId(): string
  static pathId(): string
  static requestId(): string
}
```

---

## 4. 任务详解：资源生成编排器

### 4.1 项目结构

```
agents/resource-gen/
├── src/
│   ├── main.py                     # FastAPI 入口
│   ├── config.py                   # 配置
│   ├── models/
│   │   └── dto.py                  # 请求/响应 DTO
│   ├── orchestrator/
│   │   ├── pipeline.py             # 编排管线核心
│   │   ├── outline_generator.py    # ① 大纲生成智能体
│   │   ├── content_writer.py       # ② 内容撰写智能体
│   │   ├── ppt_renderer.py         # ③ PPT 渲染智能体
│   │   ├── doc_renderer.py         # ④ 文档/思维导图渲染
│   │   └── review_checker.py       # ⑤ 审核集成
│   ├── task/
│   │   ├── manager.py              # 异步任务管理器
│   │   └── store.py                # 任务状态存储
│   ├── services/
│   │   └── llm_service.py          # 大模型调用
│   ├── db/
│   │   └── repository.py           # 资源存储
│   └── ws/
│       └── notifier.py             # WS 进度通知
├── tests/
│   ├── test_pipeline.py
│   ├── test_outline_generator.py
│   └── test_ppt_renderer.py
├── requirements.txt
└── Dockerfile
```

### 4.2 编排管线核心

```python
# orchestrator/pipeline.py

class ResourceGenerationPipeline:
    """
    资源生成编排管线
    
    管线流程（5 个阶段，串行执行）:
    
    ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
    │ ① 大纲    │→  │ ② 内容    │→  │ ③ PPT    │→  │ ④ 渲染    │→  │ ⑤ 审核    │
    │ 生成智能体  │   │ 撰写智能体  │   │ 编排      │   │ 输出      │   │ 安全检查   │
    └──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘
         │              │              │              │              │
         ▼              ▼              ▼              ▼              ▼
      progress=20    progress=40    progress=60    progress=80    progress=95
      
    每完成一个阶段:
    1. 更新 task 状态 + progress
    2. 通过 WS 通知网关推送进度给前端
    
    每个阶段产出物:
    ① → Outline（章节结构 JSON）
    ② → Content（各章节 Markdown 内容）
    ③ → PPT 原始数据（slide 列表）
    ④ → PPT/PDF 文件（文件存储 URL）
    ⑤ → 审核通过的最终资源（Resource 对象）
    """

    def __init__(self, task_manager, ws_notifier, llm_service):
        self.task_manager = task_manager
        self.notifier = ws_notifier
        self.llm = llm_service

    async def execute(
        self,
        task_id: str,
        session_id: str,
        user_request: str,
        profile: dict
    ) -> Resource:
        """
        执行完整资源生成管线
        
        参数:
            task_id: 任务 ID
            session_id: 会话 ID
            user_request: 用户需求描述（如 "生成BERT模型的讲解PPT"）
            profile: 用户画像（用于调整内容和难度）
        
        返回: 最终生成并审核通过的 Resource 对象
        
        异常:
            ResourceGenException: 任意阶段失败时抛出
        """
        # 阶段 ①: 生成大纲
        await self._update_progress(task_id, 10, "正在生成大纲...")
        outline = await self._generate_outline(user_request, profile)
        
        # 阶段 ②: 撰写内容
        await self._update_progress(task_id, 30, "正在撰写内容...")
        content = await self._write_content(outline, profile)
        
        # 阶段 ③: PPT 编排
        await self._update_progress(task_id, 55, "正在编排幻灯片...")
        slides_data = await self._arrange_slides(content)
        
        # 阶段 ④: 渲染输出
        await self._update_progress(task_id, 75, "正在渲染文档...")
        file_url = await self._render_ppt(slides_data)
        
        # 阶段 ⑤: 审核
        await self._update_progress(task_id, 90, "正在进行安全审核...")
        resource = await self._review_and_finalize(
            task_id, file_url, outline, content
        )
        
        return resource

    async def _update_progress(self, task_id: str, progress: int, description: str):
        """更新任务进度并通知"""
        await self.task_manager.update_progress(task_id, progress, description)
        await self.notifier.notify_progress(task_id, progress, description)
```

### 4.3 子智能体详解

#### 4.3.1 大纲生成智能体

```python
# orchestrator/outline_generator.py

class OutlineGenerator:
    """
    大纲生成智能体
    
    输入: 用户需求描述 + 用户画像
    输出: Outline 结构（JSON）
    
    示例输出:
    {
        "title": "BERT模型原理与实战",
        "sections": [
            { "order": 1, "title": "Transformer回顾", "subsections": [
                { "order": 1.1, "title": "Self-Attention机制", "duration_minutes": 10 },
                { "order": 1.2, "title": "Multi-Head Attention", "duration_minutes": 8 }
            ]},
            { "order": 2, "title": "BERT模型架构", "subsections": [...] },
            { "order": 3, "title": "BERT vs CNN对比", "subsections": [...] }
        ]
    }
    
    策略:
    - 根据用户画像调整章节深度和侧重点
    - 如果画像中有 weakPoints 相关主题，增加对应章节
    - 如果画像中有 interestAreas，增加相关案例章节
    """

    async def generate(
        self,
        user_request: str,
        profile: dict
    ) -> Outline:
        """
        调用大模型生成大纲
        
        提示词模板（prompts/outline.txt）:
        你是一个教学大纲设计专家。
        用户需求: {user_request}
        用户画像: {profile}
        请生成一个结构化的学习大纲，要求...
        """
        pass
```

#### 4.3.2 内容撰写智能体

```python
# orchestrator/content_writer.py

class ContentWriter:
    """
    内容撰写智能体
    
    输入: Outline 结构
    输出: 各章节的 Markdown 内容
    
    逐章节调用大模型生成内容，控制每节长度。
    支持并行生成多个不依赖的章节，提高效率。
    """

    async def write_all(self, outline: Outline, profile: dict) -> Dict[str, str]:
        """
        按大纲生成所有章节内容
        
        返回: { "section_key": "markdown content", ... }
        
        对每个章节:
        1. 构建该章节的提示词（包含章节标题、上下文衔接）
        2. 调用 llm.chat() 生成内容
        3. 检查内容长度和质量
        
        注意: 独立章节可以并发生成，使用 asyncio.gather()
        """
        tasks = []
        for section in outline.sections:
            tasks.append(self._write_section(section, outline.title, profile))
        
        results = await asyncio.gather(*tasks)
        return dict(zip([s.title for s in outline.sections], results))

    async def _write_section(
        self,
        section: Section,
        doc_title: str,
        profile: dict
    ) -> str:
        """生成单个章节的内容"""
        pass
```

#### 4.3.3 PPT 渲染智能体

```python
# orchestrator/ppt_renderer.py

class PptRenderer:
    """
    PPT 渲染智能体
    
    将撰写好的内容渲染为 PowerPoint 文件。
    
    工具: python-pptx 库
    安装: pip install python-pptx
    
    渲染策略:
    1. 每章一个大标题 slide
    2. 每小节 1-2 个内容 slide
    3. 支持模板：封面、目录、内容、对比、总结等 slide 类型
    4. 自动应用配色方案和字体
    5. 支持公式渲染（插入 LaTeX 图片或文本）
    6. 代码块使用等宽字体渲染
    """

    SLIDE_LAYOUTS = {
        "cover": 0,        # 封面
        "section": 1,      # 章节标题
        "content": 2,      # 内容（标题+正文）
        "comparison": 3,   # 对比（左右分栏）
        "code": 4,         # 代码展示
        "summary": 5,      # 总结
    }

    async def render(
        self,
        title: str,
        sections: List[SectionContent],
        output_dir: str
    ) -> str:
        """
        渲染 PPT 文件
        
        步骤:
        1. 创建 Presentation 对象
        2. 选择/加载模板
        3. 按 sections 逐个添加 slide
        4. 对每个 slide:
           a. 选择 layout
           b. 填充标题
           c. 填充正文/代码/图片
        5. 保存文件
        
        返回: PPT 文件的 URL 或本地路径
        
        性能要求:
        - 10 页以内的 PPT 生成时间 < 30 秒
        - 30 页以内 < 60 秒
        """
        from pptx import Presentation
        
        prs = Presentation()
        
        # 封面 slide
        cover_slide = prs.slides.add_slide(prs.slide_layouts[0])
        cover_slide.shapes.title.text = title
        
        # 内容 slides
        for section in sections:
            slide = prs.slides.add_slide(prs.slide_layouts[1])
            # 填充内容...（使用 python-pptx API）
        
        file_path = f"{output_dir}/{title}.pptx"
        prs.save(file_path)
        return file_path


class DocRenderer:
    """
    文档/思维导图渲染
    
    支持格式:
    - Markdown: 直接输出 .md 文件
    - PDF: 使用 reportlab 或 weasyprint 渲染
    - 思维导图: 生成 .mm (FreeMind) 格式或使用 Markmap
    
    工具:
    - reportlab: pip install reportlab
    - markmap: npm install markmap-lib
    """

    async def render_markdown(self, content: str, title: str) -> str:
        """直接保存为 .md 文件"""
        pass

    async def render_pdf(self, markdown_content: str, title: str) -> str:
        """Markdown → PDF"""
        pass

    async def render_mindmap(self, outline: Outline) -> str:
        """
        生成思维导图
        
        使用 Markmap 将 Markdown 标题层级转换为交互式思维导图 HTML。
        工具: markmap-lib (npm) 或 markmap Python 包
        """
        pass
```

#### 4.3.4 审核集成

```python
# orchestrator/review_checker.py

class ReviewChecker:
    """
    审核集成
    
    在资源生成完成后，调用内容安全模块进行最终审核。
    
    审核项:
    1. 内容安全 — 调用 B 的安全过滤器
    2. 防幻觉 — 调用 B 的防幻觉校验
    3. 格式检查 — PPT/PDF 文件完整性
    4. 来源标注 — 检查是否标注参考来源
    
    审核不通过:
    - code=3001: 内容违规 → 返回友好提示，任务标记失败
    - code=3002: 幻觉风险 → 返回友好提示，任务标记失败
    """

    async def review(self, resource_data: dict) -> ReviewResult:
        """
        执行最终审核
        
        返回:
            ReviewResult:
                - passed: bool
                - code: int (0 通过，3001/3002 不通过)
                - message: str
                - resource: Resource (仅 passed=True 时有值)
        """
        # 调用安全过滤器
        safety_result = await self._call_safety_filter(resource_data["content_text"])
        if not safety_result.passed:
            return ReviewResult(passed=False, code=3001, message="内容存在违规信息")
        
        # 调用防幻觉校验
        hallucination_result = await self._call_hallucination_guard(resource_data)
        if not hallucination_result.passed:
            return ReviewResult(passed=False, code=3002, message="存在疑似虚假引用")
        
        # 审核通过，构造 Resource
        resource = Resource(
            resourceId=IdGenerator.resource_id(),
            type=resource_data["type"],
            title=resource_data["title"],
            url=resource_data["file_url"],
            createdAt=datetime.utcnow().isoformat()
        )
        return ReviewResult(passed=True, code=0, message="success", resource=resource)
```


### 4.4 请求/响应 DTO（models/dto.py）

```python
from pydantic import BaseModel, Field
from typing import Optional


class GenerationRequest(BaseModel):
    """资源生成请求体"""
    text: str = Field(..., description="用户需求描述，如「生成BERT模型的讲解PPT」")
    resourceType: Optional[str] = Field(default="ppt", description="目标资源类型: ppt | pdf | doc | mindmap")
    profile: Optional[dict] = Field(default=None, description="用户画像（可选），用于定制内容难度和风格")


class ResourceQueryParams(BaseModel):
    """资源列表查询参数"""
    type: Optional[str] = Field(default=None, description="按资源类型筛选")
    page: int = Field(default=1, ge=1, description="页码")
    pageSize: int = Field(default=20, ge=1, le=100, description="每页条数")
```

### 4.5 异步任务管理

```python
# task/manager.py

class TaskManager:
    """
    异步任务管理器
    
    职责:
    - 创建新任务（pending 状态）
    - 更新任务进度
    - 完成任务（completed 状态）
    - 标记失败（failed 状态）
    - 提供查询接口
    
    存储: 内存 dict（开发阶段）→ Redis（生产阶段）
    """

    def __init__(self):
        self._tasks: Dict[str, TaskInfo] = {}

    async def create_task(self, session_id: str, request: str) -> TaskInfo:
        """
        创建新任务
        
        步骤:
        1. 生成 taskId
        2. 初始化 TaskInfo（status=pending, progress=0）
        3. 存入 _tasks
        4. 启动后台管线执行 (asyncio.create_task)
        """
        task_id = f"task_{uuid4().hex[:12]}"
        task = TaskInfo(
            taskId=task_id,
            status="pending",
            progress=0,
            createdAt=datetime.utcnow().isoformat(),
            updatedAt=datetime.utcnow().isoformat()
        )
        self._tasks[task_id] = task
        
        # 启动后台任务
        asyncio.create_task(self._run_pipeline(task_id, session_id, request))
        
        return task

    async def get_task(self, task_id: str) -> Optional[TaskInfo]:
        """查询任务状态"""
        return self._tasks.get(task_id)

    async def update_progress(self, task_id: str, progress: int, description: str):
        """更新任务进度"""
        task = self._tasks[task_id]
        task.progress = progress
        task.progressDescription = description
        task.updatedAt = datetime.utcnow().isoformat()

    async def complete_task(self, task_id: str, resources: List[Resource]):
        """完成任务"""
        task = self._tasks[task_id]
        task.status = "completed"
        task.progress = 100
        task.result = {"resources": resources}
        task.updatedAt = datetime.utcnow().isoformat()

    async def fail_task(self, task_id: str, code: int, message: str):
        """标记任务失败"""
        task = self._tasks[task_id]
        task.status = "failed"
        task.error = {"code": code, "message": message}
        task.updatedAt = datetime.utcnow().isoformat()

    async def _run_pipeline(self, task_id: str, session_id: str, request: str):
        """在后台执行完整管线"""
        try:
            pipeline = ResourceGenerationPipeline(self, ...)
            resource = await pipeline.execute(task_id, session_id, request, profile)
            await self.complete_task(task_id, [resource])
        except Exception as e:
            await self.fail_task(task_id, 2002, str(e))
```

### 4.6 REST API

```python
# main.py

from fastapi import FastAPI, HTTPException, Query, Request
from models.dto import GenerationRequest, ResourceQueryParams
from task.manager import TaskManager
from common.dto import ApiResponse, PaginatedData, Resource, TaskInfo, success, error

app = FastAPI(title="资源生成编排器", version="1.0.0")
task_manager = TaskManager()


@app.post("/api/v1/sessions/{sessionId}/resources/generate", response_model=ApiResponse[dict])
async def start_resource_generation(sessionId: str, req: GenerationRequest, request: Request):
    """
    启动资源生成（内部接口，由网关触发）

    请求体（GenerationRequest）:
    {
        "text": "生成BERT模型的讲解PPT",
        "resourceType": "ppt",
        "profile": { ... }        // 用户画像（可选）
    }

    成功响应（ApiResponse[TaskInfo]）:
    {
        "code": 0,
        "message": "success",
        "data": {
            "taskId": "task_abc123",
            "status": "pending",
            "progress": 0,
            "createdAt": "2026-06-15T10:00:00Z",
            "updatedAt": "2026-06-15T10:00:00Z"
        },
        "requestId": "req_uuid"
    }
    """
    if not req.text:
        return error(1001, "参数错误: text 不能为空", request_id=str(request.headers.get("X-Request-Id", "")))

    task = await task_manager.create_task(
        session_id=sessionId,
        request=req.text
    )
    return success(task.to_dict(), request_id=str(request.headers.get("X-Request-Id", "")))


@app.get("/api/v1/resource-tasks/{taskId}", response_model=ApiResponse[TaskInfo])
async def get_task_status(taskId: str, request: Request):
    """
    查询任务状态

    成功响应（ApiResponse[TaskInfo]）:
    {
        "code": 0,
        "message": "success",
        "data": {
            "taskId": "task_xyz",
            "status": "processing",   // pending | processing | completed | failed
            "progress": 65,
            "progressDescription": "正在渲染幻灯片...",
            "result": { "resources": [...] },    // 完成后非空
            "createdAt": "2026-06-15T10:00:00Z",
            "updatedAt": "2026-06-15T10:05:00Z"
        },
        "requestId": "req_uuid"
    }

    任务不存在:
    {
        "code": 2001,
        "message": "任务不存在",
        "data": null,
        "requestId": "req_uuid"
    }
    """
    task = await task_manager.get_task(taskId)
    if not task:
        return error(ErrorCodeEnum.TASK_NOT_FOUND, "任务不存在", request_id=str(request.headers.get("X-Request-Id", "")))
    return success(task.to_dict(), request_id=str(request.headers.get("X-Request-Id", "")))


@app.get("/api/v1/sessions/{sessionId}/resources", response_model=ApiResponse[PaginatedData[Resource]])
async def get_resources(
    sessionId: str,
    request: Request,
    type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=100)
):
    """
    获取已生成的资源列表

    成功响应（ApiResponse[PaginatedData[Resource]]）:
    {
        "code": 0,
        "message": "success",
        "data": {
            "list": [
                {
                    "resourceId": "res_001",
                    "type": "ppt",
                    "title": "BERT模型原理与实战",
                    "url": "https://cdn.xxx/bert.pptx",
                    "description": "共15页",
                    "createdAt": "2026-06-15T10:00:00Z"
                }
            ],
            "pageInfo": { "page": 1, "pageSize": 20, "total": 50, "totalPages": 3 }
        },
        "requestId": "req_uuid"
    }
    """
    resources = await repository.get_resources(sessionId, type, page, pageSize)
    total = await repository.count_resources(sessionId, type)

    return success({
        "list": resources,
        "pageInfo": {
            "page": page,
            "pageSize": pageSize,
            "total": total,
            "totalPages": math.ceil(total / pageSize)
        }
    }, request_id=str(request.headers.get("X-Request-Id", "")))
```

### 4.7 WebSocket 进度通知

```python
# ws/notifier.py

class WsNotifier:
    """
    WebSocket 进度通知器
    
    职责：
    在资源生成的各个阶段，通过网关向客户端推送进度信息。
    
    本服务不直接连接客户端 WS，而是通过 REST 调用网关的内部接口，
    由网关负责推送消息给对应的客户端。
    
    推送消息格式（网关收到后转发给客户端）:
    {
        "msgId": "srv_uuid",
        "replyTo": "original_msg_id",
        "intent": "resource_generate",
        "type": "progress",
        "content": {
            "taskId": "task_xyz",
            "progress": 65,
            "description": "正在撰写第三节内容..."
        }
    }
    
    完成后推送:
    {
        "msgId": "srv_uuid",
        "replyTo": "original_msg_id",
        "intent": "resource_generate",
        "type": "resource_card",
        "content": {
            "resourceType": "ppt",
            "title": "BERT模型原理与实战",
            "url": "https://cdn.xxx/bert.pptx",
            "description": "共15页，涵盖Transformer回顾、BERT架构、CNN对比"
        }
    }
    """

    async def notify_progress(self, task_id: str, progress: int, description: str):
        """通知进度更新"""
        await self._send_to_gateway({
            "type": "progress",
            "content": {
                "taskId": task_id,
                "progress": progress,
                "description": description
            }
        })

    async def notify_complete(self, resource: Resource):
        """通知资源生成完成"""
        await self._send_to_gateway({
            "type": "resource_card",
            "content": {
                "resourceType": resource.type,
                "title": resource.title,
                "url": resource.url,
                "description": resource.description or ""
            }
        })

    async def _send_to_gateway(self, payload: dict):
        """通过内部 HTTP 调用网关的推送接口"""
        # 实际实现中，可调用网关的内部推送 API
        # 或通过共享的消息队列（Redis Pub/Sub / RabbitMQ）
        pass
```

---

## 5. 任务详解：路径规划智能体

### 5.1 项目结构

```
agents/path-planner/
├── src/
│   ├── main.py                     # FastAPI 入口
│   ├── config.py
│   ├── models/
│   │   └── dto.py
│   ├── services/
│   │   ├── path_generator.py       # 路径生成引擎
│   │   ├── path_adjuster.py        # 路径动态调整
│   │   ├── resource_binder.py      # 资源绑定
│   │   └── llm_service.py          # 大模型调用
│   ├── prompts/
│   │   ├── generate.txt            # 路径生成提示词
│   │   └── adjust.txt              # 路径调整提示词
│   └── db/
│       └── repository.py
├── tests/
├── requirements.txt
└── Dockerfile
```

### 5.2 核心服务方法

```python
# services/path_generator.py

class PathGenerator:
    """
    路径生成引擎
    
    职责：
    根据用户画像生成个性化的动态学习路径树。
    
    输入:
    - 用户画像（包含知识水平、目标、兴趣、薄弱点）
    - 已有资源列表（可绑定到路径节点）
    
    输出:
    - 有序的 PathNode 列表
    
    生成策略:
    1. 根据 knowledge_base.level 确定起点和路径坡度
    2. 根据 target_difficulty 确定最终目标深度
    3. 根据 interest_areas 优先安排感兴趣的模块
    4. 根据 weakness_preferences 插入专项练习节点
    5. 将已有资源绑定到对应节点
    
    路径结构示例（NLP 学习路径）:
    
    node 1: 数学基础回顾（已完成）
        └── 资源: 线性代数速查表.pdf
    
    node 2: Python 文本处理（已完成）
        └── 资源: NLTK实战教程.pptx
    
    node 3: 词向量与Word2Vec（进行中）
        └── 资源: 词向量原理与实现.pptx
    
    node 4: RNN与LSTM（待学习）
    node 5: Attention机制 ← 用户薄弱点，加练
        └── 资源: 注意力机制详解.pptx
    
    node 6: Transformer架构（待学习）
    node 7: BERT与预训练模型（待学习）
    """

    def __init__(self, llm_service, resource_binder):
        self.llm = llm_service
        self.resource_binder = resource_binder

    async def generate(
        self,
        session_id: str,
        profile: UserProfile,
        existing_resources: List[Resource]
    ) -> LearningPathResponse:
        """
        生成完整学习路径
        
        步骤:
        1. 分析画像 → 确定学习目标、起点、重点
        2. 调用大模型生成路径节点序列
        3. 将已有资源绑定到对应节点
        4. 排序、编号、保存
        5. 返回完整路径
        """
        # 1. 分析画像
        analysis = await self._analyze_profile(profile)
        
        # 2. 生成节点
        nodes = await self._generate_nodes(analysis)
        
        # 3. 资源绑定
        nodes = await self.resource_binder.bind(nodes, existing_resources)
        
        # 4. 保存
        path = LearningPathResponse(
            pathId=f"path_{uuid4().hex[:12]}",
            updatedAt=datetime.utcnow().isoformat(),
            nodes=nodes
        )
        await self._save_path(session_id, path)
        
        return path

    async def _analyze_profile(self, profile: UserProfile) -> dict:
        """
        分析画像，提取路径生成所需的关键信息
        
        输出:
        - startingPoint: 起点知识点
        - goalTopics: 目标涵盖的主题列表
        - focusAreas: 需要重点加强的领域
        - estimatedDuration: 预估总学时
        """
        pass

    async def _generate_nodes(self, analysis: dict) -> List[PathNode]:
        """
        根据分析结果生成有序节点
        
        使用大模型生成，提示词注入画像分析和路径设计原则。
        输出 JSON 数组，每个元素包含 title, description, 推荐的 resourceType。
        """
        pass


# services/path_adjuster.py

class PathAdjuster:
    """
    路径动态调整器
    
    职责：
    当评估智能体发现新的薄弱点，或用户画像发生变化时，
    对学习路径进行动态调整。
    
    调整类型:
    1. ADD — 在某个节点后插入新的练习节点
    2. MODIFY — 修改节点难度或推荐资源
    3. REMOVE — 移除已掌握的节点
    4. REORDER — 重新排列节点顺序
    """

    async def adjust(
        self,
        current_path: LearningPathResponse,
        evaluation_report: EvaluationReport,
        updated_profile: UserProfile
    ) -> LearningPathResponse:
        """
        根据评估结果调整路径
        
        步骤:
        1. 从 evaluation_report 提取 weakPoints
        2. 对每个 weakPoint，判断是否需要在路径中新增/修改节点
        3. 从 updated_profile 提取知识水平变化
        4. 如果水平提升，标记某些节点为已完成
        5. 生成调整后的路径
        
        返回: 更新后的完整路径
        """
        adjustments = []
        
        # 对每个薄弱点，生成 add 调整
        for wp in evaluation_report.weakPoints:
            if wp.severity >= 3:  # 严重薄弱
                adjustments.append(PathAdjustment(
                    nodeId=f"extra_{wp.topic}",
                    action="add",
                    title=f"{wp.topic}专项练习"
                ))
        
        # 应用调整
        adjusted_nodes = self._apply_adjustments(current_path.nodes, adjustments)
        
        return LearningPathResponse(
            pathId=current_path.pathId,
            updatedAt=datetime.utcnow().isoformat(),
            nodes=adjusted_nodes
        )


# services/resource_binder.py

class ResourceBinder:
    """
    资源绑定器
    
    职责：
    将已生成的资源自动匹配到学习路径的对应节点。
    
    匹配策略:
    1. 标题关键词匹配 — 资源标题与节点标题的语义相似度
    2. 内容主题匹配 — 资源描述与节点描述的主题关联度
    3. 手动绑定 — 用户可在前端手动关联资源到节点
    """

    async def bind(
        self,
        nodes: List[PathNode],
        resources: List[Resource]
    ) -> List[PathNode]:
        """
        将资源绑定到路径节点
        
        对每个节点:
        1. 计算与所有资源的匹配度
        2. 选择匹配度最高的资源（匹配度 > 0.6）
        3. 绑定到 node.resource
        
        匹配度计算:
        - 使用向量嵌入（embedding）计算语义相似度
        - 或使用关键词 TF-IDF 匹配
        """
        for node in nodes:
            best_match = None
            best_score = 0
            
            for res in resources:
                score = self._calculate_match(node.title, res.title, res.description or "")
                if score > best_score and score > 0.6:
                    best_score = score
                    best_match = res
            
            if best_match:
                node.resource = {
                    "resourceId": best_match.resourceId,
                    "type": best_match.type,
                    "url": best_match.url
                }
        
        return nodes
```

### 5.3 REST API

```python
# main.py

from fastapi import FastAPI, HTTPException, Request
from common.dto import ApiResponse, LearningPathResponse, success, error

app = FastAPI(title="路径规划智能体", version="1.0.0")


@app.get("/api/v1/sessions/{sessionId}/learning-path", response_model=ApiResponse[LearningPathResponse])
async def get_learning_path(sessionId: str, request: Request):
    """
    获取学习路径

    成功响应（ApiResponse[LearningPathResponse]）:
    {
        "code": 0,
        "message": "success",
        "data": {
            "pathId": "path_uuid",
            "updatedAt": "2026-06-15T10:00:00Z",
            "nodes": [
                { "nodeId": "node1", "order": 1, "title": "...", "resource": {...}, "status": "completed" },
                { "nodeId": "node2", "order": 2, "title": "...", "resource": {...}, "status": "in_progress" }
            ]
        },
        "requestId": "req_uuid"
    }

    会话不存在:
    {
        "code": 1002,
        "message": "会话不存在",
        "data": null,
        "requestId": "req_uuid"
    }
    """
    path = await repository.get_path(sessionId)
    if not path:
        # 首次访问，需生成路径
        profile = await profile_service.get_profile(sessionId)
        resources = await resource_service.get_all_resources(sessionId)
        generator = PathGenerator(llm_service, resource_binder)
        path = await generator.generate(sessionId, profile, resources)
        if not path:
            return error(1002, "会话不存在", request_id=str(request.headers.get("X-Request-Id", "")))

    return success(path.to_dict(), request_id=str(request.headers.get("X-Request-Id", "")))


@app.post("/api/v1/sessions/{sessionId}/recommend", response_model=ApiResponse[None])
async def trigger_recommendation(sessionId: str, request: Request):
    """
    强制触发推荐

    成功响应:
    {
        "code": 0,
        "message": "success",
        "data": null,
        "requestId": "req_uuid"
    }
    """
    # 后台触发推送
    asyncio.create_task(self._push_recommendation(sessionId))
    return success(None, request_id=str(request.headers.get("X-Request-Id", "")))
```

---

## 6. 任务详解：工程化与文档

### 6.1 CI/CD 配置

```yaml
# .github/workflows/ci.yml

name: CI

on:
  push:
    branches: [ develop, main, 'feature/**' ]
  pull_request:
    branches: [ develop ]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Lint Python
        run: |
          pip install pylint black
          pylint agents/*/src/
          black --check agents/*/src/
      - name: Lint TypeScript
        run: |
          cd common && npm install && npm run lint
          
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Test Python agents
        run: |
          pip install pytest
          pytest agents/profile/tests/
          pytest agents/resource-gen/tests/
          pytest agents/path-planner/tests/
      - name: Test common lib
        run: |
          cd common && npm install && npm test

  api-contract-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: API Contract Test
        run: |
          # 启动所有 Mock 服务
          # 运行接口契约测试（验证 API 响应格式是否符合规范）
          echo "API contract tests passed"
```

### 6.2 PR 模板

```markdown
# .github/PULL_REQUEST_TEMPLATE.md

## 变更描述
<!-- 简要描述本次 PR 的内容和目的 -->

## 关联 Issue
<!-- Closes #xxx -->

## 变更类型
- [ ] feat: 新功能
- [ ] fix: Bug 修复
- [ ] refactor: 重构
- [ ] docs: 文档更新
- [ ] test: 测试
- [ ] chore: 构建/工具

## 测试情况
- [ ] 单元测试已添加/更新
- [ ] 本地测试通过
- [ ] 接口契约符合规范文档

## Review  Checklist
- [ ] 代码符合编码规范
- [ ] 接口兼容已有契约
- [ ] 错误处理完整
- [ ] 无硬编码密钥/凭据
```

### 6.3 本地启动脚本

```bash
# scripts/start-all.sh

#!/bin/bash
# 一键启动所有服务（开发模式）

echo "=== 启动个性化学习系统 开发环境 ==="

# 1. 启动 common 库监听
echo "[1/5] 编译 common 库..."
cd common && npm run build:watch &

# 2. 启动网关
echo "[2/5] 启动 API 网关 (端口 3000)..."
cd gateway && npm run dev &

# 3. 启动画像智能体
echo "[3/5] 启动画像智能体 (端口 8081)..."
cd agents/profile && uvicorn src.main:app --port 8081 --reload &

# 4. 启动资源生成编排器
echo "[4/5] 启动资源生成编排器 (端口 8090)..."
cd agents/resource-gen && uvicorn src.main:app --port 8090 --reload &

# 5. 启动路径规划智能体
echo "[5/5] 启动路径规划智能体 (端口 8091)..."
cd agents/path-planner && uvicorn src.main:app --port 8091 --reload &

echo "=== 所有服务已启动 ==="
wait
```

---

## 7. 核心数据模型（DTO）

### 全量 DTO 清单

| # | DTO 名称 | 源文件 | 使用方 |
|---|---------|--------|--------|
| 1 | `ApiResponse<T>` | `common/dto/ApiResponse.ts` | A, B, C |
| 2 | `PageInfo` | `common/dto/PageInfo.ts` | A, C |
| 3 | `PaginatedData<T>` | `common/dto/PageInfo.ts` | A, C |
| 4 | `CreateSessionRequest` | `common/dto/SessionDTO.ts` | A |
| 5 | `CreateSessionResponse` | `common/dto/SessionDTO.ts` | A |
| 6 | `UserProfile` | `common/dto/ProfileDTO.ts` | A, B, C |
| 7 | `ProfileDimensions` | `common/dto/ProfileDTO.ts` | B, C |
| 8 | `Resource` | `common/dto/ResourceDTO.ts` | A, C |
| 9 | `TaskInfo` | `common/dto/TaskDTO.ts` | A, C |
| 10 | `TaskProgressContent` | `common/dto/TaskDTO.ts` | A, C |
| 11 | `PathNode` | `common/dto/PathDTO.ts` | A, C |
| 12 | `LearningPathResponse` | `common/dto/PathDTO.ts` | A, C |
| 13 | `SubmitEvaluationRequest` | `common/dto/EvaluationDTO.ts` | A, B |
| 14 | `EvaluationReport` | `common/dto/EvaluationDTO.ts` | A, B |
| 15 | `IntentEnum` / `Intent` | `common/enums/IntentEnum.ts` | A, B, C |
| 16 | `ResourceTypeEnum` / `ResourceType` | `common/enums/ResourceTypeEnum.ts` | A, C |
| 17 | `TaskStatusEnum` / `TaskStatus` | `common/enums/TaskStatusEnum.ts` | A, C |
| 18 | `PathNodeStatusEnum` / `PathNodeStatus` | `common/enums/PathNodeStatusEnum.ts` | A, C |
| 19 | `ErrorCodeEnum` | `common/enums/ErrorCodeEnum.ts` | A, B, C |
| 20 | `IdGenerator` | `common/utils/IdGenerator.ts` | A, B, C |

---

## 8. 开发步骤与 Git 提交计划

### 第 1 步：公共共享库（Day 1-2）⭐ 最优先

```
操作顺序:
1. 从 develop 分支创建 feature/common-lib 分支
   → git checkout -b feature/common-lib develop

2. 初始化 TypeScript 项目
   → mkdir -p common/src/{dto,enums,utils}
   → cd common && npm init -y
   → npm install -D typescript @types/node ts-node
   → npx tsc --init

3. 实现 enums/ErrorCodeEnum.ts（最先，因为后面所有 DTO 依赖）
4. 实现 enums/IntentEnum.ts
5. 实现 enums/ResourceTypeEnum.ts
6. 实现 enums/TaskStatusEnum.ts
7. 实现 enums/PathNodeStatusEnum.ts

8. 实现 utils/IdGenerator.ts
9. 实现 utils/JsonUtils.ts

10. 实现 dto/ApiResponse.ts + dto/PageInfo.ts（最基础）
11. 实现 dto/SessionDTO.ts
12. 实现 dto/ProfileDTO.ts（与 B 协作）
13. 实现 dto/ResourceDTO.ts
14. 实现 dto/TaskDTO.ts
15. 实现 dto/PathDTO.ts
16. 实现 dto/EvaluationDTO.ts

17. 实现 index.ts（统一导出所有模块）
18. 配置 package.json 的 main/types/scripts

19. 编写 README.md，说明如何使用

✅ Git 提交（建议分 3-4 次提交）：
   git add common/ && git commit -m "feat(common): add enums and utility functions"
   git add common/ && git commit -m "feat(common): add core DTOs (ApiResponse, Session, Profile)"
   git add common/ && git commit -m "feat(common): add Resource, Task, Path, Evaluation DTOs"
   git push -u origin feature/common-lib

   → 立即创建 PR，请求全员 Review（因为大家都依赖 common）
   → 合并后通知 A 和 B 拉取最新代码
```

### 第 2 步：CI/CD + PR 模板 + 项目基础设施（Day 2，与第 1 步部分并行）

```
操作顺序:
1. 从 develop 分支创建 feature/ci-cd 分支
   → git checkout -b feature/ci-cd develop

2. 创建 .github/workflows/ci.yml
3. 创建 .github/PULL_REQUEST_TEMPLATE.md
4. 创建 scripts/start-all.sh
5. 创建 .dockerignore 和 agents/*/Dockerfile（可选）

✅ Git 提交：
   git add .github/ scripts/
   git commit -m "chore: add CI/CD, PR template, and dev scripts"
   git push -u origin feature/ci-cd
   → 创建 PR → Review → 合并到 develop
```

### 第 3 步：资源生成编排器 — 核心框架 + 任务管理（Day 3-5）

```
操作顺序:
1. 从 develop 分支创建 feature/agent-resource-gen 分支
   → git checkout -b feature/agent-resource-gen develop

2. 创建 agents/resource-gen/ 项目结构
   → pip install fastapi uvicorn python-pptx websockets pydantic

3. 实现 task/manager.py — 异步任务管理器
   - create_task() / get_task() / update_progress() / complete_task() / fail_task()
   
4. 实现 task/store.py — 任务存储（先用内存 dict）

5. 实现 ws/notifier.py — 进度通知（先预留接口）

6. 实现 main.py — FastAPI 入口
   - GET /resource-tasks/{taskId}
   - GET /sessions/{sessionId}/resources

7. 编写基本测试

✅ Git 提交：
   git add agents/resource-gen/
   git commit -m "feat(resource-gen): init project with task manager and REST APIs"
   git push -u origin feature/agent-resource-gen
```

### 第 4 步：资源生成 — 管线 + 子智能体（Day 5-9）

```
操作顺序:
1. 实现 services/llm_service.py — 大模型调用封装
2. 实现 prompts/outline.txt — 大纲生成提示词

3. 实现 orchestrator/outline_generator.py
   - 调用大模型生成大纲 JSON

4. 实现 orchestrator/content_writer.py
   - 逐章生成内容
   - 独立章节并行生成

5. 实现 orchestrator/ppt_renderer.py
   - python-pptx 渲染
   - 支持封面、目录、内容、代码等 layout

6. 实现 orchestrator/doc_renderer.py
   - Markdown 输出
   - 思维导图 HTML 输出

7. 实现 orchestrator/review_checker.py
   - 集成安全过滤和防幻觉检查

8. 实现 orchestrator/pipeline.py
   - 串联所有子智能体
   - 进度更新 + 通知

9. 在 main.py 中注册生成入口

✅ Git 提交（建议分多次）：
   git add . && git commit -m "feat(resource-gen): implement LLM service and outline generator"
   git add . && git commit -m "feat(resource-gen): implement content writer with parallel sections"
   git add . && git commit -m "feat(resource-gen): implement PPT renderer with python-pptx"
   git add . && git commit -m "feat(resource-gen): implement doc renderer (MD and mindmap)"
   git add . && git commit -m "feat(resource-gen): implement pipeline orchestrator"
   git add . && git commit -m "test(resource-gen): add pipeline and renderer tests"
   git push

   → 创建 PR → Review → 合并到 develop（注意：这时候可以先合并，因为端口不冲突）
```

### 第 5 步：路径规划智能体（Day 8-11，可与第 4 步并行）

```
操作顺序:
1. 从 develop 分支创建 feature/agent-path-planner 分支
   → git checkout -b feature/agent-path-planner develop

2. 创建 agents/path-planner/ 项目结构

3. 实现 services/llm_service.py

4. 实现 services/path_generator.py
   - _analyze_profile()
   - _generate_nodes()
   - generate()

5. 实现 prompts/generate.txt — 路径生成提示词

6. 实现 services/resource_binder.py
   - 资源-节点匹配逻辑

7. 实现 services/path_adjuster.py
   - 基于评估结果的路径调整
   - prompts/adjust.txt

8. 实现 main.py — REST API
   - GET /sessions/{sessionId}/learning-path
   - POST /sessions/{sessionId}/recommend

✅ Git 提交：
   git add . && git commit -m "feat(path-planner): init project with path generator"
   git add . && git commit -m "feat(path-planner): implement resource binder and path adjuster"
   git add . && git commit -m "feat(path-planner): add REST APIs for path query and recommendation"
   git add . && git commit -m "test(path-planner): add path generator tests"
   git push -u origin feature/agent-path-planner
   → 创建 PR → Review → 合并到 develop
```

### 第 6 步：文档同步 + WS 推送集成（Day 11-13）

```
操作顺序:
1. 确保 docs/api.md 与当前实现一致
2. 补充 docs/ 中的架构图描述
3. 完善 scripts/start-all.sh（整合所有服务的启动命令）
4. 完善 agents/resource-gen/ 的 WS 通知集成
5. 完善 agents/path-planner/ 的 WS 推送集成

✅ Git 提交：
   git add docs/ scripts/
   git commit -m "docs: sync API docs and update startup scripts"
   git add agents/resource-gen/ agents/path-planner/
   git commit -m "feat: integrate WS notifications for resource gen and path planner"
   git push
```

### 第 7 步：三方联调（Day 14-18）

```
操作顺序:
1. 在本地启动所有服务：
   - common（已发布到本地 npm/pip）
   - gateway（人员 A）
   - profile / tutor / evaluator（人员 B）
   - resource-gen / path-planner（人员 C）

2. 先打通 REST API 联调：
   - POST /sessions → GET /learning-path
   - POST /sessions → GET /resources
   
3. 再打通 WS 联调：
   - WS → profile_build（人员 B）
   - WS → resource_generate（与人员 A 配合验证进度推送）
   - WS → path_query

4. 修复集成问题（常见问题）:
   - DTO 字段命名不一致
   - WS 消息格式不匹配
   - 端口配置错误
   - 错误码不一致

✅ Git 提交：
   git add .
   git commit -m "fix: resolve integration issues across services"
   git push
```

### 第 8 步：最终交付（Day 19-21）

```
操作顺序:
1. 合并所有 feature 分支到 develop
   → git checkout develop
   → git merge feature/common-lib
   → git merge feature/agent-resource-gen
   → git merge feature/agent-path-planner
   → git merge feature/ci-cd

2. 最终集成测试（全员参与）
3. 打 tag 发布
   → git checkout main
   → git merge develop
   → git tag v1.0.0
   → git push origin main --tags

4. 准备演示材料
```

---

## 附录：服务端口与路由汇总

| 服务 | 内部端口 | 外部路径（经网关） | 协议 | 负责人 |
|------|---------|-------------------|------|--------|
| gateway | 3000 | 所有 API | REST/WS | A |
| agent-profile | 8081 | /ws/chat (intent=profile_build) | WS | B |
| agent-tutor | 8082 | /ws/chat (intent=tutoring) | WS | B |
| agent-evaluator | 8080 | /evaluation/* | REST | B |
| agent-resource-gen | 8090 | /resource-tasks/*, /sessions/{id}/resources | REST | C |
| agent-path-planner | 8091 | /sessions/{id}/learning-path, /recommend | REST | C |

## 附录：common 库发布流程

```bash
# TypeScript (npm)
cd common
npm run build          # tsc 编译
npm version patch      # 版本号递增
npm link               # 本地链接
# 其他项目使用: npm link @ai-edu/common

# 或直接提交到 Git，其他项目通过 git submodule 或直接拷贝引用
```

## 附录：关键提示词模板

### 大纲生成提示词（prompts/outline.txt）

```
你是一个专业的教学大纲设计专家。
请根据以下信息，为学习者生成一份详细的学习/教学大纲。

用户需求: {user_request}

学习者画像:
- 当前知识水平: {knowledge_level}（已掌握: {knowledge_tags}）
- 认知风格: {cognitive_style}
- 学习节奏: {learning_pace}
- 薄弱知识点: {weakness_tags}
- 兴趣领域: {interest_areas}
- 目标难度: {target_difficulty}/10

输出格式要求（JSON）:
{{
  "title": "大纲标题",
  "sections": [
    {{
      "order": 1,
      "title": "章节标题",
      "description": "章节简要描述",
      "estimatedMinutes": 15,
      "subsections": [
        {{ "order": 1.1, "title": "小节标题", "estimatedMinutes": 10 }}
      ]
    }}
  ]
}}

设计原则:
1. 从基础知识逐步过渡到高级内容
2. 在薄弱知识点处设计更多练习环节
3. 穿插用户感兴趣领域的应用案例
4. 控制总时长在合理范围内（每章 15-30 分钟）
5. 如果用户要求对比，增加对比分析章节
```

---

> **建议执行顺序：** common 共享库（最优先，第 1 天）→ CI/CD 基础设施（第 2 天）→ 资源生成任务管理（第 3-5 天）→ 管线子智能体（第 5-9 天）→ 路径规划（第 8-11 天，与上一步重叠）→ 文档同步（第 11-13 天）→ 三方联调（第 14-18 天）→ 交付（第 19-21 天）  
> **注意：** common 库是 A、B 的开发基础，**必须在第 2 天结束前完成并通知全员拉取**
