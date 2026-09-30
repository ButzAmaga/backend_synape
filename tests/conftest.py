"""
Purpose: Configures shared Pytest fixtures for async testing with isolated SQLite database and HTTP client.
Flow:
      1. Create temporary in-memory/isolated SQLite engine for testing.
      2. Override FastAPI get_db dependency to use test session.
      3. Instantiate AsyncClient hooked to FastAPI application instance.
Inputs: Pytest test runner environment.
Outputs: Async database session and HTTP client fixtures.
"""

import pytest
import pytest_asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.main import app
from app.core.database import Base, get_db

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine_test = create_async_engine(
    TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = async_sessionmaker(
    bind=engine_test, class_=AsyncSession, expire_on_commit=False
)


@pytest_asyncio.fixture(autouse=True)
async def setup_test_db():
    """
    Purpose: Creates fresh database tables before each test and drops them afterwards.
    Flow:
          1. Issue create_all schema generation.
          2. Yield control to running test case.
          3. Issue drop_all schema tear down.
    Inputs: None.
    Outputs: None.
    """
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Purpose: Yields an isolated async SQLAlchemy session for direct repository tests.
    Flow:
          1. Instantiate testing session.
          2. Yield session instance.
          3. Rollback uncommitted transactions upon completion.
    Inputs: None.
    Outputs: AsyncSession instance for database queries.
    """
    async with TestingSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Purpose: Provides an AsyncClient configured with test database dependency overrides.
    Flow:
          1. Override get_db app dependency with db_session fixture.
          2. Instantiate httpx AsyncClient wrapping FastAPI application.
          3. Reset app dependency overrides on teardown.
    Inputs: db_session (AsyncSession).
    Outputs: AsyncClient HTTP instance.
    """

    async def _get_test_db():
        yield db_session

    app.dependency_overrides[get_db] = _get_test_db

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()

@pytest.fixture(autouse=True)
def use_test_session_factory(monkeypatch):
    """
    Purpose: Sets up test session factory for pipeline services.
    Flow:
          1. Override async session factory for pipeline services.
    Inputs: monkeypatch (pytest.MonkeyPatch).
    Outputs: None.
    """
    monkeypatch.setattr("app.core.pipeline.async_session_factory", TestingSessionLocal)
    monkeypatch.setattr("app.services.pipeline_service.async_session_factory", TestingSessionLocal)