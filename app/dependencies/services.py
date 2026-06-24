from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.comment_service import CommentService
from app.services.task_service import TaskService
from app.services.user_service import UserService
from app.storage.comment_store import CommentStore
from app.storage.task_history_store import TaskHistoryStore
from app.storage.task_store import TaskStore
from app.storage.user_store import UserStore

from .db import get_db


def get_task_service(db: AsyncSession = Depends(get_db)) -> TaskService:
    task_store = TaskStore(db)
    history_store = TaskHistoryStore(db)
    user_store = UserStore(db)
    return TaskService(store=task_store, history_store=history_store, user_store=user_store)


def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    user_store = UserStore(db)
    return UserService(store=user_store)


def get_comment_service(db: AsyncSession = Depends(get_db)) -> CommentService:
    comment_store = CommentStore(db)
    user_store = UserStore(db)
    task_store = TaskStore(db)
    return CommentService(store=comment_store, user_store=user_store, task_store=task_store)
