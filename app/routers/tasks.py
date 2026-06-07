"""
Роутер для задач.
Слой: HTTP (routers).
Зависит от: services, models, dependencies.
"""
from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse, PlainTextResponse

from app.dependencies import get_task_service
from app.models import AssignRequest, TaskCreate, TaskListResponse, TaskResponse, TaskSummaryResponse, TaskUpdate
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
):
    """Возвращает список задач с фильтрацией, сортировкой и пагинацией."""
    return service.get_all_tasks(
        status=status,
        priority=priority,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task: TaskCreate,
    service: TaskService = Depends(get_task_service),
):
    """Создаёт новую задачу."""
    return service.create_task(task.model_dump())


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    update: TaskUpdate,
    service: TaskService = Depends(get_task_service),
):
    """Частично обновляет задачу."""
    return service.update_task(task_id, update)


@router.post("/{task_id}/assign", response_model=TaskResponse)
async def assign_task(
    task_id: int,
    request: AssignRequest,
    service: TaskService = Depends(get_task_service),
):
    """Назначает исполнителя задаче."""
    return service.assign_task(task_id, request.user_id)


@router.post("/{task_id}/archive", response_model=TaskResponse)
async def archive_task(
    task_id: int,
    service: TaskService = Depends(get_task_service),
):
    """Архивирует задачу."""
    return service.archive_task(task_id)


@router.post("/{task_id}/complete", response_model=TaskResponse)
async def complete_task(
    task_id: int,
    service: TaskService = Depends(get_task_service),
):
    """Закрывает задачу."""
    return service.complete_task(task_id)


@router.get("/summary", response_model=TaskSummaryResponse)
async def get_summary(
    service: TaskService = Depends(get_task_service),
):
    """Возвращает сводку по задачам."""
    return service.get_summary()


@router.get("/export")
async def export_tasks(
    format: str = "json",
    service: TaskService = Depends(get_task_service),
):
    """Выгружает все задачи в JSON или CSV."""

    result = service.export_tasks(format=format)

    if format == "csv":
        return PlainTextResponse(content=result, media_type="text/csv")

    return JSONResponse(content=result)


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    service: TaskService = Depends(get_task_service),
):
    """Возвращает задачу по ID."""
    return service.get_task_by_id(task_id)
