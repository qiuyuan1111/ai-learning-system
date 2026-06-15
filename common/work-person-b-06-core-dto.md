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
