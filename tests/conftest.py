import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db import SessionLocal
from app.models_sql import Comment, Task, User, TaskHistory


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def clean_database():
    """Очищает все таблицы перед каждым тестом."""
    db = SessionLocal()
    try:
        db.query(TaskHistory).delete()
        db.query(Comment).delete()
        db.query(Task).delete()
        db.query(User).delete()
        db.commit()
    finally:
        db.close()


@pytest.fixture
def test_user():
    """Создаёт тестового пользователя через сервис."""
    from app.storage.user_store import UserStore
    db = SessionLocal()
    store = UserStore(db)
    user = store.add({"username": "testuser", "email": "test@example.com"})
    db.commit()
    db.close()
    return user