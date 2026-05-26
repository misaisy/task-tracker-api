import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, status

from app.constants import TASK_STATUS_TODO
from app.models import TaskCreate, TaskResponse
from app.settings import settings


LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

logging.basicConfig(
    level=LOG_LEVELS.get(settings.LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


tasks_db: list[dict] = []
next_task_id: int = 1


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Жизненный цикл приложения."""
    logger.info("=== Task Tracker API starting ===")
    logger.info("Host: %s", settings.APP_HOST)
    logger.info("Port: %s", settings.APP_PORT)
    logger.info("Debug mode: %s", settings.DEBUG)
    logger.info("Log level: %s", settings.LOG_LEVEL)

    yield

    logger.info("=== Task Tracker API shutting down ===")


app = FastAPI(
    title="Task Tracker API",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(task: TaskCreate):
    """Создаёт новую задачу."""
    global next_task_id

    new_task = {
        "id": next_task_id,
        "title": task.title,
        "description": task.description,
        "priority": task.priority,
        "status": TASK_STATUS_TODO,
        "created_at": datetime.now(timezone.utc),
    }

    tasks_db.append(new_task)
    next_task_id += 1

    logger.info("Task created: id=%d, title=%s", new_task["id"], new_task["title"])

    return new_task


@app.get("/tasks", response_model=list[TaskResponse])
async def list_tasks():
    """Возвращает список всех задач."""
    return tasks_db


@app.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int):
    """Возвращает задачу по ID"""
    for task in tasks_db:
        if task["id"] == task_id:
            return task
