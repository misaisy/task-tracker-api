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
async def test_non_owner_gets_404(client, auth_headers):
    """Чужой пользователь не видит чужую задачу (404)."""
    create_resp = await client.post(
        "/tasks/",
        json={"title": "Чужая задача"},
        headers=auth_headers,
    )
    task_id = create_resp.json()["id"]

    await client.post(
        "/users/",
        json={"username": "other", "email": "other@test.com"},
    )
    login_resp = await client.post("/auth/login?username=other")
    other_token = login_resp.json()["access_token"]
    other_headers = {"Authorization": f"Bearer {other_token}"}

    response = await client.get(f"/tasks/{task_id}", headers=other_headers)
    assert response.status_code == 404


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
async def test_admin_can_access_any_task(client, admin_headers):
    """Админ может читать чужую задачу."""
    await client.post(
        "/users/",
        json={"username": "victim", "email": "victim@test.com"},
    )
    victim_login = await client.post("/auth/login?username=victim")
    victim_token = victim_login.json()["access_token"]
    victim_headers = {"Authorization": f"Bearer {victim_token}"}

    create_resp = await client.post(
        "/tasks/",
        json={"title": "Задача жертвы"},
        headers=victim_headers,
    )
    task_id = create_resp.json()["id"]

    # Админ смотрит чужую задачу
    response = await client.get(f"/tasks/{task_id}", headers=admin_headers)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_deactivated_user_cannot_login(client, admin_headers):
    """Деактивированный пользователь не может залогиниться."""
    create_resp = await client.post(
        "/users/",
        json={"username": "deactivate_me", "email": "deactivate@test.com"},
    )
    user_id = create_resp.json()["id"]

    await client.post(
        f"/users/{user_id}/deactivate",
        headers=admin_headers,
    )

    response = await client.post("/auth/login?username=deactivate_me")
    assert response.status_code == 403
