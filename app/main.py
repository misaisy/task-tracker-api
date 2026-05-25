import logging
from datetime import datetime, timezone
from fastapi import FastAPI
from app.settings import settings
from app.models import TaskCreate, TaskResponse


TASK_STATUS_TODO = "TODO"
TASK_STATUS_IN_PROGRESS = "IN_PROGRESS"
TASK_STATUS_REVIEW = "REVIEW"
TASK_STATUS_DONE = "DONE"
TASK_STATUS_ARCHIVED = "ARCHIVED"


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
    """
    Создаёт новую задачу.

    Валидация:
    - title: обязательный, от 1 до 200 символов
    - description: опциональный, до 1000 символов
    - priority: low, medium или high (по умолчанию medium)

    Возвращает:
    - 201 Created с объектом задачи
    - 422 Unprocessable Entity при ошибке валидации
    """
    
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

@app.get("/tasks/count")
async def count_tasks():
    """Возвращает общее количество задач."""
    return {"count": len(tasks_db)}

@app.get("/tasks", response_model=list[TaskResponse])
async def list_tasks():
    """Возвращает список всех задач."""
    return tasks_db

@app.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int):
    """Возвращает задачу по ID."""
    for task in tasks_db:
        if task["id"] == task_id:
            return task