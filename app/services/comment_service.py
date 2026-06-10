"""
Сервисный слой для комментариев.
Слой: бизнес-логика (services).
Зависит от: storage.
"""
import logging

from app.exceptions import TaskNotFoundError, UserNotFoundError
from app.storage.comment_store import CommentStore
from app.storage.task_store import TaskStore
from app.storage.user_store import UserStore

logger = logging.getLogger(__name__)


class CommentService:
    def __init__(self, store: CommentStore, user_store: UserStore, task_store: TaskStore):
        self.store = store
        self.task_store = task_store
        self.user_store = user_store

    def get_comments_by_task(self, task_id: int) -> list[dict]:
        return self.store.get_by_task_id(task_id)

    def create_comment(self, comment_data: dict) -> dict:
        task = self.task_store.get_by_id(comment_data["task_id"])
        if task is None:
            raise TaskNotFoundError(comment_data["task_id"])

        author = self.user_store.get_by_id(comment_data["author_id"])
        if author is None:
            raise UserNotFoundError(comment_data["author_id"])

        comment = self.store.add(comment_data)
        logger.info(
            "Comment created: id=%d, task_id=%d, author_id=%d",
            comment["id"], comment["task_id"], comment["author_id"])
        return comment
