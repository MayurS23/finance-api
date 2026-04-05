"""
Test configuration.

Uses an in-memory SQLite database so no real PostgreSQL is needed to run tests.
The app DATABASE_URL is overridden before any imports happen via env var.
"""
import os

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["SECRET_KEY"]   = "test-secret-key"

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app

# ── In-memory SQLite engine ────────────────────────────────────────────────────

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DB_URL, echo=False)
TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


# ── Override the get_db dependency ────────────────────────────────────────────

async def override_get_db():
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


app.dependency_overrides[get_db] = override_get_db


# ── Session-scoped setup ───────────────────────────────────────────────────────

@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_test_tables():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client() -> AsyncClient:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def admin_client(client: AsyncClient) -> AsyncClient:
    """Returns an AsyncClient pre-authenticated as an admin user."""
    # Register (first user → auto-admin)
    await client.post("/auth/register", json={
        "name": "Test Admin",
        "email": "admin@test.com",
        "password": "adminpassword",
        "role": "admin",
    })
    resp = await client.post("/auth/login", json={
        "email": "admin@test.com",
        "password": "adminpassword",
    })
    token = resp.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client
