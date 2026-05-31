from app.services.comment_service import CommentService
from app.services.task_service import TaskService
from app.services.user_service import UserService
from app.settings import Settings
from app.settings import settings as _settings
from app.storage.comment_store import comment_store
from app.storage.task_store import task_store
from app.storage.user_store import user_store


def get_task_service() -> TaskService:
    return TaskService(store=task_store)


def get_user_service() -> UserService:
    return UserService(store=user_store)


def get_comment_service() -> CommentService:
    return CommentService(store=comment_store)


def get_settings() -> Settings:
    """Возвращает настройки приложения."""
    return _settings
