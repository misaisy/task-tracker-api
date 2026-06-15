"""
Хранилище истории изменений задач (ORM).
Слой: доступ к данным (storage).
"""
from datetime import UTC, datetime
from sqlalchemy.orm import Session
from app.models_sql import TaskHistory

class TaskHistoryStore:
    def __init__(self, session: Session):
        self.session = session

    def add_entry(
        self,
        task_id: int,
        field: str,
        old_value: str | None,
        new_value: str | None,
    ) -> dict:
        entry = TaskHistory(
            task_id=task_id,
            field=field,
            old_value=old_value,
            new_value=new_value,
            changed_at=datetime.now(UTC),
        )
        self.session.add(entry)
        self.session.flush()
        return self._to_dict(entry)

    def get_by_task_id(self, task_id: int) -> list[dict]:
        entries = (
            self.session.query(TaskHistory)
            .filter(TaskHistory.task_id == task_id)
            .order_by(TaskHistory.changed_at)
            .all()
        )
        return [self._to_dict(e) for e in entries]

    def clear(self):
        self.session.query(TaskHistory).delete()

    def _to_dict(self, entry: TaskHistory) -> dict:
        return {
            "id": entry.id,
            "task_id": entry.task_id,
            "field": entry.field,
            "old_value": entry.old_value,
            "new_value": entry.new_value,
            "changed_at": entry.changed_at,
        }