"""FastAPI 入口 + WebSocket 端点"""

from contextlib import asynccontextmanager
from typing import Dict, Any
import uuid

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, status

from .config import settings
from .services.llm_service import LLMService
from .services.profile_builder import ProfileBuilder
from .services.profile_updater import ProfileUpdater
from .db.repository import ProfileRepository
from .db.memory import DialogueMemory
from .ws.handler import ProfileWSHandler


# 全局依赖（在 lifespan 中初始化）
llm_service: LLMService = None  # type: ignore
profile_builder: ProfileBuilder = None  # type: ignore
profile_updater: ProfileUpdater = None  # type: ignore
profile_repo: ProfileRepository = None  # type: ignore
dialogue_memory: DialogueMemory = None  # type: ignore
ws_handler: ProfileWSHandler = None  # type: ignore


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时初始化依赖，关闭时清理"""
    global llm_service, profile_builder, profile_updater
    global profile_repo, dialogue_memory, ws_handler

    # 校验配置
    settings.validate()

    # 初始化依赖
    llm_service = LLMService()
    profile_builder = ProfileBuilder(llm_service)
    profile_updater = ProfileUpdater(llm_service)
    profile_repo = ProfileRepository()
    dialogue_memory = DialogueMemory(max_size=settings.dialogue_history_size)
    ws_handler = ProfileWSHandler(profile_builder, profile_updater, profile_repo, dialogue_memory)

    yield

    # 清理资源


app = FastAPI(
    title="Friendly Tutor - Profile Agent",
    description="用户画像智能体服务",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """健康检查端点"""
    return {"status": "ok", "service": "profile-agent"}


@app.websocket("/ws/chat")
async def websocket_chat(ws: WebSocket):
    """WebSocket 聊天端点

    接收 JSON 消息帧，处理 intent=profile_build / profile_update 的消息。
    通过查询参数 ?session_id=<uuid> 标识会话身份。
    """
    await ws.accept()

    # 从查询参数获取 session_id，缺省时自动生成
    session_id = ws.query_params.get("session_id") or f"session_{uuid.uuid4().hex[:12]}"

    try:
        while True:
            raw = await ws.receive_text()
            frames = await ws_handler.handle_message(raw, session_id)

            for frame in frames:
                await ws.send_json(frame)

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await ws.send_json({
                "msgId": "",
                "replyTo": "",
                "intent": "profile_build",
                "type": "error",
                "content": {"code": "internal_error", "detail": str(e)},
            })
        except Exception:
            pass


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
