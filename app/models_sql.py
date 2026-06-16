"""
SQLAlchemy модели для базы данных.
"""
from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    tasks_owned = relationship('Task', back_populates='owner', foreign_keys='Task.owner_id')
    tasks_assigned = relationship('Task', back_populates='assignee', foreign_keys='Task.assignee_id')
    comments = relationship('Comment', back_populates='author')


class Task(Base):
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    priority = Column(String(10), nullable=False, server_default='medium')
    status = Column(String(20), nullable=False, server_default='TODO')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    closed_at = Column(DateTime(timezone=True))
    owner_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), index=True)
    assignee_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), index=True)
    history = relationship('TaskHistory', back_populates='task')

    owner = relationship('User', back_populates='tasks_owned', foreign_keys=[owner_id])
    assignee = relationship('User', back_populates='tasks_assigned', foreign_keys=[assignee_id])
    comments = relationship('Comment', back_populates='task')

    __table_args__ = (
        CheckConstraint("length(title) >= 1", name='ck_tasks_title_not_empty'),
        CheckConstraint("priority IN ('low', 'medium', 'high')", name='ck_tasks_priority_valid'),
        CheckConstraint("status IN ('TODO', 'IN_PROGRESS', 'REVIEW', 'DONE', 'ARCHIVED')", name='ck_tasks_status_valid')
    )


class Comment(Base):
    __tablename__ = 'comments'

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False, index=True)
    author_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=False, index=True)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    task = relationship('Task', back_populates='comments')
    author = relationship('User', back_populates='comments')

    __table_args__ = (
        CheckConstraint("length(text) >= 1 AND length(text) <= 1000", name='ck_comments_text_length'),
    )


class TaskHistory(Base):
    __tablename__ = 'task_history'

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False, index=True)
    field = Column(String(50), nullable=False)
    old_value = Column(Text)
    new_value = Column(Text)
    changed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    task = relationship('Task', back_populates='history')
