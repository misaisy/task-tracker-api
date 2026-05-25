import logging
from datetime import datetime, timezone
from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Optional
from app.settings import settings


class TaskCreate(BaseModel):
    """Модель для создания задачи."""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)
    priority: str = Field(default="medium", pattern="^(low|medium|high)$")


class TaskResponse(BaseModel):
    """Модель ответа с данными задачи."""
    id: int
    title: str
    description: Optional[str]
    priority: str
    status: str
    created_at: datetime


tasks_db: list[dict] = []
next_task_id: int = 1


log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
logging.basicConfig(
    level=log_level,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


app = FastAPI(title="Task Tracker API", version="0.1.0")

@app.on_event("startup")
async def startup_event():
    logger.info("=== Task Tracker API starting ===")
    logger.info("Environment: %s", settings.APP_ENV)
    logger.info("Port: %s", settings.APP_PORT)
    logger.info("Debug mode: %s", settings.DEBUG)
    logger.info("Log level: %s", settings.LOG_LEVEL)

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/tasks", response_model=TaskResponse, status_code=201)
async def create_task(task: TaskCreate):
    global next_task_id

    new_task = {
        "id": next_task_id,
        "title": task.title,
        "description": task.description,
        "priority": task.priority,
        "status": "todo",
        "created_at": datetime.now(timezone.utc),
    }

    tasks_db.append(new_task)
    next_task_id += 1

    logger.info("Task created: id=%d, title=%s", new_task["id"], new_task["title"])

    return new_task