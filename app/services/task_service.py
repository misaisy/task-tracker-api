"""
Сервисный слой для задач.
Слой: бизнес-логика (services).
Зависит от: storage.
"""
import logging
import time
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound

from app.core.constants import Role, Status
from app.errors.exceptions import ConflictError, TaskNotFoundError, UserNotFoundError
from app.models.orm import Task, User
from app.models.schemas import TaskCreate, TaskUpdate
from app.services.notification_service import NotificationService
from app.storage.task_history_store import TaskHistoryStore
from app.storage.task_store import TaskStore
from app.storage.user_store import UserStore

logger = logging.getLogger(__name__)


class TaskService:
    def __init__(
        self,
        store: TaskStore,
        history_store: TaskHistoryStore,
        user_store: UserStore,
        notification_service: NotificationService,
    ):
        self.store = store
        self.history_store = history_store
        self.user_store = user_store
        self.notification_service = notification_service

    async def get_all_tasks(
        self,
        status: str | None = None,
        priority: str | None = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        owner_id: UUID | None = None,
    ) -> dict:
        tasks = await self.store.get_filtered_tasks(
            status=status,
            priority=priority,
            sort_by=sort_by,
            sort_order=sort_order,
            owner_id=owner_id,
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

    async def get_task_by_id(self, task_id: UUID) -> Task:
        try:
            return await self.store.get_by_id(task_id)
        except NoResultFound as e:
            raise TaskNotFoundError(task_id) from e

    async def get_task_with_relations(self, task_id: UUID) -> Task:
        try:
            return await self.store.get_by_id_with_relations(task_id)
        except NoResultFound as e:
            raise TaskNotFoundError(task_id) from e

    async def create_task(self, task_data: TaskCreate, owner_id: UUID) -> Task:
        data = task_data.model_dump(mode='json')
        data["owner_id"] = owner_id

        try:
            task = await self.store.add(data)
            await self.store.commit()
        except IntegrityError:
            await self.store.session.rollback()
            raise ConflictError("Cannot create task") from None

        logger.info("Task created: id=%s, title=%s", task.id, task.title)
        return task

    async def update_task(self, task_id: UUID, update_data: TaskUpdate) -> Task:
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
        logger.info("Task updated: id=%s, fields=%s", task_id, update_data.model_fields_set)
        return task

    async def assign_task(self, task_id: UUID, user_id: UUID, current_user: User) -> Task:
        task = await self.get_task_by_id(task_id)

        if task.status == Status.ARCHIVED:
            raise ConflictError("Cannot assign archived task")

        try:
            await self.user_store.get_by_id(user_id)
        except NoResultFound as e:
            raise UserNotFoundError(user_id) from e

        if current_user.role != Role.ADMIN and user_id != current_user.id:
            raise ConflictError("Cannot assign someone else")

        old_assignee = task.assignee_id
        old_status = task.status
        result = await self.store.assign(task_id, user_id)

        if old_assignee != result.assignee_id:
            await self._record_change(task_id, "assignee_id", old_assignee, result.assignee_id)

        if old_status != result.status:
            await self._record_change(task_id, "status", old_status, result.status)

        await self.store.commit()
        logger.info("Task assigned: task_id=%s, user_id=%s", task_id, user_id)
        return result

    async def archive_task(self, task_id: UUID) -> Task:
        task = await self.get_task_by_id(task_id)

        if task.status == Status.ARCHIVED:
            raise ConflictError("Task is already archived")

        old_status = task.status
        result = await self.store.archive(task_id)

        await self._record_change(task_id, "status", old_status, result.status)
        await self.store.commit()
        logger.debug("Task %s archived, sending notification", task_id)
        notification_start = time.monotonic()
        await self.notification_service.notify_task_archived(result)
        logger.debug("Notification for task %s archived in %.3fs", task_id, time.monotonic() - notification_start)
        logger.info("Task archived: task_id=%s", task_id)
        return result

    async def complete_task(self, task_id: UUID) -> Task:
        task = await self.get_task_by_id(task_id)

        if task.status == Status.DONE:
            raise ConflictError("Task is already done")
        if task.status == Status.ARCHIVED:
            raise ConflictError("Cannot complete archived task")

        old_status = task.status
        result = await self.store.complete(task_id)
        await self._record_change(task_id, "status", old_status, result.status)

        await self.store.commit()
        logger.debug("Task %s closed, sending notification", task_id)
        notification_start = time.monotonic()
        await self.notification_service.notify_task_closed(result)
        logger.debug("Notification for task %s completed in %.3fs", task_id, time.monotonic() - notification_start)
        logger.info("Task completed: id=%s", task_id)
        return result

    async def get_summary(self) -> dict:
        return await self.store.get_summary()

    async def _record_change(self, task_id: UUID, field: str, old_value, new_value):
        await self.history_store.add_entry(
            task_id=task_id,
            field=field,
            old_value=str(old_value) if old_value is not None else None,
            new_value=str(new_value) if new_value is not None else None,
        )
