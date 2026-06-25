import pytest


@pytest.mark.asyncio
async def test_no_token_returns_401(client):
    """Запрос без токена возвращает 401."""
    response = await client.post("/tasks/", json={"title": "Test"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_task_with_auth(client, auth_headers):
    """С токеном задача создаётся, владелец — текущий пользователь."""
    response = await client.post(
        "/tasks/",
        json={"title": "Моя задача", "priority": "high"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert "owner_id" in data


@pytest.mark.asyncio
async def test_owner_can_modify_own_task(client, auth_headers):
    """Владелец может изменять свою задачу."""
    create_resp = await client.post(
        "/tasks/",
        json={"title": "Задача"},
        headers=auth_headers,
    )
    task_id = create_resp.json()["id"]

    response = await client.patch(
        f"/tasks/{task_id}",
        json={"title": "Обновлено"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Обновлено"


@pytest.mark.asyncio
async def test_non_owner_gets_403(client, auth_headers, other_headers):
    """Чужой пользователь не видит чужую задачу (403)."""
    create_resp = await client.post(
        "/tasks/",
        json={"title": "Чужая задача"},
        headers=auth_headers,
    )
    task_id = create_resp.json()["id"]

    response = await client.get(f"/tasks/{task_id}", headers=other_headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_owner_can_assign_self(client, auth_headers):
    """Владелец может назначить исполнителем себя."""
    create_resp = await client.post(
        "/tasks/",
        json={"title": "Задача"},
        headers=auth_headers,
    )
    task_id = create_resp.json()["id"]
    user_id = create_resp.json()["owner_id"]

    response = await client.post(
        f"/tasks/{task_id}/assign",
        json={"user_id": user_id},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["assignee_id"] == user_id


@pytest.mark.asyncio
async def test_admin_can_access_any_task(client, auth_headers, admin_headers):
    """Админ может читать чужую задачу."""
    create_resp = await client.post(
        "/tasks/",
        json={"title": "Задача жертвы"},
        headers=auth_headers,
    )
    task_id = create_resp.json()["id"]

    response = await client.get(f"/tasks/{task_id}", headers=admin_headers)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_deactivated_user_cannot_login(client, auth_user, admin_headers):
    """Деактивированный пользователь не может залогиниться."""
    users_resp = await client.get("/users/", headers=auth_user["headers"])
    user = next(u for u in users_resp.json() if u["username"] == auth_user["username"])

    await client.post(
        f"/users/{user['id']}/deactivate",
        headers=admin_headers,
    )

    response = await client.post("/auth/login", data={
        "username": auth_user["username"],
        "password": auth_user["password"],
    })
    assert response.status_code == 403
