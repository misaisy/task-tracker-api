"""
Сервисный слой для комментариев.
Слой: бизнес-логика (services).
Зависит от: storage.
"""
import logging
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound

from app.core.constants import Role, Status
from app.errors.exceptions import ConflictError, TaskNotFoundError
from app.models.orm import Comment, User
from app.models.schemas import CommentCreate
from app.storage.comment_store import CommentStore
from app.storage.task_store import TaskStore

logger = logging.getLogger(__name__)


class CommentService:
    def __init__(self, store: CommentStore, task_store: TaskStore):
        self.store = store
        self.task_store = task_store

    async def get_comments_by_task(self, task_id: UUID, current_user: User | None = None) -> list[Comment]:
        comments = await self.store.get_by_task_id(task_id)
        if current_user and current_user.role != Role.ADMIN:
            comments = [c for c in comments if c.author_id == current_user.id]
        return comments

    async def create_comment(self, comment: CommentCreate, task_id: UUID, author_id: UUID) -> Comment:
        data = comment.model_dump(mode='json')
        data["task_id"] = task_id
        data["author_id"] = author_id

        try:
            task = await self.task_store.get_by_id(task_id)
        except NoResultFound as e:
            raise TaskNotFoundError(task_id) from e

        if task.status == Status.ARCHIVED:
            raise ConflictError("Cannot comment on archived task")

        try:
            comment = await self.store.add(data)
        except IntegrityError as e:
            raise ConflictError("Cannot create comment") from e

        logger.info(
            "Comment created: id=%s, task_id=%s, author_id=%s",
            comment.id, comment.task_id, comment.author_id)
        return comment
