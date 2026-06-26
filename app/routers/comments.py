"""
Роутер для комментариев.
Слой: HTTP (routers).
Зависит от: services, models, dependencies.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.dependencies import get_comment_service, get_current_user, require_owner_or_admin
from app.models.orm import Task, User
from app.models.schemas import CommentCreate, CommentResponse
from app.services.comment_service import CommentService

router = APIRouter(prefix="/tasks", tags=["comments"])


@router.post("/{task_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    task_id: UUID,
    comment: CommentCreate,
    service: CommentService = Depends(get_comment_service),
    current_user: User = Depends(get_current_user),
    task: Task = Depends(require_owner_or_admin),
):
    """Добавляет комментарий к задаче."""
    return await service.create_comment(comment, task_id=task_id, author_id=current_user.id)


@router.get("/{task_id}/comments", response_model=list[CommentResponse])
async def list_comments(
    task_id: UUID,
    service: CommentService = Depends(get_comment_service),
    current_user: User = Depends(get_current_user),
    task: Task = Depends(require_owner_or_admin),
):
    """Возвращает список комментариев к задаче."""
    return await service.get_comments_by_task(task_id, current_user)
