import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.storage.task_store import task_store


@pytest.fixture
def client():
    """Клиент для тестирования API."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def clean_storage():
    """Очищает хранилище перед каждым тестом."""
    task_store.clear()
