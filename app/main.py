import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import settings
from app.dependencies import get_settings
from app.error_handlers import (
    comment_not_found_handler,
    task_not_found_handler,
    task_tracker_error_handler,
    user_not_found_handler,
    validation_error_handler,
)
from app.exceptions import (
    CommentNotFoundError,
    TaskNotFoundError,
    TaskTrackerError,
    UserNotFoundError,
    ValidationError,
)
from app.routers.comments import router as comments_router
from app.routers.tasks import router as tasks_router
from app.routers.users import router as users_router

LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

logging.basicConfig(
    level=LOG_LEVELS.get(settings.LOG_LEVEL, logging.INFO),  # type: ignore[attr-defined]
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


tasks_db: list[dict] = []
next_task_id: int = 1


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[no-untyped-def]
    """Жизненный цикл приложения."""
    settings = get_settings()
    logger.info("=== Task Tracker API starting ===")
    logger.info("Host: %s", settings.APP_HOST)
    logger.info("Port: %s", settings.APP_PORT)
    logger.info("Debug mode: %s", settings.DEBUG)
    logger.info("Log level: %s", settings.LOG_LEVEL)

    try:
        yield
    finally:
        logger.info("=== Task Tracker API shutting down ===")


app = FastAPI(title="Task Tracker API", version="0.1.0", lifespan=lifespan)

app.add_exception_handler(TaskTrackerError, task_tracker_error_handler)      # type: ignore[arg-type]
app.add_exception_handler(TaskNotFoundError, task_not_found_handler)         # type: ignore[arg-type]
app.add_exception_handler(UserNotFoundError, user_not_found_handler)         # type: ignore[arg-type]
app.add_exception_handler(CommentNotFoundError, comment_not_found_handler)   # type: ignore[arg-type]
app.add_exception_handler(ValidationError, validation_error_handler)         # type: ignore[arg-type]

app.include_router(tasks_router)
app.include_router(users_router)
app.include_router(comments_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
