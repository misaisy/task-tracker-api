"""
Хранилище истории изменений задач.
Слой: доступ к данным (storage).
"""
from datetime import UTC, datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.orm import TaskHistory


class TaskHistoryStore:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_entry(
        self,
        task_id: int,
        field: str,
        old_value: str | None,
        new_value: str | None,
    ) -> TaskHistory:
        entry = TaskHistory(
            task_id=task_id,
            field=field,
            old_value=old_value,
            new_value=new_value,
            changed_at=datetime.now(UTC),
        )
        self.session.add(entry)
        await self.session.flush()
        return entry

    async def get_by_task_id(self, task_id: int) -> list[TaskHistory]:
        stmt = (
            select(TaskHistory)
            .where(TaskHistory.task_id == task_id)
            .order_by(TaskHistory.changed_at)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def clear(self):
        await self.session.execute(delete(TaskHistory))
