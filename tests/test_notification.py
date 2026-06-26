from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.services.notification_service import NotificationService


@pytest.mark.asyncio
async def test_notify_task_closed_success(caplog):
    """Успешная отправка уведомления: HTTP 200."""
    class DummyTask:
        id = 1
        title = "Test task"
        closed_at = None

    task = DummyTask()

    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = lambda: None

    with (
        patch("httpx.AsyncClient.post", return_value=mock_response) as mock_post,
        patch("app.services.notification_service.settings.NOTIFICATION_WEBHOOK_URL", "http://test.local"),
    ):
        service = NotificationService()
        await service.notify_task_closed(task)

        mock_post.assert_called_once()
        assert "Notification task_closed sent for task" in caplog.text


@pytest.mark.asyncio
async def test_notify_task_closed_timeout_error(caplog):
    """Сбой отправки уведомления: таймаут или HTTPError."""
    class DummyTask:
        id = 2
        title = "Timeout task"
        closed_at = None

    task = DummyTask()

    with (
        patch("httpx.AsyncClient.post", side_effect=httpx.TimeoutException("Timeout")),
        patch("app.services.notification_service.settings.NOTIFICATION_WEBHOOK_URL", "http://test.local"),
    ):
        service = NotificationService()
        await service.notify_task_closed(task)

        assert "Failed to send task_closed notification" in caplog.text
