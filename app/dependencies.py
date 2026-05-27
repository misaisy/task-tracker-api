from app.storage.task_store import TaskStore, task_store
from app.services.task_service import TaskService

from app.storage.user_store import UserStore, user_store
from app.services.user_service import UserService

from app.storage.comment_store import CommentStore, comment_store
from app.services.comment_service import CommentService


def get_task_service() -> TaskService:
    return TaskService(store=task_store)


def get_user_service() -> UserService:
    return UserService(store=user_store)


def get_comment_service() -> CommentService:
    return CommentService(store=comment_store)