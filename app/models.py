"""
Pydantic-модели.
Слой: модели данных.
"""
from datetime import datetime
from pydantic import BaseModel, Field, model_validator
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


class TaskUpdate(BaseModel):
    """Модель для частичного обновления задачи."""
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    priority: str | None = Field(default=None, pattern="^(low|medium|high)$")
    status: str | None = Field(default=None)

    @model_validator(mode="after")
    def check_title_not_null(self):
        """Проверяет, что title не установлен в null явно."""
        if "title" in self.model_fields_set and self.title is None:
            raise ValueError("title не может быть null")
        return self


class TaskListResponse(BaseModel):
    """Модель ответа для списка задач с пагинацией."""
    items: list[TaskResponse]
    total: int
    page: int
    page_size: int
    pages: int


class AssignRequest(BaseModel):
    """Модель запроса для назначения исполнителя."""
    user_id: int = Field(..., gt=0, description="ID пользователя-исполнителя")


class TaskWithAssigneeResponse(TaskResponse):
    """Модель ответа задачи с назначенным исполнителем."""
    assignee_id: int | None = None


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

class TaskSummaryResponse(BaseModel):
    """Модель ответа для сводки по задачам."""
    total: int
    by_status: dict[str, int]
    by_priority: dict[str, int]


class TaskExportResponse(BaseModel):
    """Модель ответа для экспорта задач."""
    exported_at: str
    format: str
    tasks: list[TaskResponse]