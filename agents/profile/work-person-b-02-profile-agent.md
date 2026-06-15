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
