"""
Сервисный слой для задач.
Слой: бизнес-логика (services).
Зависит от: storage.
"""
import csv
import io
import logging
from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound

from app.core.constants import Status
from app.errors.exceptions import ConflictError, TaskNotFoundError, UserNotFoundError
from app.models.orm import Task
from app.models.schemas import TaskUpdate
from app.storage.task_history_store import TaskHistoryStore
from app.storage.task_store import TaskStore
from app.storage.user_store import UserStore

logger = logging.getLogger(__name__)


class TaskService:
    def __init__(self, store: TaskStore, history_store: TaskHistoryStore, user_store: UserStore):
        self.store = store
        self.history_store = history_store
        self.user_store = user_store

    async def get_all_tasks(
        self,
        status: str | None = None,
        priority: str | None = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> dict:
        tasks = await self.store.get_filtered_tasks(
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

    async def get_task_by_id(self, task_id: int) -> Task:
        try:
            return await self.store.get_by_id(task_id)
        except NoResultFound as e:
            raise TaskNotFoundError(task_id) from e

    async def get_task_with_relations(self, task_id: int) -> Task:
        try:
            return await self.store.get_by_id_with_relations(task_id)
        except NoResultFound as e:
            raise TaskNotFoundError(task_id) from e

    async def create_task(self, task_data: dict) -> Task:
        owner_id = task_data.get("owner_id")
        if owner_id is not None:
            try:
                await self.user_store.get_by_id(owner_id)
            except NoResultFound as e:
                raise UserNotFoundError(owner_id) from e

        try:
            task = await self.store.add(task_data)
            await self.store.commit()
        except IntegrityError:
            await self.store.session.rollback()
            raise ConflictError("Cannot create task") from None

        logger.info("Task created: id=%d, title=%s", task.id, task.title)
        return task

    async def update_task(self, task_id: int, update_data: TaskUpdate) -> Task:
        task = await self.get_task_by_id(task_id)
        if task.status == Status.ARCHIVED:
            raise ConflictError("Cannot modify archived task")

        changes = update_data.model_dump(exclude_unset=True)
        for field, value in changes.items():
            old_val = getattr(task, field, None)

            if field == "description" and value is None:
                new_val = None
            elif value is not None:
                new_val = value
            else:
                continue
            if str(old_val) != str(new_val):
                await self._record_change(task_id, field, old_val, new_val)

        task = await self.store.update(task_id, changes)
        await self.store.commit()
        logger.info("Task updated: id=%d, fields=%s", task_id, update_data.model_fields_set)
        return task

    async def assign_task(self, task_id: int, user_id: int) -> Task:
        task = await self.get_task_by_id(task_id)

        if task.status == Status.ARCHIVED:
            raise ConflictError("Cannot assign archived task")

        try:
            await self.user_store.get_by_id(user_id)
        except NoResultFound as e:
            raise UserNotFoundError(user_id) from e

        old_assignee = task.assignee_id
        old_status = task.status
        result = await self.store.assign(task_id, user_id)

        if old_assignee != result.assignee_id:
            await self._record_change(task_id, "assignee_id", old_assignee, result.assignee_id)

        if old_status != result.status:
            await self._record_change(task_id, "status", old_status, result.status)

        await self.store.commit()
        logger.info("Task assigned: task_id=%d, user_id=%d", task_id, user_id)
        return result

    async def archive_task(self, task_id: int) -> Task:
        task = await self.get_task_by_id(task_id)

        if task.status == Status.ARCHIVED:
            raise ConflictError("Task is already archived")

        old_status = task.status
        result = await self.store.archive(task_id)

        await self._record_change(task_id, "status", old_status, result.status)
        await self.store.commit()
        logger.info("Task archived: task_id=%d", task_id)
        return result

    async def complete_task(self, task_id: int) -> Task:
        task = await self.get_task_by_id(task_id)

        if task.status == Status.DONE:
            raise ConflictError("Task is already done")
        if task.status == Status.ARCHIVED:
            raise ConflictError("Cannot complete archived task")

        old_status = task.status
        result = await self.store.complete(task_id)
        await self._record_change(task_id, "status", old_status, result.status)

        await self.store.commit()
        logger.info("Task completed: id=%d", task_id)
        return result

    async def get_summary(self) -> dict:
        return await self.store.get_summary()

    async def export_tasks(self, format: str = "json") -> dict | str:
        tasks = await self.store.get_all()

        if format == "csv":
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=["id", "title", "status", "priority", "created_at"])
            writer.writeheader()
            for task in tasks:
                writer.writerow({
                    "id": str(task.id),
                    "title": task.title,
                    "status": task.status,
                    "priority": task.priority,
                    "created_at": task.created_at,
                })
            return output.getvalue()

        return {
            "exported_at": datetime.now(UTC).isoformat(),
            "format": "json",
            "tasks": [
                {
                    "id": str(t.id),
                    "title": t.title,
                    "description": t.description,
                    "priority": t.priority,
                    "status": t.status,
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                    "updated_at": t.updated_at.isoformat() if t.updated_at else None,
                    "closed_at": t.closed_at.isoformat() if t.closed_at else None,
                    "owner_id": str(t.owner_id),
                    "assignee_id": str(t.assignee_id),
                }
                for t in tasks
            ],
        }

    async def _record_change(self, task_id: int, field: str, old_value, new_value):
        await self.history_store.add_entry(
            task_id=task_id,
            field=field,
            old_value=str(old_value) if old_value is not None else None,
            new_value=str(new_value) if new_value is not None else None,
        )
