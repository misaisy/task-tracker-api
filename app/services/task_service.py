"""
Сервисный слой для задач.
Слой: бизнес-логика (services).
Зависит от: storage.
"""
import csv
import io
import logging
from datetime import UTC, datetime

from app.constants import (
    DEFAULT_PRIORITY,
    DEFAULT_STATUS,
    PRIORITY_HIGH,
    PRIORITY_LOW,
    PRIORITY_MEDIUM,
    TASK_STATUS_ARCHIVED,
    TASK_STATUS_DONE,
    TASK_STATUS_IN_PROGRESS,
    TASK_STATUS_REVIEW,
    TASK_STATUS_TODO,
)
from app.exceptions import ConflictError, TaskNotFoundError, UserNotFoundError, ValidationError
from app.models import TaskUpdate
from app.storage.task_history_store import TaskHistoryStore
from app.storage.task_store import TaskStore
from app.storage.user_store import UserStore

logger = logging.getLogger(__name__)


class TaskService:
    """Сервис для работы с задачами."""

    def __init__(self, store: TaskStore, history_store: TaskHistoryStore, user_store: UserStore):
        self.store = store
        self.history_store = history_store
        self.user_store = user_store

    def get_all_tasks(
        self,
        status: str | None = None,
        priority: str | None = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> dict:
        """
        Возвращает список задач с фильтрацией и пагинацией.
        """
        tasks = self.store.get_all()

        if status:
            tasks = [t for t in tasks if t["status"] == status]

        if priority:
            tasks = [t for t in tasks if t["priority"] == priority]

        allowed_sort_fields = {"created_at", "priority", "status"}
        reverse = sort_order.lower() == "desc"
        if sort_by not in allowed_sort_fields:
            sort_by = "created_at"
        if sort_by == "priority":
            priority_order = {PRIORITY_LOW: 0, PRIORITY_MEDIUM: 1, PRIORITY_HIGH: 2}
            tasks.sort(key=lambda t: priority_order.get(t.get("priority", DEFAULT_PRIORITY), 1), reverse=reverse)
        elif sort_by == "status":
            status_order = {
                TASK_STATUS_TODO: 0,
                TASK_STATUS_IN_PROGRESS: 1,
                TASK_STATUS_REVIEW: 2,
                TASK_STATUS_DONE: 3,
                TASK_STATUS_ARCHIVED: 4
            }
            tasks.sort(key=lambda t: status_order.get(t.get("status", DEFAULT_STATUS), 0), reverse=reverse)
        else:
            tasks.sort(key=lambda t: t.get(sort_by, ""), reverse=reverse)

        total = len(tasks)
        pages = (total + page_size - 1) // page_size
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
        owner_id = task_data.get("owner_id")
        if owner_id is not None:
            user = self.user_store.get_by_id(owner_id)
            if user is None:
                raise UserNotFoundError(owner_id)

        task = self.store.add(task_data)
        logger.info("Task created: id=%d, title=%s", task["id"], task["title"])
        return task

    def update_task(self, task_id: int, update_data: TaskUpdate) -> dict:
        """
        Частично обновляет задачу.
        """
        task = self.get_task_by_id(task_id)

        if task.get("status") == TASK_STATUS_ARCHIVED:
            raise ValidationError("Cannot modify archived task")

        changes = update_data.model_dump(exclude_unset=True)

        for field, value in changes.items():
            old_val = task.get(field)

            if field == "description" and value is None:
                task["description"] = None
                new_val = None
            elif value is not None:
                task[field] = value
                new_val = value
            else:
                continue
            self._record_change(task_id, field, old_val, new_val)

        logger.info("Task updated: id=%d, fields=%s", task_id, update_data.model_fields_set)
        return task

    def assign_task(self, task_id: int, user_id: int) -> dict:
        """
        Назначает исполнителя задаче.
        """
        task = self.get_task_by_id(task_id)

        if task.get("status") == TASK_STATUS_ARCHIVED:
            raise ConflictError("Cannot assign archived task")

        user = self.user_store.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(user_id)

        old_assignee = task.get("assignee_id")
        old_status = task.get("status")
        result = self.store.assign(task_id, user_id)

        if result is None:
            raise RuntimeError("Task disappeared")

        if old_assignee != result["assignee_id"]:
            self._record_change(task_id, "assignee_id", old_assignee, result["assignee_id"])

        if old_status != result["status"]:
            self._record_change(task_id, "status", old_status, result["status"])

        logger.info("Task assigned: task_id=%d, user_id=%d", task_id, user_id)
        return result  # type: ignore[return-value]

    def archive_task(self, task_id: int) -> dict:
        """Архивирует задачу."""
        task = self.get_task_by_id(task_id)

        old_status = task.get("status")
        result = self.store.archive(task_id)
        if result is None:
            raise ConflictError("Task is already archived")

        self._record_change(task_id, "status", old_status, result["status"])
        logger.info("Task archived: task_id=%d", task_id)
        return result

    def get_summary(self) -> dict:
        """Возвращает сводку по задачам: количество по статусам и приоритетам."""
        tasks = self.store.get_all()

        by_status = {
            TASK_STATUS_TODO: 0,
            TASK_STATUS_IN_PROGRESS: 0,
            TASK_STATUS_REVIEW: 0,
            TASK_STATUS_DONE: 0,
            TASK_STATUS_ARCHIVED: 0
        }

        by_priority = {PRIORITY_LOW: 0, PRIORITY_MEDIUM: 0, PRIORITY_HIGH: 0}

        for task in tasks:
            status = task.get("status", DEFAULT_STATUS)
            if status in by_status:
                by_status[status] += 1

            priority = task.get("priority", DEFAULT_PRIORITY)
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

        return {
            "exported_at": datetime.now(UTC).isoformat(),
            "format": "json",
            "tasks": tasks,
        }

    def complete_task(self, task_id: int) -> dict:
        """Закрывает задачу. Нельзя закрыть архивную или уже закрытую."""
        task = self.get_task_by_id(task_id)

        if task.get("status") == TASK_STATUS_DONE:
            raise ConflictError("Task is already done")
        if task.get("status") == TASK_STATUS_ARCHIVED:
            raise ConflictError("Cannot complete archived task")

        old_status = task.get("status")
        result = self.store.complete(task_id)
        self._record_change(task_id, "status", old_status, result["status"])

        logger.info("Task completed: id=%d", task_id)
        return result

    def _record_change(self, task_id: int, field: str, old_value, new_value):
        self.history_store.add_entry(
            task_id=task_id,
            field=field,
            old_value=str(old_value) if old_value is not None else None,
            new_value=str(new_value) if new_value is not None else None,
        )
