"""
Хранилище комментариев.
Слой: доступ к данным (storage).
"""
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.orm import Comment


class CommentStore:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, comment_data: dict) -> Comment:
        comment = Comment(
            task_id=comment_data["task_id"],
            author_id=comment_data["author_id"],
            text=comment_data["text"],
            created_at=datetime.now(UTC),
        )
        self.session.add(comment)
        await self.session.flush()
        await self.session.commit()
        return comment

    async def get_by_id(self, comment_id: UUID) -> Comment:
        return await self.session.get_one(Comment, comment_id)

    async def get_by_task_id(self, task_id: UUID) -> list[Comment]:
        stmt = (
            select(Comment)
            .where(Comment.task_id == task_id)
            .order_by(Comment.created_at)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_all(self) -> list[Comment]:
        stmt = (
            select(Comment)
            .order_by(Comment.id)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def clear(self):
        await self.session.execute(delete(Comment))
