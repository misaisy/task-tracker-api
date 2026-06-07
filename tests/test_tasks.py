def test_create_task_success(client):
    """Успешное создание задачи."""
    payload = {
        "title": "Тестовая задача",
        "description": "Описание",
        "priority": "high"
    }
    response = client.post("/tasks", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Тестовая задача"
    assert data["description"] == "Описание"
    assert data["priority"] == "high"
    assert data["status"] == "TODO"
    assert "id" in data
    assert "created_at" in data


def test_update_task_success(client):
    """PATCH /tasks/{id} обновляет разрешённые поля и игнорирует запрещённые."""
    create_resp = client.post("/tasks", json={
        "title": "Исходная задача",
        "priority": "low"
    })
    assert create_resp.status_code == 201
    task_id = create_resp.json()["id"]
    original_created_at = create_resp.json()["created_at"]

    update_resp = client.patch(f"/tasks/{task_id}", json={
        "title": "Обновлённая задача",
        "priority": "high",
        "id": 999,
        "created_at": "2020-01-01T00:00:00Z"
    })

    assert update_resp.status_code == 200
    data = update_resp.json()
    assert data["title"] == "Обновлённая задача"
    assert data["priority"] == "high"
    assert data["id"] == task_id
    assert data["created_at"] == original_created_at
