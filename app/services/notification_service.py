import logging
import time

import httpx

from app.core.settings import settings

logger = logging.getLogger(__name__)


class NotificationService:
    async def notify_task_closed(self, task) -> None:
        await self._send_notification(task, "task_closed", {
            "closed_at": task.closed_at.isoformat() if task.closed_at else None,
        })

    async def notify_task_archived(self, task) -> None:
        await self._send_notification(task, "task_archived", {
            "archived_at": task.updated_at.isoformat() if task.updated_at else None,
        })

    async def _send_notification(self, task, event: str, extra_payload: dict) -> None:
        if not settings.NOTIFICATION_WEBHOOK_URL:
            logger.warning("NOTIFICATION_WEBHOOK_URL is not set, skipping %s for task %s", event, task.id)
            return

        payload = {
            "event": event,
            "task_id": str(task.id),
            "title": task.title,
            **extra_payload,
        }
        logger.debug("Sending %s notification for task %s to %s", event, task.id, settings.NOTIFICATION_WEBHOOK_URL)
        start = time.monotonic()
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    settings.NOTIFICATION_WEBHOOK_URL,
                    json=payload,
                    timeout=5.0,
                )
                response.raise_for_status()
                elapsed = time.monotonic() - start
                logger.info(
                    "Notification %s sent for task %s, status %d (%.3fs)",
                    event,
                    task.id,
                    response.status_code,
                    elapsed
                )
            except httpx.HTTPError as exc:
                elapsed = time.monotonic() - start
                logger.error("Failed to send %s notification for task %s after %.3fs: %s", event, task.id, elapsed, exc)
