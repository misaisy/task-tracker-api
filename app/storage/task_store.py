"""
Хранилище задач.
Слой: доступ к данным (storage).
"""
from datetime import UTC, datetime

from sqlalchemy import and_, case, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.core.constants import DEFAULT_PRIORITY, DEFAULT_STATUS
from app.models.orm import Task


class TaskStore:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, task_data: dict) -> dict:
        task = Task(
            title=task_data["title"],
            description=task_data.get("description"),
            priority=task_data.get("priority", DEFAULT_PRIORITY),
            status=DEFAULT_STATUS,
            owner_id=task_data.get("owner_id"),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        self.session.add(task)
        await self.session.flush()
        return self._to_dict(task)

    async def get_all(self) -> list[dict]:
        stmt = select(Task).order_by(Task.id)
        result = await self.session.execute(stmt)
        tasks = result.scalars().all()
        return [self._to_dict(t) for t in tasks]

    async def get_by_id(self, task_id: int) -> dict | None:
        task = await self.session.get(Task, task_id)
        return self._to_dict(task) if task else None

    async def get_by_id_with_relations(self, task_id: int) -> dict | None:
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
        task = result.unique().scalar_one_or_none()
        if not task:
            return None
        return self._to_dict_with_relations(task)

    async def get_filtered_tasks(
        self,
        status: str | None = None,
        priority: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> list[dict]:
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
                (Task.priority == "low", 0),
                (Task.priority == "medium", 1),
                (Task.priority == "high", 2),
                else_=3,
            )
        elif sort_by == "status":
            order_col = case(
                (Task.status == "TODO", 0),
                (Task.status == "IN_PROGRESS", 1),   # constants
                (Task.status == "REVIEW", 2),
                (Task.status == "DONE", 3),
                (Task.status == "ARCHIVED", 4),
                else_=5,
            )
        else:
            order_col = Task.created_at
        if order_direction == "desc":
            order_col = order_col.desc()
        stmt = stmt.order_by(order_col)

        result = await self.session.execute(stmt)
        tasks = result.scalars().all()
        return [self._to_dict(t) for t in tasks]

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

    async def update(self, task_id: int, data: dict) -> dict | None:
        task = await self.session.get(Task, task_id)
        if not task:
            return None
        for field, value in data.items():
            if hasattr(task, field) and field not in ("id", "created_at", "updated_at", "closed_at", "owner_id"):
                setattr(task, field, value)
        task.updated_at = datetime.now(UTC)
        await self.session.flush()
        return self._to_dict(task)

    async def assign(self, task_id: int, user_id: int) -> dict | None:
        task = await self.session.get(Task, task_id)
        if not task:
            return None
        if task.status == "TODO":
            task.status = "IN_PROGRESS"
        task.assignee_id = user_id
        task.updated_at = datetime.now(UTC)
        await self.session.flush()
        return self._to_dict(task)

    async def archive(self, task_id: int) -> dict | None:
        task = await self.session.get(Task, task_id)
        if not task:
            return None
        if task.status == "ARCHIVED":
            return None
        task.status = "ARCHIVED"
        task.updated_at = datetime.now(UTC)
        await self.session.flush()
        return self._to_dict(task)

    async def complete(self, task_id: int) -> dict | None:
        task = await self.session.get(Task, task_id)
        if not task:
            return None
        task.status = "DONE"
        task.closed_at = datetime.now(UTC)
        task.updated_at = datetime.now(UTC)
        await self.session.flush()
        return self._to_dict(task)

    async def commit(self):
        await self.session.commit()

    async def clear(self):
        await self.session.execute(delete(Task))

    def _to_dict(self, task: Task) -> dict:
        return {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "priority": task.priority,
            "status": task.status,
            "created_at": task.created_at,
            "updated_at": task.updated_at,
            "closed_at": task.closed_at,
            "owner_id": task.owner_id,
            "assignee_id": task.assignee_id,
        }

    def _to_dict_with_relations(self, task: Task) -> dict:
        result = self._to_dict(task)
        result["owner"] = self._user_to_dict(task.owner) if task.owner else None
        result["assignee"] = self._user_to_dict(task.assignee) if task.assignee else None
        result["comments"] = [
            {
                "id": c.id,
                "task_id": c.task_id,
                "text": c.text,
                "author_id": c.author_id,
                "created_at": c.created_at,
            }
            for c in task.comments
        ]
        return result

    def _user_to_dict(self, user) -> dict | None:
        if not user:
            return None
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "created_at": user.created_at,
        }
