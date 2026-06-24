"""画像数据持久化"""

from typing import Optional

from ..config import settings
from ..models.schema import UserProfile

try:
    import sqlalchemy as sa
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker

    HAS_SQLA = True
except ImportError:
    HAS_SQLA = False


class ProfileRepository:
    """画像数据持久化仓库

    提供 UserProfile 的增删改查操作。
    支持异步 SQLAlchemy（可选依赖），当未安装时回退到内存存储。
    """

    def __init__(self):
        self._profiles: dict[str, UserProfile] = {}
        self._engine = None
        self._session_factory = None

        if HAS_SQLA and settings.db_url:
            db_url = settings.db_url
            if db_url.startswith("sqlite:///"):
                db_url = db_url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
            elif db_url.startswith("postgresql://"):
                db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
            self._engine = create_async_engine(db_url, echo=settings.debug)
            self._session_factory = sessionmaker(self._engine, class_=AsyncSession, expire_on_commit=False)

    async def init_db(self) -> None:
        """建表（幂等）。profiles 表存序列化的画像 JSON。

        原代码只用了 profiles 表却从未建表，导致首次查询即 OperationalError。
        """
        if not self._engine:
            return
        async with self._engine.begin() as conn:
            await conn.execute(
                sa.text(
                    "CREATE TABLE IF NOT EXISTS profiles ("
                    "session_id TEXT PRIMARY KEY, "
                    "data TEXT NOT NULL, "
                    "updated_at TEXT NOT NULL"
                    ")"
                )
            )

    async def save(self, profile: UserProfile) -> None:
        """保存或更新画像（upsert）"""
        self._profiles[profile.session_id] = profile
        if self._session_factory:
            await self._db_upsert(profile)

    async def get(self, session_id: str) -> Optional[UserProfile]:
        """根据 session_id 获取画像"""
        if self._session_factory:
            db_profile = await self._db_get(session_id)
            if db_profile:
                return db_profile
        return self._profiles.get(session_id)

    async def delete(self, session_id: str) -> bool:
        """删除指定 session 的画像"""
        existed = session_id in self._profiles
        self._profiles.pop(session_id, None)
        if self._session_factory:
            await self._db_delete(session_id)
        return existed

    async def _db_upsert(self, profile: UserProfile) -> None:
        """数据库 upsert 实现"""
        async with self._session_factory() as session:  # type: ignore
            stmt = sa.text(
                "INSERT INTO profiles (session_id, data, updated_at) "
                "VALUES (:sid, :data, :ts) "
                "ON CONFLICT (session_id) DO UPDATE SET data = :data, updated_at = :ts"
            )
            await session.execute(
                stmt,
                {
                    "sid": profile.session_id,
                    "data": profile.model_dump_json(),
                    "ts": profile.updated_at.isoformat(),
                },
            )
            await session.commit()

    async def _db_get(self, session_id: str) -> Optional[UserProfile]:
        """数据库获取实现"""
        async with self._session_factory() as session:  # type: ignore
            stmt = sa.text("SELECT data FROM profiles WHERE session_id = :sid")
            row = (await session.execute(stmt, {"sid": session_id})).scalar_one_or_none()
            if row:
                return UserProfile.model_validate_json(row)
            return None

    async def _db_delete(self, session_id: str) -> None:
        """数据库删除实现"""
        async with self._session_factory() as session:  # type: ignore
            stmt = sa.text("DELETE FROM profiles WHERE session_id = :sid")
            await session.execute(stmt, {"sid": session_id})
            await session.commit()
