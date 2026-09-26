"""
Purpose: Manages asynchronous SQLite engine creation, session factory, and database initialization.
Flow:
      1. Create asynchronous SQLAlchemy engine configured with a 30s busy timeout.
      2. Bind async session factory for dependency injection.
      3. Enable SQLite Write-Ahead Logging (WAL) and synchronous modes on startup using SQLAlchemy text().
      4. Provide async generator yielding scoped database sessions.
Inputs: DATABASE_URL and settings from app.core.config.
Outputs: Exposes init_db startup routine and get_db session dependency.
"""

from typing import AsyncGenerator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    connect_args={
        "timeout": 30,  # 30-second busy timeout to prevent database locks
    },
    echo=settings.DEBUG,
)

async_session_factory = async_sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)


class Base(DeclarativeBase):
    """
    Purpose: Declarative base class for ORM model mapping.
    Flow:
          1. Serve as root base class for all SQLAlchemy domain models.
    Inputs: None.
    Outputs: Base ORM declarative instance.
    """
    pass


async def init_db() -> None:
    """
    Purpose: Configures SQLite PRAGMA execution and initializes database schema.
    Flow:
          1. Acquire direct database connection handle from engine context.
          2. Execute PRAGMA journal_mode=WAL wrapped in text() construct.
          3. Execute PRAGMA synchronous=NORMAL wrapped in text() construct.
          4. Run synchronous table schema creation for all registered ORM models.
    Inputs: None.
    Outputs: None.
    """
    async with engine.begin() as conn:
        await conn.execute(text("PRAGMA journal_mode=WAL;"))
        await conn.execute(text("PRAGMA synchronous=NORMAL;"))
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Purpose: Yields asynchronous database session context for HTTP request execution.
    Flow:
          1. Instantiate new AsyncSession from global session factory.
          2. Yield session handle to API controller/service layer.
          3. Automatically close session upon HTTP request lifecycle completion.
    Inputs: None.
    Outputs: AsyncGenerator yielding active AsyncSession object.
    """
    async with async_session_factory() as session:
        yield session