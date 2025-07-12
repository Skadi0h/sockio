from __future__ import annotations

"""Database initialization and connection management using SQLAlchemy."""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from sockio.config import config


class Base(DeclarativeBase):
    pass


class DatabaseManager:
    """Manage PostgreSQL connection."""

    def __init__(self) -> None:
        self.engine = create_async_engine(config.postgres_url, echo=False)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)

    async def init_models(self) -> None:
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        async with self.session_factory() as session:
            yield session

    async def close(self) -> None:
        await self.engine.dispose()


# Global instance
db_manager = DatabaseManager()

__all__ = ["Base", "db_manager", "AsyncSession"]
