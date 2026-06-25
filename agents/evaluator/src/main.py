"""评估智能体 FastAPI 入口

提供:
- POST /evaluation/submit — 提交评估数据，触发评估流程
- GET /sessions/{sessionId}/evaluation-report — 获取评估报告
- GET /health — 健康检查
"""

import asyncio
import logging
import uuid
from contextlib import asynccontextmanager
from typing import Dict, List

from fastapi import FastAPI, HTTPException, Request

from .config import settings
from .db.repository import EvaluationRepository
from .models.dto import (
    ApiResponse,
    EvaluationReport,
    EvaluationSubmitData,
    EvaluationSubmitRequest,
    error,
    success,
)
from .services.behavior_analyzer import BehaviorAnalyzer
from .services.evaluator import Evaluator
from .services.llm_service import LLMService
from .services.profile_service_client import ProfileServiceClient
from .services.quiz_grader import QuizGrader
from .services.weakness_finder import WeaknessFinder

# ── 日志配置 ────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# ── 全局服务实例 ────────────────────────────────────────────────

llm_service: LLMService
quiz_grader: QuizGrader
behavior_analyzer: BehaviorAnalyzer
weakness_finder: WeaknessFinder
profile_client: ProfileServiceClient
evaluator: Evaluator
repository: EvaluationRepository


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global llm_service, quiz_grader, behavior_analyzer
    global weakness_finder, profile_client, evaluator, repository

    logger.info("正在初始化评估智能体服务...")

    # 校验配置
    settings.validate()

    # 初始化各层服务
    llm_service = LLMService()
    quiz_grader = QuizGrader(llm_service)
    behavior_analyzer = BehaviorAnalyzer()
    weakness_finder = WeaknessFinder(llm_service)
    profile_client = ProfileServiceClient()
    repository = EvaluationRepository()

    evaluator = Evaluator(
        llm_service=llm_service,
        quiz_grader=quiz_grader,
        behavior_analyzer=behavior_analyzer,
        weakness_finder=weakness_finder,
        profile_service=profile_client,
    )

    logger.info("评估智能体已启动: %s:%s, model=%s", settings.host, settings.port, settings.llm_model)

    yield

    logger.info("评估智能体已关闭")


# ── FastAPI 应用 ─────────────────────────────────────────────────

app = FastAPI(
    title="评估智能体 (Evaluator Agent)",
    version="1.0.0",
    lifespan=lifespan,
)


# ── REST 端点 ────────────────────────────────────────────────────


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """健康检查

    验证服务自身状态及关键下游服务（画像服务）的连通性。
    """
    ps_ok = await profile_client.health_check()
    return {
        "status": "ok" if ps_ok else "degraded",
        "service": "evaluator-agent",
        "profile_service": ps_ok,
    }


@app.post("/evaluation/submit", response_model=ApiResponse[EvaluationSubmitData])
async def submit_evaluation(req: EvaluationSubmitRequest, request: Request):
    """提交评估数据

    处理答题数据和行为数据，执行异步评估流程。

    请求参数:
    - sessionId: 会话 ID（必填）
    - quizId: 测验 ID
    - answers: 答题数据列表
    - behaviors: 行为数据列表

    返回:
    - evaluationId: 评估 ID
    - status: 处理状态
    """
    request_id = str(request.headers.get("X-Request-Id", ""))
    msg = ""

    # 参数校验
    if not req.sessionId:
        msg = "参数错误: sessionId 不能为空"
        logger.warning("提交评估失败: %s", msg)
        return error(1001, msg, request_id)

    if not req.answers and not req.behaviors:
        msg = "参数错误: answers 和 behaviors 不能同时为空"
        logger.warning("提交评估失败: %s", msg)
        return error(1003, msg, request_id)

    # 生成评估 ID 并保存提交
    evaluation_id = f"eval_{uuid.uuid4().hex[:12]}"
    await repository.save_submission(
        session_id=req.sessionId,
        evaluation_id=evaluation_id,
        answers=req.answers,
        behaviors=req.behaviors,
    )

    # 异步执行评估（不阻塞响应）
    # 实际生产环境建议放入任务队列（如 Celery / Redis Queue）
    asyncio.create_task(_run_evaluation_in_background(
        session_id=req.sessionId,
        answers=req.answers,
        behaviors=req.behaviors,
    ))

    logger.info("评估提交成功: session=%s, evaluationId=%s", req.sessionId, evaluation_id)

    return success(
        EvaluationSubmitData(evaluationId=evaluation_id, status="processing"),
        request_id=request_id,
    )


async def _run_evaluation_in_background(
    session_id: str,
    answers: List,
    behaviors: List,
) -> None:
    """后台执行评估流程并保存结果"""
    try:
        # 对话历史当前为空（由外部系统通过其他方式记录）
        dialogue_history: List[Dict] = []

        result = await evaluator.evaluate(
            session_id=session_id,
            answers=answers,
            behaviors=behaviors,
            dialogue_history=dialogue_history,
        )

        await repository.save_report(session_id, result)
        logger.info("后台评估完成: session=%s", session_id)
    except Exception as e:
        logger.exception("后台评估失败: session=%s, error=%s", session_id, e)


@app.get(
    "/sessions/{sessionId}/evaluation-report",
    response_model=ApiResponse[EvaluationReport],
)
async def get_evaluation_report(sessionId: str, request: Request):
    """获取评估报告

    根据 sessionId 查询评估结果。
    如果评估仍在进行中，返回 processing 状态。

    参数:
    - sessionId: 会话 ID（路径参数）

    返回: 评估报告（含维度评分、薄弱点、建议、路径调整）
    """
    request_id = str(request.headers.get("X-Request-Id", ""))

    if not sessionId:
        return error(1001, "参数错误: sessionId 不能为空", request_id)

    report = await repository.get_report(sessionId)

    if not report:
        # 检查是否有提交记录（正在处理中）
        # 简化处理：只要没有报告就返回 404
        raise HTTPException(
            status_code=404,
            detail=error(1002, "评估报告不存在或仍在处理中", request_id).model_dump(),
        )

    return success(
        EvaluationReport(
            dimensions=report.dimensions,
            weakPoints=report.weakPoints,
            suggestions=report.suggestions,
            pathAdjustments=report.pathAdjustments,
        ),
        request_id=request_id,
    )


# ── 入口 ────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info",
    )
