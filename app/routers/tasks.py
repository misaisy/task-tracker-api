"""
Роутер для задач.
Слой: HTTP (routers).
Зависит от: services, models, dependencies.
"""
from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_task_service
from app.models import TaskCreate, TaskResponse
from app.services.task_service import TaskService


router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(task: TaskCreate, service: TaskService = Depends(get_task_service)):
    """Создаёт новую задачу."""
    new_task = service.create_task(task.model_dump())
    return new_task


@router.get("/", response_model=list[TaskResponse])
async def list_tasks(service: TaskService = Depends(get_task_service)):
    """Возвращает список всех задач."""
    return service.get_all_tasks()


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int, service: TaskService = Depends(get_task_service)):
    """Возвращает задачу по ID."""
    return service.get_task_by_id(task_id)