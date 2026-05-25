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