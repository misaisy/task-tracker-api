"""
Хранилище задач.
Слой: доступ к данным (storage).
Зависит от: constants.
"""
from datetime import datetime, timezone

from app.constants import TASK_STATUS_TODO


class TaskStore:
    def __init__(self):
        self._tasks: list[dict] = []
        self._next_id: int = 1

    def add(self, task_data: dict) -> dict:
        """Добавляет задачу в хранилище и возвращает её с присвоенным id."""
        task = {
            "id": self._next_id,
            "title": task_data["title"],
            "description": task_data.get("description"),
            "priority": task_data.get("priority", "medium"),
            "status": TASK_STATUS_TODO,
            "created_at": datetime.now(timezone.utc),
        }
        self._tasks.append(task)
        self._next_id += 1
        return task

    def get_all(self) -> list[dict]:
        """Возвращает список всех задач."""
        return self._tasks

    def get_by_id(self, task_id: int) -> dict | None:
        """Возвращает задачу по ID или None, если не найдена."""
        for task in self._tasks:
            if task["id"] == task_id:
                return task
        return None

    def clear(self):
        """Очищает хранилище (для тестов)."""
        self._tasks.clear()
        self._next_id = 1

task_store = TaskStore()