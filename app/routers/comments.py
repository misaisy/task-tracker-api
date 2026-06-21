"""
Роутер для комментариев.
Слой: HTTP (routers).
Зависит от: services, models, dependencies.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.dependencies import get_comment_service
from app.models.schemas import CommentCreate, CommentResponse
from app.services.comment_service import CommentService

router = APIRouter(prefix="/tasks", tags=["comments"])


@router.post("/{task_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    task_id: UUID,
    comment: CommentCreate,
    service: CommentService = Depends(get_comment_service),
):
    """Добавляет комментарий к задаче."""
    data = comment.model_dump(mode='json')
    data["task_id"] = task_id
    return await service.create_comment(data)


@router.get("/{task_id}/comments", response_model=list[CommentResponse])
async def list_comments(
    task_id: UUID,
    service: CommentService = Depends(get_comment_service),
):
    """Возвращает список комментариев к задаче."""
    return await service.get_comments_by_task(task_id)
