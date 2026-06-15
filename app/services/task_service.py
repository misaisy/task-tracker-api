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
    TASK_STATUS_ARCHIVED,
    TASK_STATUS_DONE,
)
from app.exceptions import ConflictError, TaskNotFoundError, UserNotFoundError, ValidationError
from app.models import TaskUpdate
from app.storage.task_history_store import TaskHistoryStore
from app.storage.task_store import TaskStore
from app.storage.user_store import UserStore

logger = logging.getLogger(__name__)


class TaskService:
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
        Возвращает список задач с фильтрацией, сортировкой и пагинацией.
        """
        tasks = self.store.get_filtered_tasks(
            status=status,
            priority=priority,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        total = len(tasks)
        pages = (total + page_size - 1) // page_size
        start = (page - 1) * page_size
        end = start + page_size
        items = tasks[start:end]

        logger.debug(
            "Getting tasks: status=%s, priority=%s, sort=%s %s, page=%d, total=%d",
            status, priority, sort_by, sort_order, page, total,
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
        self.store.commit()
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

        self.store.commit()
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

        self.store.commit()
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
        self.store.commit()
        logger.info("Task archived: task_id=%d", task_id)
        return result

    def get_summary(self) -> dict:
        return self.store.get_summary()

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

        self.store.commit()
        logger.info("Task completed: id=%d", task_id)
        return result

    def _record_change(self, task_id: int, field: str, old_value, new_value):
        self.history_store.add_entry(
            task_id=task_id,
            field=field,
            old_value=str(old_value) if old_value is not None else None,
            new_value=str(new_value) if new_value is not None else None,
        )
    
    def get_task_with_relations(self, task_id: int) -> dict:
        """Возвращает задачу с владельцем, исполнителем и комментариями."""
        task = self.store.get_by_id_with_relations(task_id)
        if task is None:
            raise TaskNotFoundError(task_id)
        return task
