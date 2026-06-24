import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.settings import settings
from app.dependencies import get_db
from app.main import app
from app.models.orm import Base

test_engine = create_async_engine(
    settings.TEST_DATABASE_URL,
    poolclass=NullPool,
)

TestAsyncSession = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def override_get_db():
    async with TestAsyncSession() as session:
        yield session


@pytest.fixture(scope="session", autouse=True)
async def setup_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest.fixture
async def client():
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


@pytest_asyncio.fixture(autouse=True)
async def cleanup_db():
    yield
    async with TestAsyncSession() as session:
        for table in ("task_history", "comments", "tasks", "users"):
            await session.execute(text(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE"))
        await session.commit()


@pytest.fixture
async def auth_headers(client):
    """Создаёт обычного пользователя и возвращает заголовок с его токеном."""
    await client.post(
        "/users/",
        json={"username": "testuser", "email": "test@test.com"},
    )
    login_resp = await client.post("/auth/login?username=testuser")
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def admin_headers(client):
    """Создаёт админа и возвращает заголовок с его токеном."""
    create_resp = await client.post(
        "/users/",
        json={"username": "admintest", "email": "admin@test.com"},
    )
    user_id = create_resp.json()["id"]

    async with TestAsyncSession() as session:
        await session.execute(
            text("UPDATE users SET role = 'admin' WHERE id = :user_id"),
            {"user_id": user_id},
        )
        await session.commit()

    login_resp = await client.post("/auth/login?username=admintest")
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
