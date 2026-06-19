"""评估数据持久化

提供评估结果和提交数据的增删改查操作。
支持异步 SQLAlchemy（可选依赖），当未安装时回退到内存存储。
"""

import json
import logging
from typing import Any, Dict, List, Optional

from ..config import settings
from ..models.evaluation import Answer, Behavior, EvaluationResult

logger = logging.getLogger(__name__)

try:
    import sqlalchemy as sa
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker

    HAS_SQLA = True
except ImportError:
    HAS_SQLA = False


# 建表 DDL（跨数据库兼容）
_DDL_SUBMISSIONS = """
CREATE TABLE IF NOT EXISTS submissions (
    evaluation_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    data TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
)
"""

_DDL_REPORTS = """
CREATE TABLE IF NOT EXISTS reports (
    session_id TEXT PRIMARY KEY,
    data TEXT NOT NULL,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
)
"""


class EvaluationRepository:
    """评估数据持久化仓库

    提供评估提交和评估结果的存储。
    支持异步 SQLAlchemy（可选依赖），当未安装时回退到内存存储。
    """

    def __init__(self):
        # 内存存储
        self._submissions: Dict[str, dict] = {}
        self._reports: Dict[str, EvaluationResult] = {}
        self._initialized = False

        # 数据库引擎
        self._engine = None
        self._session_factory = None

        if HAS_SQLA and settings.db_url:
            db_url = settings.db_url
            if db_url.startswith("sqlite:///"):
                db_url = db_url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
            elif db_url.startswith("postgresql://"):
                db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
            self._engine = create_async_engine(db_url, echo=settings.debug)
            self._session_factory = sessionmaker(
                self._engine, class_=AsyncSession, expire_on_commit=False,
            )

    async def _ensure_tables(self) -> None:
        """确保数据库表已创建（仅执行一次）"""
        if not self._session_factory or self._initialized:
            return
        async with self._session_factory() as session:
            for ddl in (_DDL_SUBMISSIONS, _DDL_REPORTS):
                await session.execute(sa.text(ddl))
            await session.commit()
        self._initialized = True

    async def save_submission(
        self,
        session_id: str,
        evaluation_id: str,
        answers: List[Answer],
        behaviors: List[Behavior],
    ) -> None:
        """保存评估提交数据"""
        data = {
            "sessionId": session_id,
            "evaluationId": evaluation_id,
            "answers": [a.model_dump() for a in answers],
            "behaviors": [b.model_dump() for b in behaviors],
        }
        self._submissions[evaluation_id] = data
        if self._session_factory:
            await self._ensure_tables()
            await self._db_insert_submission(evaluation_id, data)

    async def get_submission(self, evaluation_id: str) -> Optional[dict]:
        """获取评估提交数据"""
        if self._session_factory:
            db_sub = await self._db_get_submission(evaluation_id)
            if db_sub:
                return db_sub
        return self._submissions.get(evaluation_id)

    async def save_report(self, session_id: str, report: EvaluationResult) -> None:
        """保存评估报告"""
        self._reports[session_id] = report
        if self._session_factory:
            await self._ensure_tables()
            await self._db_upsert_report(session_id, report)

    async def get_report(self, session_id: str) -> Optional[EvaluationResult]:
        """获取评估报告"""
        if self._session_factory:
            if not self._initialized:
                await self._ensure_tables()
            db_report = await self._db_get_report(session_id)
            if db_report:
                return db_report
        return self._reports.get(session_id)

    # ── 数据库操作 ──────────────────────────────────────────────

    async def _db_insert_submission(self, evaluation_id: str, data: dict) -> None:
        async with self._session_factory() as session:  # type: ignore
            stmt = sa.text(
                "INSERT INTO submissions (evaluation_id, session_id, data, created_at) "
                "VALUES (:eid, :sid, :data, CURRENT_TIMESTAMP)"
            )
            await session.execute(stmt, {
                "eid": evaluation_id,
                "sid": data["sessionId"],
                "data": json.dumps(data, ensure_ascii=False),
            })
            await session.commit()

    async def _db_get_submission(self, evaluation_id: str) -> Optional[dict]:
        async with self._session_factory() as session:  # type: ignore
            stmt = sa.text("SELECT data FROM submissions WHERE evaluation_id = :eid")
            row = (await session.execute(stmt, {"eid": evaluation_id})).scalar_one_or_none()
            if row:
                return json.loads(row)
            return None

    async def _db_upsert_report(self, session_id: str, report: EvaluationResult) -> None:
        async with self._session_factory() as session:  # type: ignore
            stmt = sa.text(
                "INSERT INTO reports (session_id, data, updated_at) "
                "VALUES (:sid, :data, CURRENT_TIMESTAMP) "
                "ON CONFLICT (session_id) DO UPDATE SET data = :data, updated_at = CURRENT_TIMESTAMP"
            )
            await session.execute(stmt, {
                "sid": session_id,
                "data": report.model_dump_json(),
            })
            await session.commit()

    async def _db_get_report(self, session_id: str) -> Optional[EvaluationResult]:
        async with self._session_factory() as session:  # type: ignore
            stmt = sa.text("SELECT data FROM reports WHERE session_id = :sid")
            row = (await session.execute(stmt, {"sid": session_id})).scalar_one_or_none()
            if row:
                return EvaluationResult.model_validate_json(row)
            return None
