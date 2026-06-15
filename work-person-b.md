# 人员 B 工作手册：对话与学习核心智能体

> **负责模块：** `agents/profile/`（画像智能体）+ `agents/tutor/`（辅导智能体）+ `agents/evaluator/`（评估智能体）  
> **工作目标：** 实现"画像 + 辅导 + 评估"3 个智能体，覆盖用户画像构建、个性化答疑、学习评估全流程  
> **主要协作对象：** 人员 A（WebSocket/REST 对接）、人员 C（共享 DTO + 安全模块协作）

---

## 目录

1. [技术栈选型](#1-技术栈选型)
2. [工作任务总览](#2-工作任务总览)
3. [任务详解：画像智能体](#3-任务详解画像智能体)
4. [任务详解：辅导智能体](#4-任务详解辅导智能体)
5. [任务详解：评估智能体](#5-任务详解评估智能体)
6. [任务详解：内容安全与防幻觉模块](#6-任务详解内容安全与防幻觉模块)
7. [核心数据模型（DTO）](#7-核心数据模型dto)
8. [开发步骤与 Git 提交计划](#8-开发步骤与-git-提交计划)

---

## 1. 技术栈选型

| 模块 | 推荐技术 | 备选方案 |
|------|---------|---------|
| **编程语言** | Python 3.11+ | Node.js |
| **Web 框架** | FastAPI | Flask |
| **大模型 SDK** | OpenAI API（`openai`） | Anthropic API |
| **WebSocket 库** | `websockets`（Python） | FastAPI WebSocket |
| **向量数据库** | ChromaDB（轻量） | FAISS |
| **嵌入模型** | OpenAI Embedding（`text-embedding-3-small`） | text2vec |
| **序列化** | Pydantic v2 | — |
| **测试** | pytest | — |
| **开发工具** | Pylint + Black + isort | — |

> **核心模型选择说明：** 采用 OpenAI API 作为大模型服务（GPT-4o / GPT-4o-mini），通过 `openai` Python SDK 调用。若需本地部署可选用开源模型（如 Qwen2.5、DeepSeek），需在文档中标注来源。

---

## 2. 工作任务总览

### 2.1 画像智能体 — agents/profile/

| 编号 | 任务 | 优先级 | 说明 |
|------|------|--------|------|
| B-PR-01 | 画像 Schema 定义与校验 | P0 | 与 C 协作完成 |
| B-PR-02 | 对话式画像构建（多轮追问） | P0 | WS 接收 profile_build |
| B-PR-03 | 画像增量更新 | P0 | 学习过程中动态更新 |
| B-PR-04 | 画像持久化 | P1 | 数据库存储 |

### 2.2 辅导智能体 — agents/tutor/

| 编号 | 任务 | 优先级 | 说明 |
|------|------|--------|------|
| B-TU-01 | 个性化问答引擎 | P0 | WS 接收 tutoring |
| B-TU-02 | 基于画像的答案定制 | P0 | 结合画像维度调整回答 |
| B-TU-03 | 多模态输入处理 | P1 | 图片/附件理解 |
| B-TU-04 | 对话上下文管理 | P0 | 多轮对话记忆 |

### 2.3 评估智能体 — agents/evaluator/

| 编号 | 任务 | 优先级 | 说明 |
|------|------|--------|------|
| B-EV-01 | 评估数据提交 REST API | P0 | POST /evaluation/submit |
| B-EV-02 | 评估报告生成 REST API | P0 | GET /sessions/{id}/evaluation-report |
| B-EV-03 | 多维度评价模型 | P0 | 知识、理解、应用等维度 |
| B-EV-04 | 薄弱知识点分析 | P0 | 输出薄弱点列表 |
| B-EV-05 | 路径调整建议输出 | P1 | 建议的学习路径调整 |
| B-EV-06 | 行为数据收集与分析 | P1 | 视频暂停/快进等行为 |

### 2.4 内容安全与防幻觉（通用模块）

| 编号 | 任务 | 优先级 | 说明 |
|------|------|--------|------|
| B-SF-01 | 内容安全过滤器 | P0 | 违规内容拦截（code 3001） |
| B-SF-02 | 事实核查/防幻觉 | P0 | 无根据内容拦截（code 3002） |

---

## 3. 任务详解：画像智能体

### 3.1 项目结构

```
agents/profile/
├── src/
│   ├── main.py                 # FastAPI 入口 + WebSocket 端点
│   ├── config.py               # 配置（模型密钥、数据库连接）
│   ├── models/
│   │   ├── schema.py           # 画像 Schema 定义（Pydantic）
│   │   └── dto.py              # 消息 DTO
│   ├── services/
│   │   ├── profile_builder.py  # 画像构建核心逻辑
│   │   ├── profile_updater.py  # 画像增量更新
│   │   └── llm_service.py      # 大模型调用封装
│   ├── prompts/
│   │   ├── build.txt           # 画像构建提示词模板
│   │   └── update.txt          # 画像更新提示词模板
│   ├── db/
│   │   ├── repository.py       # 画像数据持久化
│   │   └── memory.py           # 对话记忆存储
│   └── ws/
│       └── handler.py          # WebSocket 消息处理器
├── tests/
│   ├── test_profile_builder.py
│   └── test_schema.py
├── requirements.txt
└── Dockerfile
```

### 3.2 画像 Schema 定义

```python
# models/schema.py
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
from datetime import datetime


class KnowledgeLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class CognitiveStyle(str, Enum):
    THEORETICAL = "theoretical"       # 理论推导型
    PRACTICAL = "practical"           # 实践应用型
    VISUAL = "visual"                 # 视觉图像型
    VERBAL = "verbal"                 # 语言阅读型


class LearningPace(str, Enum):
    SLOW = "slow"
    MODERATE = "moderate"
    FAST = "fast"


class ProfileDimension(BaseModel):
    """画像维度基类"""
    confidence: float = Field(ge=0.0, le=1.0, description="该维度的置信度")


class KnowledgeBase(ProfileDimension):
    """知识基础"""
    level: KnowledgeLevel
    tags: List[str] = Field(default_factory=list, description="已掌握的知识标签")


class CognitiveStyleDim(ProfileDimension):
    """认知风格"""
    style: CognitiveStyle
    detail: str = ""


class LearningPaceDim(ProfileDimension):
    """学习节奏"""
    pace: LearningPace
    preferred_session_minutes: int = 30


class WeaknessPreference(ProfileDimension):
    """易错点偏好"""
    weak_tags: List[str] = Field(default_factory=list, description="薄弱知识点标签")
    description: str = ""


class InterestArea(ProfileDimension):
    """兴趣领域"""
    areas: List[str] = Field(default_factory=list)
    depth: int = Field(ge=1, le=5, default=3)


class TargetDifficulty(ProfileDimension):
    """目标难度等级"""
    level: int = Field(ge=1, le=10, default=5)
    description: str = ""


class UserProfile(BaseModel):
    """完整用户画像"""
    session_id: str
    dimensions: ProfileDimensions
    raw_dialogue: List[str] = Field(default_factory=list, description="构建过程中的对话原文")
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    version: int = 1


class ProfileDimensions(BaseModel):
    """画像维度集合（至少 6 个维度）"""
    knowledge_base: Optional[KnowledgeBase] = None
    cognitive_style: Optional[CognitiveStyleDim] = None
    learning_pace: Optional[LearningPaceDim] = None
    weakness_preferences: List[WeaknessPreference] = Field(default_factory=list)
    interest_areas: List[InterestArea] = Field(default_factory=list)
    target_difficulty: Optional[TargetDifficulty] = None
```

### 3.3 核心服务方法

#### 3.3.1 画像构建 — `services/profile_builder.py`

```python
class ProfileBuilder:
    """
    画像构建服务
    
    职责：
    通过多轮对话逐步构建用户画像。
    每次用户发送 profile_build 意图的消息，触发追问-回答循环。
    当画像信息足够丰富（所有维度置信度 > 0.7）时，结束构建。
    
    工作流程：
    1. 接收用户消息 → 提取关键信息
    2. 判断哪些画像维度已覆盖、哪些缺失
    3. 对缺失/低置信度维度生成追问问题
    4. 用户回答后更新对应维度 + 提高置信度
    5. 所有维度置信度 >= 0.7 → 返回 type=done
    """

    def __init__(self, llm_service: LLMService):
        self.llm = llm_service

    async def process_message(
        self,
        session_id: str,
        user_text: str,
        current_profile: Optional[UserProfile]
    ) -> ProfileBuildResult:
        """
        处理用户的一条消息，返回更新后的画像和回复
        
        参数:
            session_id: 会话 ID
            user_text: 用户输入的文本
            current_profile: 当前画像（None 表示首次构建）
        
        返回:
            ProfileBuildResult: {
                "updated_profile": UserProfile,   # 更新后的画像
                "reply_text": str,                 # 回复文本
                "is_complete": bool,               # 画像是否构建完成
                "missing_dimensions": List[str]     # 仍未覆盖的维度
            }
        """
        pass

    def _extract_profile_info(self, text: str) -> dict:
        """
        从用户文本中提取画像信息
        
        使用大模型解析用户输入，提取与画像维度相关的信息。
        例如 "我是人工智能大三学生，刚学完吴恩达机器学习"
        → { knowledge_base: { level: "intermediate", tags: ["机器学习"] } }
        """
        pass

    def _generate_question(self, missing_dims: List[str]) -> str:
        """
        对缺失维度生成追问问题
        
        追问策略:
        - 每次最多追问 1-2 个维度
        - 问题应自然、友好，不像是机器在"填表"
        - 示例: "你更喜欢理论推导还是动手做项目？"（认知风格）
        """
        pass

    def _assess_completeness(self, profile: UserProfile) -> bool:
        """
        判断画像是否构建完整
        
        标准: 所有 6 个维度都存在且置信度 >= 0.7
        """
        pass
```

#### 3.3.2 画像更新 — `services/profile_updater.py`

```python
class ProfileUpdater:
    """
    画像增量更新服务
    
    职责：
    在学习过程中，根据用户的行为（问答、做题、资源观看）动态更新画像。
    例如: 用户频繁问 NLP 问题 → interest_areas 增加 NLP 权重
         用户做错某类题目 → weakness_preferences 更新
    
    触发时机:
    1. tutoring 对话中提取新的画像信息
    2. evaluate 结果回写到画像
    3. 用户主动补充信息
    """

    async def update_from_dialogue(
        self,
        session_id: str,
        dialogue_history: List[dict],
        current_profile: UserProfile
    ) -> UserProfile:
        """
        从对话中提取画像更新信息
        
        参数:
            dialogue_history: 最近 N 轮对话
            current_profile: 当前画像
        
        返回: 更新后的画像
        """
        pass

    async def update_from_evaluation(
        self,
        session_id: str,
        evaluation_result: dict,
        current_profile: UserProfile
    ) -> UserProfile:
        """
        从评估结果更新画像
        
        例如: 评估发现用户"注意力机制"薄弱
        → weakness_preferences 增加 "Attention"
        → knowledge_base 相应调整
        """
        pass
```

#### 3.3.3 大模型调用封装 — `services/llm_service.py`

```python
class LLMService:
    """
    大模型调用封装
    
    封装 OpenAI API 调用，提供统一的完成/流式完成接口。
    支持提示词模板渲染和对话历史管理。
    """

    def __init__(self, api_key: str, model: str = "gpt-4o"):
        """
        初始化 OpenAI 客户端
        
        工具: openai Python SDK
        安装: pip install openai
        文档: https://platform.openai.com/docs/api-reference
        """
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key)
        self.model = model

    async def chat(
        self,
        messages: List[dict],
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> str:
        """
        非流式对话完成
        
        参数:
            messages: [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]
            temperature: 生成温度
            max_tokens: 最大输出 Token 数
        
        返回: 模型生成的文本
        """
        pass

    async def chat_stream(
        self,
        messages: List[dict],
        temperature: float = 0.7
    ) -> AsyncGenerator[str, None]:
        """
        流式对话完成（用于 WS 推送）
        
        逐 token 生成，通过 WS 实时推送 type=text 消息
        """
        pass
```

### 3.4 WebSocket 消息处理

```python
# ws/handler.py

class ProfileWSHandler:
    """
    WebSocket 消息处理器（画像构建）
    
    处理 /ws/chat 中 intent=profile_build 的消息
    
    输入消息帧:
    {
        "msgId": "client_uuid",
        "intent": "profile_build",
        "content": { "text": "我是人工智能大三学生..." },
        "context": {}
    }
    
    输出消息帧（逐条推送，最后一条 type=done）:
    {
        "msgId": "srv_uuid",
        "replyTo": "client_uuid",
        "intent": "profile_build",
        "type": "text",
        "content": { "markdown": "好的！让我先了解一下你的基础..." }
    }
    {
        "msgId": "srv_uuid",
        "replyTo": "client_uuid",
        "intent": "profile_build",
        "type": "done",
        "content": { "profile": { ... } }  // 包含当前画像摘要
    }
    """

    async def handle_message(self, message: dict, profile: UserProfile) -> List[dict]:
        """
        处理一条 profile_build 消息
        
        返回: 服务端推送帧列表
        """
        pass
```

---

## 4. 任务详解：辅导智能体

### 4.1 项目结构

```
agents/tutor/
├── src/
│   ├── main.py                 # FastAPI 入口 + WebSocket 端点
│   ├── config.py               # 配置
│   ├── models/
│   │   ├── context.py          # 对话上下文模型
│   │   └── dto.py              # 消息 DTO
│   ├── services/
│   │   ├── tutor_engine.py     # 辅导引擎核心
│   │   ├── answer_generator.py # 答案生成（含画像适配）
│   │   ├── context_manager.py  # 对话上下文管理
│   │   └── llm_service.py      # 大模型调用（同画像智能体模式）
│   ├── prompts/
│   │   ├── system.txt          # 系统提示词（角色设定）
│   │   └── adapt.txt           # 画像适配提示词
│   ├── db/
│   │   └── chat_history.py     # 对话历史存储
│   └── ws/
│       └── handler.py          # WebSocket 消息处理器
├── tests/
│   ├── test_tutor_engine.py
│   └── test_answer_generator.py
├── requirements.txt
└── Dockerfile
```

### 4.2 核心服务方法

```python
# services/tutor_engine.py

class TutorEngine:
    """
    辅导引擎
    
    职责：
    接收用户的辅导请求（intent=tutoring），结合画像生成个性化回答。
    支持多模态输入（图片/附件），输出图文混合 Markdown。
    
    核心策略：
    1. 根据画像中的 knowledge_base 调整回答深度
    2. 根据 cognitive_style 调整呈现方式（理论推导 / 代码示例 / 图解）
    3. 根据 learning_pace 调整语速和信息密度
    4. 关联 weakness_preferences 对薄弱点着重讲解
    5. 关联 interest_areas 使用用户感兴趣的例子
    """

    def __init__(self, llm_service, profile_service):
        self.llm = llm_service
        self.profile_service = profile_service

    async def generate_answer(
        self,
        session_id: str,
        question: str,
        attachments: List[dict],
        context: dict
    ) -> AsyncGenerator[dict, None]:
        """
        生成个性化辅导回答
        
        参数:
            session_id: 会话 ID（用于获取画像）
            question: 用户问题
            attachments: 附件列表（图片等）
            context: 上下文（resourceId, courseId 等）
        
        生成（yield）:
            逐步输出 type=text 流式消息
            最终输出 type=done 结束
        
        实现步骤:
        1. 从 profile_service 获取当前画像
        2. 根据画像构建系统提示词（注入画像维度信息）
        3. 从 context_manager 获取对话历史
        4. 调用 llm.chat_stream() 生成回答
        5. 将回答通过 WS 逐段推送给前端
        """
        # 1. 获取画像
        profile = await self.profile_service.get_profile(session_id)
        
        # 2. 构建系统提示词
        system_prompt = self._build_system_prompt(profile, context)
        
        # 3. 构建消息列表
        messages = self._build_messages(system_prompt, question, attachments)
        
        # 4. 流式生成
        async for chunk in self.llm.chat_stream(messages):
            yield {
                "type": "text",
                "content": {"markdown": chunk}
            }
        
        # 5. 结束
        yield {"type": "done", "content": {}}

    def _build_system_prompt(self, profile: UserProfile, context: dict) -> str:
        """
        根据画像和上下文构建系统提示词
        
        例如:
        - 用户知识水平=intermediate → "使用中等难度的术语解释"
        - 认知风格=practical → "多提供代码示例和实际应用场景"
        - 薄弱点包含"注意力机制" → "对注意力机制部分重点讲解"
        """
        pass

    def _build_messages(
        self,
        system_prompt: str,
        question: str,
        attachments: List[dict]
    ) -> List[dict]:
        """
        构建大模型消息列表
        
        如果有图片附件，根据模型能力选择:
        - 支持多模态 → 直接传入 image_url
        - 不支持 → 先使用图片描述模型生成文本描述再传入
        """
        pass


# services/context_manager.py

class ContextManager:
    """
    对话上下文管理器
    
    职责：
    维护多轮对话历史，支持上下文窗口截断。
    当对话过长时，自动摘要历史或丢弃最早轮次。
    
    策略:
    - 保留最近 10 轮完整对话
    - 超过 10 轮时，将前文压缩为摘要
    - 每次请求携带最近 N 轮 + 摘要
    """

    MAX_ROUNDS = 10

    async def get_context(self, session_id: str) -> List[dict]:
        """获取当前会话的对话上下文"""
        pass

    async def append_round(self, session_id: str, question: str, answer: str):
        """追加一轮对话记录"""
        pass

    async def summarize_history(self, session_id: str) -> str:
        """对历史对话进行摘要"""
        pass
```

---

## 5. 任务详解：评估智能体

### 5.1 项目结构

```
agents/evaluator/
├── src/
│   ├── main.py                 # FastAPI 入口 + REST 端点
│   ├── config.py
│   ├── models/
│   │   ├── evaluation.py       # 评估模型
│   │   └── dto.py              # 请求/响应 DTO
│   ├── services/
│   │   ├── evaluator.py        # 评估引擎核心
│   │   ├── quiz_grader.py      # 答题评分
│   │   ├── behavior_analyzer.py# 行为分析
│   │   ├── weakness_finder.py  # 薄弱点发现
│   │   └── llm_service.py      # 大模型调用
│   ├── prompts/
│   │   ├── grade.txt           # 评分提示词
│   │   └── analyze.txt         # 分析提示词
│   └── db/
│       └── repository.py
├── tests/
├── requirements.txt
└── Dockerfile
```

### 5.2 REST API 定义

#### 5.2.1 提交评估数据 — `POST /evaluation/submit`

```python
# main.py
from fastapi import FastAPI, HTTPException, Request
from models.dto import (
    ApiResponse,
    EvaluationSubmitRequest,
    EvaluationSubmitData,
    EvaluationReport,
    success,
    error,
)

app = FastAPI(title="评估智能体", version="1.0.0")


@app.post("/evaluation/submit", response_model=ApiResponse[EvaluationSubmitData])
async def submit_evaluation(req: EvaluationSubmitRequest, request: Request):
    """
    提交评估数据
    
    请求体（EvaluationSubmitRequest）:
    {
        "sessionId": "sess_abc",
        "quizId": "quiz_01",
        "answers": [
            { "questionId": "q1", "answer": "B", "timeSpent": 45 },
            { "questionId": "q2", "answer": "A", "timeSpent": 30 }
        ],
        "behaviors": [
            { "action": "video_pause", "resourceId": "res_001", "timestamp": "2026-06-15T10:00:00Z" }
        ]
    }
    
    成功响应（ApiResponse[EvaluationSubmitData]）:
    {
        "code": 0,
        "message": "success",
        "data": { "evaluationId": "eval_001", "status": "processing" },
        "requestId": "req_uuid"
    }

    失败响应:
    {
        "code": 1001,
        "message": "参数错误: sessionId 不能为空",
        "data": null,
        "requestId": "req_uuid"
    }
    """
    # 参数校验示例
    if not req.sessionId:
        return error(1001, "参数错误: sessionId 不能为空", request_id=str(request.headers.get("X-Request-Id", "")))
    
    # 处理评估...
    return success(
        EvaluationSubmitData(evaluationId="eval_001", status="processing"),
        request_id=str(request.headers.get("X-Request-Id", ""))
    )
```

#### 5.2.2 获取评估报告 — `GET /sessions/{sessionId}/evaluation-report`

```python
@app.get("/sessions/{sessionId}/evaluation-report", response_model=ApiResponse[EvaluationReport])
async def get_evaluation_report(sessionId: str, request: Request):
    """
    获取评估报告
    
    成功响应（ApiResponse[EvaluationReport]）:
    {
        "code": 0,
        "message": "success",
        "data": {
            "dimensions": [
                { "name": "基础知识掌握", "score": 85, "maxScore": 100 },
                { "name": "理解深度", "score": 70, "maxScore": 100 },
                { "name": "应用能力", "score": 60, "maxScore": 100 },
                { "name": "学习效率", "score": 90, "maxScore": 100 },
                { "name": "专注度", "score": 75, "maxScore": 100 }
            ],
            "weakPoints": [
                { "topic": "注意力机制", "severity": 4, "description": "对 Attention 的 Query/Key/Value 理解不够深入", "suggestion": "建议回顾 CS224n 第 6 讲" }
            ],
            "suggestions": [
                "建议回顾 CS224n 第 6 讲关于 Attention 的内容",
                "推荐完成「动手学深度学习」中反向传播的练习题"
            ],
            "pathAdjustments": [
                { "nodeId": "node_3", "action": "add", "title": "注意力机制专项练习" }
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
    # 查询评估报告逻辑...
    report = await get_report_from_db(sessionId)
    if not report:
        raise HTTPException(status_code=404, detail=error(1002, "会话不存在"))
    return success(report, request_id=str(request.headers.get("X-Request-Id", "")))
```

### 5.3 核心服务方法

```python
# services/evaluator.py

class Evaluator:
    """
    评估引擎
    
    评估维度:
    1. 基础知识掌握 (knowledge_mastery) — 答题正确率
    2. 理解深度 (understanding_depth) — 复杂问题表现
    3. 应用能力 (application_ability) — 能否举一反三
    4. 学习效率 (learning_efficiency) — 单位时间掌握量
    5. 专注度 (engagement) — 行为数据反映的投入程度
    
    数据来源:
    - 答题数据: 正确率、用时
    - 行为数据: 视频暂停/快进/回放、资源浏览时长
    - 对话数据: 提问质量、追问深度
    """

    def __init__(self, llm_service, quiz_grader, behavior_analyzer, weakness_finder):
        self.llm = llm_service
        self.quiz_grader = quiz_grader
        self.behavior_analyzer = behavior_analyzer
        self.weakness_finder = weakness_finder

    async def evaluate(
        self,
        session_id: str,
        answers: List[Answer],
        behaviors: List[Behavior],
        dialogue_history: List[dict]
    ) -> EvaluationResult:
        """
        执行完整评估流程
        
        步骤:
        1. 答题评分 → 知识掌握度得分
        2. 行为分析 → 学习效率 + 专注度得分
        3. 对话分析 → 理解深度得分
        4. 薄弱点发现 → 从错误和对话中提取薄弱知识点
        5. 综合评分 → 各维度加权汇总
        6. 生成建议 → 基于薄弱点推荐改进方向
        7. 路径调整 → 建议需要加强的学习节点
        
        返回: EvaluationResult（包含维度评分、薄弱点、建议、路径调整）
        """
        # 第 1 步: 答题评分
        quiz_result = await self.quiz_grader.grade(answers)
        
        # 第 2 步: 行为分析
        behavior_score = await self.behavior_analyzer.analyze(behaviors)
        
        # 第 3 步: 薄弱点发现
        weak_points = await self.weakness_finder.find(
            quiz_result=quiz_result,
            dialogue_history=dialogue_history
        )
        
        # 第 4 步: 大模型综合评估
        evaluation = await self.llm.generate_evaluation(
            quiz_result=quiz_result,
            behavior_score=behavior_score,
            weak_points=weak_points,
            profile=await self.profile_service.get_profile(session_id)
        )
        
        return evaluation


# services/quiz_grader.py

class QuizGrader:
    """
    答题评分器
    
    支持多种题型评分:
    - 选择题: 直接对比答案
    - 填空题: 关键词匹配 + 语义相似度
    - 简答题: 大模型评分（根据参考答案和评分标准）
    """

    async def grade(self, answers: List[Answer]) -> QuizResult:
        """
        评分逻辑:
        1. 选择题: answer === correct_answer → 正确，否则错误
        2. 简答题: 调用大模型，传入"问题 + 参考答案 + 学生答案" → 返回分数
        
        返回:
        {
            "totalScore": 85,
            "maxScore": 100,
            "details": [
                { "questionId": "q1", "score": 10, "maxScore": 10, "correct": true },
                { "questionId": "q2", "score": 7, "maxScore": 10, "correct": false }
            ],
            "wrongTopics": ["反向传播", "损失函数"]
        }
        """
        pass


# services/weakness_finder.py

class WeaknessFinder:
    """
    薄弱点发现器
    
    从错误答案和对话历史中提取薄弱知识点。
    
    方法:
    1. 统计错误题目的知识点标签
    2. 分析对话中用户反复提问/表现出困惑的主题
    3. 使用大模型对薄弱点进行归因分析
    """

    async def find(
        self,
        quiz_result: QuizResult,
        dialogue_history: List[dict]
    ) -> List[WeakPoint]:
        """
        返回薄弱点列表，每个薄弱点包含:
        - topic: 知识点名称
        - severity: 严重程度 (1-5)
        - description: 具体问题描述
        - suggestion: 改进建议
        """
        pass
```

---

## 6. 任务详解：内容安全与防幻觉模块

### 6.1 内容安全过滤器

```python
# 位置: 可作为独立模块 agents/safety/ 或集成到各智能体中
# 建议作为独立服务，所有智能体统一调用

class ContentSafetyFilter:
    """
    内容安全过滤器
    
    职责：
    对 AI 生成内容进行安全审核，拦截违规内容。
    
    实现方式:
    1. 关键词过滤 — 敏感词库匹配
    2. 大模型审核 — 调用 OpenAI  moderation API
    3. 规则引擎 — 特定模式的拦截规则
    
    触发时机:
    每次智能体生成最终答案前，调用本过滤器
    命中违规 → 返回 code 3001, 推送友好提示
    """

    SENSITIVE_KEYWORDS = [...]  # 敏感词库

    async def check(self, text: str) -> SafetyVerdict:
        """
        审核文本内容
        
        返回:
        {
            "passed": True/False,         # 是否通过审核
            "riskLevel": "safe|suspect|violation",
            "violatedRules": ["规则1", "规则2"],
            "suggestion": "建议修改..."
        }
        """
        # 1. 关键词匹配
        # 2. 大模型审核
        pass
```

### 6.2 防幻觉校验模块

```python
class HallucinationGuard:
    """
    防幻觉校验模块
    
    职责：
    检查模型生成内容是否存在"幻觉"（无根据的虚假信息）。
    
    实现方式:
    1. 引用核查 — 检查引用的论文/资源是否存在
    2. 事实一致性 — 与已知事实对比
    3. 置信度评估 — 对不确定内容进行标注
    
    触发时机:
    资源生成、辅导回答输出前
    命中幻觉 → 返回 code 3002, 推送"暂无法提供准确答案"
    """

    async def check(self, generated_text: str, context: dict) -> HallucinationVerdict:
        """
        校验是否存在幻觉
        
        context 包含:
        - profile: 用户画像（知识水平）
        - source_material: 参考来源（如有）
        - dialogue_history: 对话历史
        
        返回:
        {
            "passed": True/False,
            "hallucinatedClaims": [
                {"claim": "XXX论文证明了...", "evidence": "未找到该论文", "confidence": 0.1}
            ],
            "overallConfidence": 0.85
        }
        
        策略:
        - 如果 generated_text 引用了具体论文/数据/事实:
          → 使用大模型判断该引用是否可能为真实
          → 低置信度引用标记为"疑似幻觉"
        - 对于学术资源生成:
          → 强制要求标注参考来源
          → 无来源标注的内容要求重新生成
        """
        pass
```

---

## 7. 核心数据模型（DTO）

### 7.1 通用 WS 消息 DTO（与人员 A 共享）

```python
# 由 common/ 包提供，这里列出接口定义供参考

class WSClientMessage(BaseModel):
    """客户端 WS 消息帧"""
    msgId: str
    intent: Literal["profile_build", "resource_generate", "tutoring", "path_query", "evaluate"]
    content: MessageContent
    context: Optional[Dict] = None


class MessageContent(BaseModel):
    text: str
    attachments: Optional[List[Attachment]] = None


class Attachment(BaseModel):
    type: str
    url: str
    mimeType: str


class WSServerMessage(BaseModel):
    """服务端 WS 消息帧"""
    msgId: str
    replyTo: str
    intent: str
    type: Literal["text", "resource_card", "progress", "done", "error"]
    content: Dict
```

### 7.2 评估 DTO

```python
from typing import Generic, TypeVar, Optional, List
from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """通用 REST API 响应体"""
    code: int = Field(default=0)
    message: str = Field(default="success")
    data: Optional[T] = None
    requestId: str = Field(default="", description="请求追踪 ID")

def success(data, request_id: str = "") -> dict:
    return {"code": 0, "message": "success", "data": data, "requestId": request_id}

def error(code: int, message: str, request_id: str = "") -> dict:
    return {"code": code, "message": message, "data": None, "requestId": request_id}


# 评估数据模型
class Answer(BaseModel):
    questionId: str
    answer: str
    timeSpent: int  # 秒

class Behavior(BaseModel):
    action: str  # video_pause, video_forward, video_rewind, resource_view
    resourceId: str
    timestamp: str

class EvaluationSubmitRequest(BaseModel):
    sessionId: str
    quizId: str
    answers: List[Answer]
    behaviors: List[Behavior]

# 评估响应数据体（ApiResponse.data 中携带）
class EvaluationSubmitData(BaseModel):
    evaluationId: str
    status: str  # "processing" | "completed"

# 评估响应外层统一使用 ApiResponse[EvaluationSubmitData]
class EvaluationReport(BaseModel):
    name: str
    score: float
    maxScore: float = 100.0

class WeakPoint(BaseModel):
    topic: str
    severity: int = Field(ge=1, le=5)
    description: str
    suggestion: str = ""

class PathAdjustment(BaseModel):
    nodeId: str
    action: Literal["add", "modify", "remove"]
    title: str

class EvaluationReport(BaseModel):
    dimensions: List[EvaluationDimension]
    weakPoints: List[WeakPoint]
    suggestions: List[str]
    pathAdjustments: List[PathAdjustment] = []
```

---

## 8. 开发步骤与 Git 提交计划

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
