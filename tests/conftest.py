import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from app.main import app
from app.db import get_connection
from app.storage.user_store import user_store

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture(autouse=True)
def clean_database():
    conn = get_connection()
    try:
        conn.execute(text("DELETE FROM comments"))
        conn.execute(text("DELETE FROM tasks"))
        conn.execute(text("DELETE FROM users"))
        conn.commit()
    finally:
        conn.close()

@pytest.fixture
def test_user():
    return user_store.add({"username": "testuser", "email": "test@example.com"})