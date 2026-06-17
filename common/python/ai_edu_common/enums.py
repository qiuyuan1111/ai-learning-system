"""枚举定义 —— 与 TS 版 @ai-edu/common 严格对应（见 work-person-c.md 3.3）。

使用 Python 的 Enum + str 混入，保证序列化为 JSON 时输出字符串字面量值。
"""
from __future__ import annotations

from enum import Enum


class StrEnumBase(str, Enum):
    """字符串枚举基类：既保留枚举约束，又能像字符串一样直接用作 JSON 值。"""

    def __str__(self) -> str:  # 便于日志打印
        return self.value


class IntentEnum(StrEnumBase):
    """意图枚举（WS 聊天帧 intent 字段）。"""

    PROFILE_BUILD = "profile_build"
    RESOURCE_GENERATE = "resource_generate"
    TUTORING = "tutoring"
    PATH_QUERY = "path_query"
    EVALUATE = "evaluate"


class ResourceTypeEnum(StrEnumBase):
    """资源类型枚举（赛题要求至少 5 种）。"""

    PPT = "ppt"
    PDF = "pdf"
    DOC = "doc"
    MINDMAP = "mindmap"
    VIDEO = "video"


class TaskStatusEnum(StrEnumBase):
    """异步任务状态枚举。"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class PathNodeStatusEnum(StrEnumBase):
    """学习路径节点状态枚举。"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class ErrorCodeEnum(int, Enum):
    """业务错误码枚举（与 api.md 3.2 一致）。

    编号段：1xxx 请求/会话层；2xxx 资源生成；3xxx 安全/防幻觉；
           4xxx 智能体超时；5xxx 系统未知。
    """

    SUCCESS = 0
    PARAM_ERROR = 1001
    SESSION_NOT_FOUND = 1002
    TASK_NOT_FOUND = 2001
    RESOURCE_GEN_FAILED = 2002
    CONTENT_SAFETY_VIOLATION = 3001
    HALLUCINATION_DETECTED = 3002
    AGENT_TIMEOUT = 4001
    UNKNOWN_ERROR = 5000
