"""
SQLAlchemy модели для базы данных.
"""
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.constants import Priority, Status


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    tasks_owned: Mapped[list[Task]] = relationship(back_populates='owner', foreign_keys='Task.owner_id')
    tasks_assigned: Mapped[list[Task]] = relationship(back_populates='assignee', foreign_keys='Task.assignee_id')
    comments: Mapped[list[Comment]] = relationship(back_populates='author')


class Task(Base):
    __tablename__ = 'tasks'
    __table_args__ = (
        CheckConstraint("length(title) >= 1", name='ck_tasks_title_not_empty'),
        CheckConstraint("priority IN ('low', 'medium', 'high')", name='ck_tasks_priority_valid'),
        CheckConstraint("status IN ('TODO', 'IN_PROGRESS', 'REVIEW', 'DONE', 'ARCHIVED')", name='ck_tasks_status_valid')
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    priority: Mapped[Priority] = mapped_column(
        SAEnum(Priority, values_callable=lambda x: [e.value for e in x]),
        default=Priority.MEDIUM,
    )
    status: Mapped[Status] = mapped_column(
        SAEnum(Status, values_callable=lambda x: [e.value for e in x]),
        default=Status.TODO,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    owner_id: Mapped[int | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'), index=True)
    assignee_id: Mapped[int | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'), index=True)

    owner: Mapped[User | None] = relationship(back_populates='tasks_owned', foreign_keys=[owner_id])
    assignee: Mapped[User | None] = relationship(back_populates='tasks_assigned', foreign_keys=[assignee_id])
    comments: Mapped[list[Comment]] = relationship(back_populates='task')
    history: Mapped[list[TaskHistory]] = relationship(back_populates='task')


class Comment(Base):
    __tablename__ = 'comments'
    __table_args__ = (
    CheckConstraint(
        "length(text) >= 1 AND length(text) <= 1000",
        name='ck_comments_text_length',
    ),
)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(ForeignKey('tasks.id', ondelete='CASCADE'), index=True)
    author_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'), index=True)
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    task: Mapped[Task] = relationship(back_populates='comments')
    author: Mapped[User] = relationship(back_populates='comments')


class TaskHistory(Base):
    __tablename__ = 'task_history'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(ForeignKey('tasks.id', ondelete='CASCADE'), index=True)
    field: Mapped[str] = mapped_column(String(50))
    old_value: Mapped[str | None] = mapped_column(Text)
    new_value: Mapped[str | None] = mapped_column(Text)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    task: Mapped[Task] = relationship(back_populates='history')
