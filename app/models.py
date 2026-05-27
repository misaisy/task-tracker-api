"""
Pydantic-модели.
Слой: модели данных.
"""
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class TaskCreate(BaseModel):
    """Модель для создания задачи."""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)
    priority: str = Field(default="medium", pattern="^(low|medium|high)$")


class TaskResponse(BaseModel):
    """Модель ответа с данными задачи."""
    id: int
    title: str
    description: Optional[str]
    priority: str
    status: str
    created_at: datetime


class UserCreate(BaseModel):
    """Модель для создания пользователя."""
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


class UserResponse(BaseModel):
    """Модель ответа с данными пользователя."""
    id: int
    username: str
    email: str
    created_at: datetime


class CommentCreate(BaseModel):
    """Модель для создания комментария."""
    task_id: int = Field(..., gt=0)
    text: str = Field(..., min_length=1, max_length=1000)


class CommentResponse(BaseModel):
    """Модель ответа с данными комментария."""
    id: int
    task_id: int
    text: str
    created_at: datetime