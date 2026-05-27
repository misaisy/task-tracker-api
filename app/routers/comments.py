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


@router.post("/", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(comment: CommentCreate, service: CommentService = Depends(get_comment_service)):
    return service.create_comment(comment.model_dump())


@router.get("/", response_model=list[CommentResponse])
async def list_comments(task_id: int, service: CommentService = Depends(get_comment_service)):
    return service.get_comments_by_task(task_id)