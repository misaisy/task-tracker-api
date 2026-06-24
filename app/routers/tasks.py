"""
Роутер для задач.
Слой: HTTP (routers).
Зависит от: services, models, dependencies.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse, PlainTextResponse

from app.core.constants import Role
from app.dependencies import get_current_user, get_task_service, require_owner_or_admin
from app.models.orm import Task, User
from app.models.schemas import (
    AssignRequest,
    TaskCreate,
    TaskDetailResponse,
    TaskHistoryResponse,
    TaskListResponse,
    TaskResponse,
    TaskSummaryResponse,
    TaskUpdate,
)
from app.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/", response_model=TaskListResponse)
async def list_tasks(
    status: str | None = Query(default=None, description="Фильтр по статусу"),
    priority: str | None = Query(default=None, description="Фильтр по приоритету"),
    page: int = Query(default=1, ge=1, description="Номер страницы"),
    page_size: int = Query(default=20, ge=1, le=100, description="Размер страницы"),
    sort_by: str = Query(default="created_at", description="Поле для сортировки"),
    sort_order: str = Query(default="desc", description="Направление сортировки"),
    service: TaskService = Depends(get_task_service),
    current_user: User = Depends(get_current_user),
):
    """Возвращает список задач с фильтрацией, сортировкой и пагинацией."""
    owner_id = None if current_user.role == Role.ADMIN else current_user.id
    return await service.get_all_tasks(
        status=status,
        priority=priority,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
        owner_id=owner_id,
    )


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task: TaskCreate,
    service: TaskService = Depends(get_task_service),
    current_user: User = Depends(get_current_user),
):
    """Создаёт новую задачу."""
    data = task.model_dump(mode='json')
    data["owner_id"] = current_user.id
    return await service.create_task(data)


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: UUID,
    update: TaskUpdate,
    service: TaskService = Depends(get_task_service),
    task: Task = Depends(require_owner_or_admin),
):
    """Частично обновляет задачу."""
    return await service.update_task(task_id, update)


@router.post("/{task_id}/assign", response_model=TaskResponse)
async def assign_task(
    task_id: UUID,
    request: AssignRequest,
    service: TaskService = Depends(get_task_service),
    current_user: User = Depends(get_current_user),
    task: Task = Depends(require_owner_or_admin),
):
    """Назначает исполнителя задаче."""
    return await service.assign_task(task_id, request.user_id, current_user)


@router.post("/{task_id}/archive", response_model=TaskResponse)
async def archive_task(
    task_id: UUID,
    service: TaskService = Depends(get_task_service),
    task: Task = Depends(require_owner_or_admin),
):
    """Архивирует задачу."""
    return await service.archive_task(task_id)


@router.post("/{task_id}/complete", response_model=TaskResponse)
async def complete_task(
    task_id: UUID,
    service: TaskService = Depends(get_task_service),
    task: Task = Depends(require_owner_or_admin),
):
    """Закрывает задачу."""
    return await service.complete_task(task_id)


@router.get("/summary", response_model=TaskSummaryResponse)
async def get_summary(
    service: TaskService = Depends(get_task_service),
):
    """Возвращает сводку по задачам."""
    return await service.get_summary()


@router.get("/export")
async def export_tasks(
    format: str = "json",
    service: TaskService = Depends(get_task_service),
    current_user: User = Depends(get_current_user),
):
    """Выгружает все задачи в JSON или CSV."""

    result = await service.export_tasks(format=format)

    if format == "csv":
        return PlainTextResponse(content=result, media_type="text/csv")

    return JSONResponse(content=result)


@router.get("/{task_id}", response_model=TaskDetailResponse)
async def get_task(
    task_id: UUID,
    service: TaskService = Depends(get_task_service),
    task: Task = Depends(require_owner_or_admin),
):
    """Возвращает задачу по ID."""
    return await service.get_task_with_relations(task_id)


@router.get("/{task_id}/history", response_model=list[TaskHistoryResponse])
async def get_task_history(
    task_id: UUID,
    service: TaskService = Depends(get_task_service),
    task: Task = Depends(require_owner_or_admin),
):
    """Возвращает историю изменений задачи."""
    await service.get_task_by_id(task_id)
    return await service.history_store.get_by_task_id(task_id)
