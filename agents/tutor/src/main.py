"""
辅导智能体 FastAPI 入口

提供:
- WebSocket 端点 /ws/chat （处理 intent=tutoring）
- REST 端点 /health （健康检查）
"""

import json
import logging
import uuid
from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from src.config import config
from src.db.chat_history import ChatHistoryStore
from src.services.llm_service import LLMService
from src.services.answer_generator import AnswerGenerator
from src.services.context_manager import ContextManager
from src.services.profile_service_client import ProfileServiceClient
from src.services.tutor_engine import TutorEngine
from src.ws.handler import TutorWSHandler

# ── 日志配置 ────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# ── 全局服务实例 ────────────────────────────────────────────────

llm_service: LLMService
profile_client: ProfileServiceClient
chat_store: ChatHistoryStore
context_manager: ContextManager
answer_generator: AnswerGenerator
tutor_engine: TutorEngine
ws_handler: TutorWSHandler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global llm_service, profile_client, chat_store
    global context_manager, answer_generator, tutor_engine, ws_handler

    logger.info("正在初始化辅导智能体服务...")

    # 初始化各层服务
    llm_service = LLMService()
    profile_client = ProfileServiceClient()
    chat_store = ChatHistoryStore()
    context_manager = ContextManager(
        store=chat_store,
        llm_service=llm_service,
    )
    answer_generator = AnswerGenerator(llm_service=llm_service)
    tutor_engine = TutorEngine(
        llm_service=llm_service,
        profile_service=profile_client,
        answer_generator=answer_generator,
        context_manager=context_manager,
    )
    ws_handler = TutorWSHandler(tutor_engine=tutor_engine)

    logger.info(
        "辅导智能体已启动: %s:%s, model=%s",
        config.host,
        config.port,
        config.llm_model,
    )

    yield

    logger.info("辅导智能体已关闭")


# ── FastAPI 应用 ─────────────────────────────────────────────────

app = FastAPI(
    title="辅导智能体 (Tutor Agent)",
    version="1.0.0",
    lifespan=lifespan,
)


# ── REST 端点 ────────────────────────────────────────────────────


class HealthResponse(BaseModel):
    status: str
    model: str
    profile_service: bool


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查"""
    ps_ok = await profile_client.health_check()
    return HealthResponse(
        status="ok",
        model=config.llm_model,
        profile_service=ps_ok,
    )


@app.get("/sessions/{session_id}/stats")
async def session_stats(session_id: str):
    """获取会话统计信息"""
    context = await context_manager.get_context(session_id)
    return {
        "session_id": session_id,
        "total_rounds": context.total_rounds(),
        "recent_rounds": len(context.rounds),
        "has_summary": context.summary is not None,
    }


# ── WebSocket 端点 ──────────────────────────────────────────────


@app.websocket("/ws/chat")
async def websocket_chat(ws: WebSocket):
    """
    WebSocket 聊天端点

    接收 intent=tutoring 的消息，返回个性化辅导回答。

    消息协议:
        客户端 → { "msgId": "uuid", "intent": "tutoring",
                   "content": { "text": "问题", "attachments": [...] },
                   "context": { "resourceId": "...", "courseId": "..." } }
        服务端 → { "msgId": "uuid", "replyTo": "原msgId", "intent": "tutoring",
                   "type": "text|progress|done|error", "content": {...} }

    路径参数:
        session_id (query): 会话 ID，必填
    """
    await ws.accept()

    # 获取会话 ID
    session_id = ws.query_params.get("session_id", "")
    if not session_id:
        await ws.send_json({
            "msgId": str(uuid.uuid4()),
            "replyTo": "",
            "intent": "tutoring",
            "type": "error",
            "content": {"code": "MISSING_SESSION_ID", "message": "缺少 session_id 参数"},
        })
        await ws.close(code=4000)
        return

    logger.info("WS 连接建立: session=%s", session_id)

    try:
        while True:
            # 接收客户端消息
            raw_text = await ws.receive_text()
            raw_data = json.loads(raw_text)

            # 校验
            error = ws_handler.validate_message(raw_data)
            if error:
                await ws.send_json({
                    "msgId": str(uuid.uuid4()),
                    "replyTo": raw_data.get("msgId", ""),
                    "intent": "tutoring",
                    "type": "error",
                    "content": {"code": "VALIDATION_ERROR", "message": error},
                })
                continue

            # 处理消息（逐段推送）
            async for server_msg in ws_handler.handle_message(raw_data, session_id):
                await ws.send_json(server_msg.model_dump())

    except WebSocketDisconnect:
        logger.info("WS 断开: session=%s", session_id)
    except json.JSONDecodeError:
        await ws.send_json({
            "msgId": str(uuid.uuid4()),
            "replyTo": "",
            "intent": "tutoring",
            "type": "error",
            "content": {"code": "INVALID_JSON", "message": "消息格式错误，请发送合法的 JSON"},
        })
    except Exception as e:
        logger.exception("WS 处理异常: session=%s", session_id)
        try:
            await ws.send_json({
                "msgId": str(uuid.uuid4()),
                "replyTo": "",
                "intent": "tutoring",
                "type": "error",
                "content": {"code": "INTERNAL_ERROR", "message": "服务内部错误，请稍后重试"},
            })
        except Exception:
            pass
    finally:
        logger.info("WS 连接关闭: session=%s", session_id)


# ── 入口 ────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=config.host,
        port=config.port,
        reload=False,
        log_level="info",
    )
