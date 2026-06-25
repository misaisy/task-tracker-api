import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.settings import settings
from app.dependencies import get_db
from app.main import app
from app.models.orm import Base, User
from app.services.user_service import UserService

test_engine = create_async_engine(
    settings.TEST_DATABASE_URL,
    poolclass=NullPool,
)

TestAsyncSession = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest_asyncio.fixture
async def db_session():
    async with test_engine.connect() as connection:

        transaction = await connection.begin()

        session = AsyncSession(
            bind=connection,
            expire_on_commit=False,
        )

        nested = await connection.begin_nested()

        @event.listens_for(session.sync_session, "after_transaction_end")
        def restart_savepoint(session_, transaction_):
            nonlocal nested

            if not nested.is_active:
                nested = connection.sync_connection.begin_nested()

        yield session

        await session.close()
        await transaction.rollback()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest_asyncio.fixture
async def client(db_session):

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
async def auth_headers(client):
    """Создаёт обычного пользователя и возвращает заголовок с его токеном."""
    username = f"test_{uuid.uuid4().hex[:8]}"
    await client.post("/auth/register", json={
        "username": username,
        "email": f"{username}@test.com",
        "password": "testpass",
    })
    login_resp = await client.post("/auth/login", data={
        "username": username,
        "password": "testpass",
    })
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def auth_user(client):
    username = f"test_{uuid.uuid4().hex[:8]}"
    register_resp = await client.post(
        "/auth/register",
        json={
            "username": username,
            "email": f"{username}@test.com",
            "password": "testpass",
        },
    )
    login_resp = await client.post(
        "/auth/login",
        data={
            "username": username,
            "password": "testpass",
        },
    )
    token = login_resp.json()["access_token"]
    return {
        "id": register_resp.json()["id"],
        "username": username,
        "password": "testpass",
        "headers": {
            "Authorization": f"Bearer {token}"
        },
    }


@pytest.fixture
async def admin_headers(client, db_session):
    """Создаёт админа через БД и возвращает заголовок с его токеном."""
    username = f"admin_{uuid.uuid4().hex[:8]}"
    user = User(
        username=username,
        email=f"{username}@test.com",
        password_hash=UserService.hash_password("adminpass"),
        role="admin",
    )

    db_session.add(user)
    await db_session.commit()

    login_resp = await client.post("/auth/login", data={
        "username": username,
        "password": "adminpass",
    })
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def other_headers(client):
    """Создаёт другого обычного пользователя и возвращает заголовок с его токеном."""
    username = f"test_{uuid.uuid4().hex[:8]}"
    register_resp = await client.post("/auth/register", json={
        "username": username,
        "email": f"{username}@test.com",
        "password": "otherpass",
    })
    assert register_resp.status_code == 201

    login_resp = await client.post("/auth/login", data={
        "username": username,
        "password": "otherpass",
    })
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
