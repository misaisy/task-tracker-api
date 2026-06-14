"""
Pydantic-модели.
Слой: модели данных.
"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.constants import DEFAULT_PRIORITY, DEFAULT_STATUS


class ErrorDetail(BaseModel):
    """Одна ошибка в списке details."""
    loc: list[str] | None = None
    msg: str


class ErrorResponse(BaseModel):
    """Единый формат всех ошибок API."""
    error_code: str
    details: str | list[ErrorDetail]


class TaskBase(BaseModel):
    """Общие поля для всех моделей задачи."""
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    priority: str = Field(default=DEFAULT_PRIORITY, pattern="^(low|medium|high)$")
    status: str = Field(default=DEFAULT_STATUS)


class TaskCreate(TaskBase):
    """Модель для создания задачи."""
    owner_id: int | None = Field(default=None, gt=0)
    model_config = ConfigDict(extra="forbid")


class TaskResponse(TaskBase):
    """Модель ответа с данными задачи."""
    id: int
    created_at: datetime
    updated_at: datetime | None = None
    closed_at: datetime | None = None
    owner_id: int | None = None
    assignee_id: int | None = None


class TaskUpdate(BaseModel):
    """Модель для частичного обновления задачи."""
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    priority: str | None = Field(default=None, pattern="^(low|medium|high)$")
    status: str | None = Field(default=None)
    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def check_title_not_null(self) -> "TaskUpdate":  # noqa: UP037
        """Проверяет, что title не установлен в null."""
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
    model_config = ConfigDict(extra="forbid")


class TaskWithAssigneeResponse(TaskResponse):
    """Модель ответа задачи с назначенным исполнителем."""
    assignee_id: int | None = None


class UserCreate(BaseModel):
    """Модель для создания пользователя."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    model_config = ConfigDict(extra="forbid")


class UserResponse(BaseModel):
    """Модель ответа с данными пользователя."""
    id: int
    username: str
    email: str
    created_at: datetime


class CommentCreate(BaseModel):
    """Модель для создания комментария."""
    text: str = Field(..., min_length=1, max_length=1000)
    author_id: int = Field(..., gt=0, description="ID автора комментария")
    model_config = ConfigDict(extra="forbid")


class CommentResponse(BaseModel):
    """Модель ответа с данными комментария."""
    id: int
    task_id: int
    text: str
    author_id: int
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


class TaskHistoryResponse(BaseModel):
    """Запись истории изменений задачи."""
    id: int
    task_id: int
    field: str
    old_value: str | None
    new_value: str | None
    changed_at: datetime
