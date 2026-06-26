import asyncio

import pytest

from app.core.constants import Priority, Status


@pytest.mark.asyncio
async def test_create_task_success(client, auth_headers):
    """Успешное создание задачи."""
    payload = {
        "title": "Тестовая задача",
        "description": "Описание",
        "priority": "high"
    }
    response = await client.post("/tasks/", json=payload, headers=auth_headers)

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Тестовая задача"
    assert data["description"] == "Описание"
    assert data["priority"] == Priority.HIGH
    assert data["status"] == Status.TODO
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_get_nonexistent_task(client, auth_headers):
    """Проверяет, что запрос несуществующей задачи возвращает 404."""
    response = await client.get(
        "/tasks/550e8400-e29b-41d4-a716-446655440000",
        headers=auth_headers,
    )
    assert response.status_code == 404
    assert "details" in response.json()
    assert response.json()["error_code"] == "TASK_NOT_FOUND"


@pytest.mark.asyncio
async def test_complete_task_success(client, auth_headers):
    """Успешное закрытие задачи."""
    create_resp = await client.post("/tasks/", json={"title": "Задача для закрытия"}, headers=auth_headers)
    assert create_resp.status_code == 201
    task_id = create_resp.json()["id"]

    complete_resp = await client.post(f"/tasks/{task_id}/complete", headers=auth_headers)
    assert complete_resp.status_code == 200
    data = complete_resp.json()
    assert data["status"] == Status.DONE
    assert data["closed_at"] is not None


@pytest.mark.asyncio
async def test_create_task_empty_title(client, auth_headers):
    """Создание задачи с пустым title возвращает 422."""
    response = await client.post("/tasks/", json={"title": ""}, headers=auth_headers)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_complete_task_already_done(client, auth_headers):
    """Повторное закрытие задачи возвращает 409."""
    create_resp = await client.post("/tasks/", json={"title": "Задача для повторного закрытия"}, headers=auth_headers)
    assert create_resp.status_code == 201
    task_id = create_resp.json()["id"]

    await client.post(f"/tasks/{task_id}/complete", headers=auth_headers)
    after_first = (await client.get(f"/tasks/{task_id}", headers=auth_headers)).json()

    response = await client.post(f"/tasks/{task_id}/complete", headers=auth_headers)
    assert response.status_code == 409
    after_second = (await client.get(f"/tasks/{task_id}", headers=auth_headers)).json()

    assert after_second["status"] == after_first["status"]
    assert after_second["closed_at"] == after_first["closed_at"]


@pytest.mark.asyncio
async def test_update_archived_task(client, auth_headers):
    """Обновление архивной задачи возвращает 409."""
    create_resp = await client.post("/tasks/", json={"title": "Задача для архивации"}, headers=auth_headers)
    assert create_resp.status_code == 201
    task_id = create_resp.json()["id"]

    await client.post(f"/tasks/{task_id}/archive", headers=auth_headers)
    after_archive = (await client.get(f"/tasks/{task_id}", headers=auth_headers)).json()

    response = await client.patch(f"/tasks/{task_id}", json={"title": "Новое название"}, headers=auth_headers)
    assert response.status_code == 409

    after_fail = (await client.get(f"/tasks/{task_id}", headers=auth_headers)).json()
    assert after_fail["title"] == after_archive["title"]
    assert after_fail["status"] == after_archive["status"]


@pytest.mark.asyncio
async def test_update_task_success(client, auth_headers):
    """PATCH /tasks/{id} обновляет разрешённые поля, а запрещённые не изменяются."""
    create_resp = await client.post(
        "/tasks/",
        json={"title": "Исходная задача", "priority": Priority.LOW},
        headers=auth_headers,
    )
    assert create_resp.status_code == 201
    task_id = create_resp.json()["id"]
    original_created_at = create_resp.json()["created_at"]

    update_resp = await client.patch(
        f"/tasks/{task_id}",
        json={"title": "Обновлённая задача", "priority": Priority.HIGH},
        headers=auth_headers,
    )

    assert update_resp.status_code == 200
    data = update_resp.json()
    assert data["title"] == "Обновлённая задача"
    assert data["priority"] == Priority.HIGH
    assert data["id"] == task_id
    assert data["created_at"] == original_created_at


