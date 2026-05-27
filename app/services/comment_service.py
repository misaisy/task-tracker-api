"""
Сервисный слой для комментариев.
Слой: бизнес-логика (services).
Зависит от: storage.
"""
import logging
from app.storage.comment_store import CommentStore
from app.exceptions import CommentNotFoundError

logger = logging.getLogger(__name__)


class CommentService:
    def __init__(self, store: CommentStore):
        self.store = store

    def get_comments_by_task(self, task_id: int) -> list[dict]:
        return self.store.get_by_task_id(task_id)

    def create_comment(self, comment_data: dict) -> dict:
        comment = self.store.add(comment_data)
        logger.info(
            "Comment created: id=%d, task_id=%d", 
            comment["id"], 
            comment["task_id"],
        )
        return comment