"""
Роутер для комментариев.
Слой: HTTP (routers).
Зависит от: services, models, dependencies.
"""
from fastapi import APIRouter, Depends, status

from app.dependencies import get_comment_service
from app.models import CommentCreate, CommentResponse
from app.services.comment_service import CommentService

router = APIRouter(prefix="/comments", tags=["comments"])


@router.post("/{task_id}", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    task_id: int,
    comment: CommentCreate,
    service: CommentService = Depends(get_comment_service),
):
    """Добавляет комментарий к задаче."""
    data = comment.model_dump()
    data["task_id"] = task_id
    return service.create_comment(data)


@router.get("/{task_id}", response_model=list[CommentResponse])
async def list_comments(
    task_id: int,
    service: CommentService = Depends(get_comment_service),
):
    """Возвращает список комментариев к задаче."""
    return service.get_comments_by_task(task_id)
