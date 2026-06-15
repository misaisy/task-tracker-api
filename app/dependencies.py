from app.services.comment_service import CommentService
from app.services.task_service import TaskService
from app.services.user_service import UserService
from app.settings import Settings
from app.settings import settings as _settings
from app.storage.comment_store import CommentStore
from app.storage.task_history_store import TaskHistoryStore
from app.storage.task_store import TaskStore
from app.storage.user_store import UserStore
from app.db import SessionLocal
from sqlalchemy.orm import Session
from fastapi import Depends
from typing import Generator


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_task_service(db: Session = Depends(get_db)) -> TaskService:
    task_store = TaskStore(db)
    history_store = TaskHistoryStore(db)
    user_store = UserStore(db)
    return TaskService(store=task_store, history_store=history_store, user_store=user_store)


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    user_store = UserStore(db)
    return UserService(store=user_store)


def get_comment_service(db: Session = Depends(get_db)) -> CommentService:
    comment_store = CommentStore(db)
    user_store = UserStore(db)
    task_store = TaskStore(db)
    return CommentService(store=comment_store, user_store=user_store, task_store=task_store)


def get_settings() -> Settings:
    return _settings
