from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import AsyncSessionLocal
from app.services.comment_service import CommentService
from app.services.export_service import ExportService
from app.services.notification_service import NotificationService
from app.services.task_service import TaskService
from app.services.user_service import UserService
from app.storage.comment_store import CommentStore
from app.storage.task_history_store import TaskHistoryStore
from app.storage.task_store import TaskStore
from app.storage.user_store import UserStore

from .db import get_db

_export_service = None


def get_notification_service() -> NotificationService:
    return NotificationService()


def get_task_service(
    db: AsyncSession = Depends(get_db),
    notification_service: NotificationService = Depends(get_notification_service),
) -> TaskService:
    task_store = TaskStore(db)
    history_store = TaskHistoryStore(db)
    user_store = UserStore(db)
    return TaskService(
        store=task_store,
        history_store=history_store,
        user_store=user_store,
        notification_service=notification_service,
    )


def get_export_service() -> ExportService:
    global _export_service
    if _export_service is None:
        _export_service = ExportService(AsyncSessionLocal)
    return _export_service


def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    user_store = UserStore(db)
    return UserService(store=user_store)


def get_comment_service(db: AsyncSession = Depends(get_db)) -> CommentService:
    comment_store = CommentStore(db)
    task_store = TaskStore(db)
    return CommentService(store=comment_store, task_store=task_store)
