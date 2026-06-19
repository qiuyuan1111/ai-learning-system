"""内容安全与防幻觉智能体 FastAPI 入口

提供:
- POST /safety/check — 内容安全审核
- POST /safety/hallucination-check — 防幻觉校验
- GET /health — 健康检查

错误码:
- 3001: 内容安全违规
- 3002: 检测到幻觉
"""

import logging
from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .config import settings
from .models.dto import (
    ApiResponse,
    HallucinationCheckRequest,
    HallucinationCheckResponse,
    SafetyCheckRequest,
    SafetyCheckResponse,
    error,
    success,
)
from .services.hallucination_guard import HallucinationGuard
from .services.llm_service import LLMService
from .services.profile_service_client import ProfileServiceClient
from .services.safety_filter import ContentSafetyFilter

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

llm_service: LLMService
safety_filter: ContentSafetyFilter
hallucination_guard: HallucinationGuard
profile_client: ProfileServiceClient


@asynccontextmanager
async def lifespan(app: FastAPI):
    global llm_service, safety_filter, hallucination_guard, profile_client
    logger.info("正在初始化内容安全与防幻觉智能体...")
    settings.validate()
    llm_service = LLMService()
    profile_client = ProfileServiceClient()
    safety_filter = ContentSafetyFilter(llm_service=llm_service)
    hallucination_guard = HallucinationGuard(llm_service=llm_service)
    logger.info("安全智能体已启动: %s:%s, model=%s", settings.host, settings.port, settings.llm_model)
    yield
    await profile_client.close()
    logger.info("安全智能体已关闭")


app = FastAPI(title="内容安全与防幻觉智能体 (Safety Guard Agent)", version="1.0.0", lifespan=lifespan)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("未预期的错误: %s", exc)
    request_id = str(request.headers.get("X-Request-Id", ""))
    return JSONResponse(status_code=500, content=error(9999, "服务器内部错误", request_id).model_dump())


@app.get("/health")
async def health_check() -> Dict[str, str]:
    ps_ok = await profile_client.health_check()
    return {
        "status": "ok" if ps_ok else "degraded",
        "service": "safety-agent",
        "profile_service": "connected" if ps_ok else "unavailable",
    }


@app.post("/safety/check", response_model=ApiResponse[SafetyCheckResponse])
async def safety_check(req: SafetyCheckRequest, request: Request):
    request_id = str(request.headers.get("X-Request-Id", ""))
    if not req.text.strip():
        return error(1001, "参数错误: text 不能为空", request_id)
    logger.info("收到安全审核请求: text_len=%d, source=%s", len(req.text), req.source)
    result = await safety_filter.check(text=req.text, context=req.context, source=req.source)
    response_data = SafetyCheckResponse(
        passed=result.verdict.passed, riskLevel=result.verdict.riskLevel,
        violatedRules=result.verdict.violatedRules, suggestion=result.verdict.suggestion,
        filterResults=result,
    )
    if not result.verdict.passed:
        logger.warning("安全审核未通过: riskLevel=%s", result.verdict.riskLevel)
        return error(3001, result.verdict.suggestion or "内容审核未通过", request_id)
    if result.verdict.riskLevel == "suspect":
        logger.info("安全审核通过（含风险）")
    return success(response_data, request_id=request_id)


@app.post("/safety/hallucination-check", response_model=ApiResponse[HallucinationCheckResponse])
async def hallucination_check(req: HallucinationCheckRequest, request: Request):
    request_id = str(request.headers.get("X-Request-Id", ""))
    if not req.text.strip():
        return error(1001, "参数错误: text 不能为空", request_id)
    logger.info("收到防幻觉校验请求: text_len=%d", len(req.text))
    result = await hallucination_guard.check(
        text=req.text, session_id=req.sessionId,
        source_material=req.sourceMaterial, dialogue_history=req.dialogueHistory or [],
    )
    response_data = HallucinationCheckResponse(
        passed=result.verdict.passed, overallConfidence=result.verdict.overallConfidence,
        hallucinatedClaims=[c.model_dump() for c in result.verdict.hallucinatedClaims],
        suggestion=result.suggestion, guardResult=result.verdict,
    )
    if not result.verdict.passed:
        logger.warning("防幻觉校验未通过: confidence=%s", result.verdict.overallConfidence)
        return error(3002, result.verdict.suggestion or "暂无法提供准确答案", request_id)
    logger.info("防幻觉校验通过: confidence=%s", result.verdict.overallConfidence)
    return success(response_data, request_id=request_id)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host=settings.host, port=settings.port, reload=settings.debug, log_level="info")
