"""
Сервисный слой для комментариев.
Слой: бизнес-логика (services).
Зависит от: storage.
"""
import logging

from sqlalchemy.orm.exc import NoResultFound

from app.errors.exceptions import TaskNotFoundError, UserNotFoundError
from app.storage.comment_store import CommentStore
from app.storage.task_store import TaskStore
from app.storage.user_store import UserStore

logger = logging.getLogger(__name__)


class CommentService:
    def __init__(self, store: CommentStore, user_store: UserStore, task_store: TaskStore):
        self.store = store
        self.task_store = task_store
        self.user_store = user_store

    async def get_comments_by_task(self, task_id: int) -> list[dict]:
        return await self.store.get_by_task_id(task_id)

    async def create_comment(self, comment_data: dict) -> dict:
        try:
            await self.task_store.get_by_id(comment_data["task_id"])
        except NoResultFound as e:
            raise TaskNotFoundError(comment_data["task_id"]) from e

        try:
            await self.user_store.get_by_id(comment_data["author_id"])
        except NoResultFound as e:
            raise UserNotFoundError(comment_data["author_id"]) from e

        comment = await self.store.add(comment_data)
        await self.store.commit()
        logger.info(
            "Comment created: id=%d, task_id=%d, author_id=%d",
            comment["id"], comment["task_id"], comment["author_id"])
        return comment
