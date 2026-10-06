from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings


class Base(DeclarativeBase):
    """Base declarative class for all SQLAlchemy 2.0 models."""
    pass


# Default async engine for standard requests
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    echo=settings.DEBUG,
)

# Bypass engine for Celery/cron tasks crossing tenant or org boundaries
bypass_engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    echo=settings.DEBUG,
)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

bypass_session_factory = async_sessionmaker(
    bind=bypass_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for standard API requests."""
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_bypass_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for background tasks / Celery jobs."""
    async with bypass_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
