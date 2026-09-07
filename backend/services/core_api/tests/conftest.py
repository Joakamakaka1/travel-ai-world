from typing import AsyncGenerator
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from core_api.main import app
from core_api.db.session import get_db
from core_api import (
    models,  # noqa: F401 — registers models with Base.metadata
)
from core_api.models.base import Base
from core_api.config import settings

from sqlalchemy.pool import NullPool

# Test database URL (using real PostgreSQL for full type support)
TEST_DB_NAME = f"{settings.DB_NAME}_test"
TEST_SQLALCHEMY_DATABASE_URI = f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_SERVER}:{settings.DB_PORT}/{TEST_DB_NAME}"

# Engine for dynamically creating the test DB (connects to default 'postgres' db)
setup_engine = create_async_engine(
    f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_SERVER}:{settings.DB_PORT}/postgres",
    isolation_level="AUTOCOMMIT",
    poolclass=NullPool,
)

engine_test = create_async_engine(TEST_SQLALCHEMY_DATABASE_URI, poolclass=NullPool)
AsyncSessionTest = async_sessionmaker(
    bind=engine_test, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(scope="session")
async def setup_db():
    # 1. Create the test database if it doesn't exist
    async with setup_engine.begin() as conn:
        result = await conn.execute(
            text(f"SELECT 1 FROM pg_database WHERE datname='{TEST_DB_NAME}'")
        )
        if not result.scalar():
            await conn.execute(text(f"CREATE DATABASE {TEST_DB_NAME}"))

    # Wait for the DB to be ready and clear previous tables
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield

    # 3. Drop all tables after tests finish
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session(setup_db) -> AsyncGenerator[AsyncSession, None]:
    """A session per test, and an empty database when the test is over."""
    async with AsyncSessionTest() as session:
        yield session

    async with engine_test.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    # Override get_db dependency
    async def _get_test_db():
        yield db_session

    app.dependency_overrides[get_db] = _get_test_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
