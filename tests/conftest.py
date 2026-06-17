import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.db import AsyncSessionLocal
from app.main import app


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


@pytest_asyncio.fixture(autouse=True)
async def clean_database():
    async with AsyncSessionLocal() as db:
        await db.execute(text("DELETE FROM task_history"))
        await db.execute(text("DELETE FROM comments"))
        await db.execute(text("DELETE FROM tasks"))
        await db.execute(text("DELETE FROM users"))
        await db.commit()
