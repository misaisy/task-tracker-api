"""
Хранилище задач.
Слой: доступ к данным (storage).
Зависит от: constants.
"""
from datetime import UTC, datetime

from app.constants import TASK_STATUS_TODO


class TaskStore:
    _tasks: dict[int, dict]
    _next_id: int

    def __init__(self):
        self._tasks = {}
        self._next_id = 1

    def add(self, task_data: dict) -> dict:
        """Добавляет задачу в хранилище и возвращает её с присвоенным id."""
        task = {
            "id": self._next_id,
            "title": task_data["title"],
            "description": task_data.get("description"),
            "priority": task_data.get("priority", "medium"),
            "status": TASK_STATUS_TODO,
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
            "closed_at": None,
            "owner_id": task_data.get("owner_id"),
            "assignee_id": None,
        }
        self._tasks[self._next_id] = task
        self._next_id += 1
        return task

    def get_all(self) -> list[dict]:
        """Возвращает список всех задач."""
        return list(self._tasks.values())

    def get_by_id(self, task_id: int) -> dict | None:
        """Возвращает задачу по ID или None, если не найдена."""
        return self._tasks.get(task_id)

    def update(self, task_id: int, data: dict) -> dict | None:
        task = self._tasks.get(task_id)
        if task is not None:
            task.update(data)
            self._touch(task_id)
        return task

    def assign(self, task_id: int, user_id: int) -> dict | None:
        """Назначает исполнителя задаче."""
        task = self._tasks.get(task_id)
        if task is None:
            return None
        task["assignee_id"] = user_id
        if task.get("status") == "TODO":
            task["status"] = "IN_PROGRESS"
        self._touch(task_id)
        return task

    def archive(self, task_id: int) -> dict | None:
        """Архивирует задачу."""
        task = self._tasks.get(task_id)
        if task is None:
            return None
        if task.get("status") == "archived":
            return None
        task["status"] = "archived"
        self._touch(task_id)
        return task

    def clear(self):
        """Очищает хранилище (для тестов)."""
        self._tasks.clear()
        self._next_id = 1

    def complete(self, task_id: int) -> dict | None:
        """Закрывает задачу. Возвращает обновлённую задачу или None, если не найдена."""
        task = self._tasks.get(task_id)
        if task is None:
            return None
        task["status"] = "DONE"
        task["closed_at"] = datetime.now(UTC)
        self._touch(task_id)
        return task

    def _touch(self, task_id: int) -> None:
        """Обновляет updated_at у задачи, если она существует."""
        task = self._tasks.get(task_id)
        if task:
            task["updated_at"] = datetime.now(UTC)


task_store = TaskStore()  # type: ignore[no-untyped-call]
