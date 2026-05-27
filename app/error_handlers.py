from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.exceptions import (
    TaskTrackerError,
    TaskNotFoundError,
    UserNotFoundError,
    CommentNotFoundError,
    ValidationError,
)


async def task_tracker_error_handler(request: Request, exc: TaskTrackerError) -> JSONResponse:
    """Общий обработчик для всех ошибок приложения."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": str(exc)},
    )


async def task_not_found_handler(request: Request, exc: TaskNotFoundError) -> JSONResponse:
    """Обработчик: задача не найдена - 404."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc)},
    )


async def user_not_found_handler(request: Request, exc: UserNotFoundError) -> JSONResponse:
    """Обработчик: пользователь не найден - 404."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc)},
    )


async def comment_not_found_handler(request: Request, exc: CommentNotFoundError) -> JSONResponse:
    """Обработчик: комментарий не найден - 404."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc)},
    )


async def validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """Обработчик: ошибка валидации - 422."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": str(exc)},
    )