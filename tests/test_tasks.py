from app.constants import PRIORITY_HIGH, PRIORITY_LOW, TASK_STATUS_TODO


def test_create_task_success(client):
    """Успешное создание задачи."""
    payload = {
        "title": "Тестовая задача",
        "description": "Описание",
        "priority": PRIORITY_HIGH
    }
    response = client.post("/tasks", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Тестовая задача"
    assert data["description"] == "Описание"
    assert data["priority"] == PRIORITY_HIGH
    assert data["status"] == TASK_STATUS_TODO
    assert "id" in data
    assert "created_at" in data


def test_update_task_success(client):
    """PATCH /tasks/{id} обновляет разрешённые поля, а запрещённые не изменяются."""
    create_resp = client.post("/tasks", json={
        "title": "Исходная задача",
        "priority": PRIORITY_LOW
    })
    assert create_resp.status_code == 201
    task_id = create_resp.json()["id"]
    original_created_at = create_resp.json()["created_at"]

    update_resp = client.patch(f"/tasks/{task_id}", json={
        "title": "Обновлённая задача",
        "priority": PRIORITY_HIGH,
    })

    assert update_resp.status_code == 200
    data = update_resp.json()
    assert data["title"] == "Обновлённая задача"
    assert data["priority"] == PRIORITY_HIGH
    assert data["id"] == task_id
    assert data["created_at"] == original_created_at


def test_get_nonexistent_task(client):
    """Проверяет, что запрос несуществующей задачи возвращает 404."""
    response = client.get("/tasks/999")
    assert response.status_code == 404
    assert "details" in response.json()
    assert response.json()["error_code"] == "TASK_NOT_FOUND"
