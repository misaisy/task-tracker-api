from datetime import UTC, datetime


class TaskHistoryStore:
    def __init__(self):
        self._history: dict[int, list[dict]] = {}
        self._next_id: int = 1

    def add_entry(
        self,
        task_id: int,
        field: str,
        old_value: str | None,
        new_value: str | None,
    ) -> dict:
        entry = {
            "id": self._next_id,
            "task_id": task_id,
            "field": field,
            "old_value": old_value,
            "new_value": new_value,
            "changed_at": datetime.now(UTC),
        }
        self._history.setdefault(task_id, []).append(entry)
        self._next_id += 1
        return entry

    def get_by_task_id(self, task_id: int) -> list[dict]:
        return self._history.get(task_id, [])


task_history_store = TaskHistoryStore()
