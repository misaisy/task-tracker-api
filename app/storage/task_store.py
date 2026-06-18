"""
Хранилище задач.
Слой: доступ к данным (storage).
"""
from datetime import UTC, datetime

from sqlalchemy import and_, case, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.core.constants import (
    Priority,
    Status,
)
from app.models.orm import Task


class TaskStore:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, task_data: dict) -> Task:
        task = Task(
            title=task_data["title"],
            description=task_data.get("description"),
            priority=task_data.get("priority", Priority.MEDIUM),
            status=Status.TODO,
            owner_id=task_data.get("owner_id"),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        self.session.add(task)
        await self.session.flush()
        return task

    async def get_all(self) -> list[Task]:
        stmt = select(Task).order_by(Task.id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, task_id: int) -> Task:
        return await self.session.get_one(Task, task_id)

    async def get_by_id_with_relations(self, task_id: int) -> Task:
        stmt = (
            select(Task)
            .options(
                joinedload(Task.owner),
                joinedload(Task.assignee),
                selectinload(Task.comments)
            )
            .where(Task.id == task_id)
        )
        result = await self.session.execute(stmt)
        return result.unique().scalar_one()

    async def get_filtered_tasks(
        self,
        status: str | None = None,
        priority: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> list[Task]:
        stmt = select(Task)
        conditions = []
        if status:
            conditions.append(Task.status == status)
        if priority:
            conditions.append(Task.priority == priority)
        if conditions:
            stmt = stmt.where(and_(*conditions))

        order_direction = "desc" if sort_order.lower() == "desc" else "asc"
        if sort_by == "priority":
            order_col = case(
                (Task.priority == Priority.LOW, 0),
                (Task.priority == Priority.MEDIUM, 1),
                (Task.priority == Priority.HIGH, 2),
                else_=3,
            )
        elif sort_by == "status":
            order_col = case(
                (Task.status == Status.TODO, 0),
                (Task.status == Status.IN_PROGRESS, 1),
                (Task.status == Status.REVIEW, 2),
                (Task.status == Status.DONE, 3),
                (Task.status == Status.ARCHIVED, 4),
                else_=5,
            )
        else:
            order_col = Task.created_at
        if order_direction == "desc":
            order_col = order_col.desc()
        stmt = stmt.order_by(order_col)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_summary(self) -> dict:
        status_stmt = (
            select(Task.status, func.count(Task.id))
            .group_by(Task.status)
        )
        status_result = await self.session.execute(status_stmt)
        by_status = {row.status: row.count for row in status_result}

        priority_stmt = (
            select(Task.priority, func.count(Task.id))
            .group_by(Task.priority)
        )
        priority_result = await self.session.execute(priority_stmt)
        by_priority = {row.priority: row.count for row in priority_result}

        total = await self.session.scalar(select(func.count(Task.id)))

        return {
            "total": total,
            "by_status": by_status,
            "by_priority": by_priority,
        }

    async def update(self, task_id: int, data: dict) -> Task:
        task = await self.session.get_one(Task, task_id)
        for field, value in data.items():
            setattr(task, field, value)
        task.updated_at = datetime.now(UTC)
        await self.session.flush()
        return task

    async def assign(self, task_id: int, user_id: int) -> Task:
        task = await self.session.get_one(Task, task_id)
        if task.status == Status.TODO:
            task.status = Status.IN_PROGRESS
        task.assignee_id = user_id
        task.updated_at = datetime.now(UTC)
        await self.session.flush()
        return task

    async def archive(self, task_id: int) -> Task:
        task = await self.session.get_one(Task, task_id)
        task.status = Status.ARCHIVED
        task.updated_at = datetime.now(UTC)
        await self.session.flush()
        return task

    async def complete(self, task_id: int) -> Task:
        task = await self.session.get_one(Task, task_id)
        task.status = Status.DONE
        task.closed_at = datetime.now(UTC)
        task.updated_at = datetime.now(UTC)
        await self.session.flush()
        return task

    async def commit(self):
        await self.session.commit()

    async def clear(self):
        await self.session.execute(delete(Task))