@pytest.mark.asyncio
async def test_list_tasks_with_filters(client, auth_headers):
    """GET /tasks с фильтром по статусу возвращает только подходящие задачи."""
    await client.post("/tasks/", json={"title": "Задача TODO", "priority": "low"}, headers=auth_headers)
    await client.post("/tasks/", json={"title": "Задача DONE", "priority": "high"}, headers=auth_headers)
    tasks = (await client.get("/tasks/", headers=auth_headers)).json()
    task_id = next(t["id"] for t in tasks["items"] if t["status"] == Status.TODO)
    await client.post(f"/tasks/{task_id}/complete", headers=auth_headers)

    response = await client.get(f"/tasks/?status={Status.DONE}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["status"] == Status.DONE
    assert data["total"] == 1


@pytest.mark.asyncio
async def test_list_tasks_with_sorting(client, auth_headers):
    """GET /tasks с сортировкой по приоритету возвращает правильный порядок."""
    await client.post("/tasks/", json={"title": "Low", "priority": "low"}, headers=auth_headers)
    await client.post("/tasks/", json={"title": "High", "priority": "high"}, headers=auth_headers)
    await client.post("/tasks/", json={"title": "Medium", "priority": "medium"}, headers=auth_headers)

    response = await client.get("/tasks/?sort_by=priority&sort_order=asc", headers=auth_headers)
    assert response.status_code == 200
    items = response.json()["items"]
    priorities = [item["priority"] for item in items]
    assert priorities == [Priority.LOW, Priority.MEDIUM, Priority.HIGH]


@pytest.mark.asyncio
async def test_list_tasks_with_pagination(client, auth_headers):
    """GET /tasks с пагинацией возвращает корректные page и total."""
    for i in range(5):
        await client.post("/tasks/", json={"title": f"Задача {i}", "priority": "low"}, headers=auth_headers)

    response = await client.get("/tasks/?page=1&page_size=2", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] == 5
    assert data["page"] == 1
    assert data["pages"] == 3


@pytest.mark.asyncio
async def test_get_summary(client, auth_headers):
    """GET /tasks/summary возвращает сводку по статусам и приоритетам."""
    await client.post("/tasks/", json={"title": "Todo task", "priority": "low"}, headers=auth_headers)
    await client.post("/tasks/", json={"title": "Done task", "priority": "high"}, headers=auth_headers)
    tasks = (await client.get("/tasks/", headers=auth_headers)).json()
    task_id = next(t["id"] for t in tasks["items"] if t["status"] == Status.TODO)
    await client.post(f"/tasks/{task_id}/complete", headers=auth_headers)

    response = await client.get("/tasks/summary", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "by_status" in data
    assert "by_priority" in data
    assert data["total"] == 2
    assert data["by_status"][Status.DONE] == 1
    assert data["by_priority"][Priority.HIGH] == 1


@pytest.mark.asyncio
async def test_export_tasks(client, auth_headers):
    """Экспорт задач."""
    start_resp = await client.post("/tasks/export?format=json", headers=auth_headers)
    assert start_resp.status_code == 202
    export_id = start_resp.json()["export_id"]

    for _ in range(10):
        result_resp = await client.get(f"/tasks/export/{export_id}", headers=auth_headers)
        data = result_resp.json()
        if "status" not in data or data["status"] == "completed":
            break
        await asyncio.sleep(0.01)
    else:
        pytest.fail("Export did not complete in time")

    assert "exported_at" in data
    assert data["format"] == "json"
    assert isinstance(data["tasks"], list)


@pytest.mark.asyncio
async def test_task_history_on_complete(client, auth_headers):
    """При закрытии задачи появляется запись в TaskHistory."""
    create_resp = await client.post("/tasks/", json={"title": "Задача для истории"}, headers=auth_headers)
    assert create_resp.status_code == 201
    task_id = create_resp.json()["id"]

    await client.post(f"/tasks/{task_id}/complete", headers=auth_headers)

    history_resp = await client.get(f"/tasks/{task_id}/history", headers=auth_headers)
    assert history_resp.status_code == 200
    history = history_resp.json()
    assert len(history) >= 1
    assert any(
        entry["field"] == "status" and entry["new_value"] == Status.DONE
        for entry in history
    )


@pytest.mark.asyncio
async def test_patch_null_description(client, auth_headers):
    """PATCH с description: null сбрасывает описание."""
    create_resp = await client.post(
        "/tasks/",
        json={"title": "Задача с описанием", "description": "Будет сброшено"},
        headers=auth_headers,
    )
    assert create_resp.status_code == 201
    task_id = create_resp.json()["id"]

    update_resp = await client.patch(f"/tasks/{task_id}", json={"description": None}, headers=auth_headers)
    assert update_resp.status_code == 200
    assert update_resp.json()["description"] is None


@pytest.mark.asyncio
async def test_patch_null_title(client, auth_headers):
    """PATCH с title: null возвращает 422."""
    create_resp = await client.post("/tasks/", json={"title": "Задача"}, headers=auth_headers)
    assert create_resp.status_code == 201
    task_id = create_resp.json()["id"]

    response = await client.patch(f"/tasks/{task_id}", json={"title": None}, headers=auth_headers)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_patch_forbidden_fields(client, auth_headers):
    """PATCH с запрещёнными полями (id, created_at) возвращает 422."""
    create_resp = await client.post("/tasks/", json={"title": "Задача"}, headers=auth_headers)
    assert create_resp.status_code == 201
    task_id = create_resp.json()["id"]

    response = await client.patch(
        f"/tasks/{task_id}",
        json={"id": 999, "created_at": "2020-01-01T00:00:00Z"},
        headers=auth_headers,
    )
    assert response.status_code == 422
