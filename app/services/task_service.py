"""
Сервисный слой для задач.
Слой: бизнес-логика (services).
Зависит от: storage.
"""
import logging

from app.storage.task_store import TaskStore
from app.exceptions import TaskNotFoundError

logger = logging.getLogger(__name__)


class TaskService:
    def __init__(self, store: TaskStore):
        self.store = store

    def get_all_tasks(self) -> list[dict]:
        """Возвращает список всех задач."""
        logger.debug("Getting all tasks")
        return self.store.get_all()

    def get_task_by_id(self, task_id: int) -> dict | None:
        """Возвращает задачу по ID или None."""
        task = self.store.get_by_id(task_id)
        if task is None:
            raise TaskNotFoundError(task_id)
        return task

    def create_task(self, task_data: dict) -> dict:
        """Создаёт новую задачу и возвращает её."""
        logger.debug("Creating task with data: %s", task_data)
        task = self.store.add(task_data)
        logger.info("Task created: id=%d, title=%s", task["id"], task["title"])
        return task