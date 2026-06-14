from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.exceptions import (
    CommentNotFoundError,
    ConflictError,
    TaskNotFoundError,
    TaskTrackerError,
    UserNotFoundError,
    ValidationError,
)
from app.models import ErrorDetail, ErrorResponse


def task_tracker_error_handler(request: Request, exc: TaskTrackerError) -> JSONResponse:
    """Общий обработчик для всех непредвиденных ошибок приложения."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error_code="INTERNAL_ERROR",
            details=str(exc),
        ).model_dump(),
    )


def task_not_found_handler(request: Request, exc: TaskNotFoundError) -> JSONResponse:
    """Обработчик: задача не найдена - 404."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=ErrorResponse(
            error_code="TASK_NOT_FOUND",
            details=str(exc),
        ).model_dump(),
    )


def user_not_found_handler(request: Request, exc: UserNotFoundError) -> JSONResponse:
    """Обработчик: пользователь не найден - 404."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=ErrorResponse(
            error_code="USER_NOT_FOUND",
            details=str(exc),
        ).model_dump(),
    )


def comment_not_found_handler(request: Request, exc: CommentNotFoundError) -> JSONResponse:
    """Обработчик: комментарий не найден - 404."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=ErrorResponse(
            error_code="COMMENT_NOT_FOUND",
            details=str(exc),
        ).model_dump(),
    )


def validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """Обработчик: ошибка валидации - 422."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            error_code="VALIDATION_ERROR",
            details=str(exc),
        ).model_dump(),
    )


def conflict_error_handler(request: Request, exc: ConflictError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=ErrorResponse(
            error_code="CONFLICT",
            details=str(exc),
        ).model_dump(),
    )


def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Обработчик ошибок Pydantic-валидации (422)."""
    details = []
    for e in exc.errors():
        loc = [str(item) for item in e["loc"]]
        details.append(ErrorDetail(loc=loc, msg=e["msg"]))
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            error_code="VALIDATION_ERROR",
            details=details,
        ).model_dump(),
    )
