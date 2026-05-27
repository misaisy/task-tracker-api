"""
Сервисный слой для задач.
Слой: бизнес-логика (services).
Зависит от: storage.
"""
"""
Сервисный слой для задач.
Содержит бизнес-логику: получение списка, создание, обновление.
"""
import logging
import math

from app.exceptions import TaskNotFoundError
from app.storage.task_store import TaskStore

logger = logging.getLogger(__name__)


class TaskService:
    """Сервис для работы с задачами."""

    def __init__(self, store: TaskStore):
        self.store = store

    def get_all_tasks(self, status: str | None = None, priority: str | None = None, page: int = 1, page_size: int = 20) -> dict:
        """
        Возвращает список задач с фильтрацией и пагинацией.
        """
        tasks = self.store.get_all()

        if status:
            tasks = [t for t in tasks if t["status"] == status]

        if priority:
            tasks = [t for t in tasks if t["priority"] == priority]

        total = len(tasks)
        pages = max(1, math.ceil(total / page_size))
        start = (page - 1) * page_size
        end = start + page_size
        items = tasks[start:end]

        logger.debug(
            "Getting tasks: status=%s, priority=%s, page=%d, total=%d",
            status, priority, page, total,
        )

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": pages,
        }

    def get_task_by_id(self, task_id: int) -> dict:
        """Возвращает задачу по ID или выбрасывает TaskNotFoundError."""
        task = self.store.get_by_id(task_id)
        if task is None:
            raise TaskNotFoundError(task_id)
        return task

    def create_task(self, task_data: dict) -> dict:
        """Создаёт новую задачу и возвращает её."""
        task = self.store.add(task_data)
        logger.info("Task created: id=%d, title=%s", task["id"], task["title"])
        return task

    def update_task(self, task_id: int, update_data: TaskUpdate) -> dict:
        """
        Частично обновляет задачу.
        """
        task = self.get_task_by_id(task_id)

        if task.get("status") == "archived":
            from app.exceptions import ValidationError
            raise ValidationError("Cannot modify archived task")

        forbidden_fields = {"id", "created_at"}

        for field in update_data.model_fields_set:
            if field in forbidden_fields:
                continue

            value = getattr(update_data, field)

            if field == "description" and value is None:
                task["description"] = None
            elif value is not None:
                task[field] = value

        logger.info("Task updated: id=%d, fields=%s", task_id, update_data.model_fields_set)
        return task
    
    def assign_task(self, task_id: int, user_id: int) -> dict:
        """
        Назначает исполнителя задаче.
        """
        task = self.get_task_by_id(task_id)

        if task.get("status") == "archived":
            from app.exceptions import ValidationError
            raise ValidationError("Cannot assign archived task")

        result = self.store.assign(task_id, user_id)
        logger.info("Task assigned: task_id=%d, user_id=%d", task_id, user_id)
        return result

    def archive_task(self, task_id: int) -> dict:
        """Архивирует задачу."""
        task = self.get_task_by_id(task_id)

        result = self.store.archive(task_id)
        if result is None:
            from app.exceptions import ValidationError
            raise ValidationError("Task is already archived")

        logger.info("Task archived: task_id=%d", task_id)
        return result
    
    def get_summary(self) -> dict:
        """Возвращает сводку по задачам: количество по статусам и приоритетам."""
        tasks = self.store.get_all()

        by_status = {"TODO": 0, "IN_PROGRESS": 0, "REVIEW": 0, "DONE": 0, "ARCHIVED": 0}
        by_priority = {"low": 0, "medium": 0, "high": 0}

        for task in tasks:
            status = task.get("status", "TODO")
            if status in by_status:
                by_status[status] += 1

            priority = task.get("priority", "medium")
            if priority in by_priority:
                by_priority[priority] += 1

        return {
            "total": len(tasks),
            "by_status": by_status,
            "by_priority": by_priority,
        }


    def export_tasks(self, format: str = "json") -> dict | str:
        """Выгружает все задачи в указанном формате."""
        tasks = self.store.get_all()

        if format == "csv":
            import io, csv

            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=["id", "title", "status", "priority", "created_at"])
            writer.writeheader()
            for task in tasks:
                writer.writerow({
                    "id": task["id"],
                    "title": task["title"],
                    "status": task["status"],
                    "priority": task["priority"],
                    "created_at": task["created_at"],
                })
            return output.getvalue()

        from datetime import datetime, timezone

        return {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "format": "json",
            "tasks": tasks,
        }