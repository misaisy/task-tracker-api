"""
Хранилище комментариев.
Слой: доступ к данным (storage).
"""
from datetime import UTC, datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models_sql import Comment


class CommentStore:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, comment_data: dict) -> dict:
        comment = Comment(
            task_id=comment_data["task_id"],
            author_id=comment_data["author_id"],
            text=comment_data["text"],
            created_at=datetime.now(UTC),
        )
        self.session.add(comment)
        await self.session.flush()
        return self._to_dict(comment)

    async def get_by_id(self, comment_id: int) -> dict | None:
        comment = await self.session.get(Comment, comment_id)
        return self._to_dict(comment) if comment else None

    async def get_by_task_id(self, task_id: int) -> list[dict]:
        stmt = (
            select(Comment)
            .where(Comment.task_id == task_id)
            .order_by(Comment.created_at)
        )
        result = await self.session.execute(stmt)
        comments = result.scalars().all()
        return [self._to_dict(c) for c in comments]

    async def get_all(self) -> list[dict]:
        stmt = (
            select(Comment)
            .order_by(Comment.id)
        )
        result = await self.session.execute(stmt)
        comments = result.scalars().all()
        return [self._to_dict(c) for c in comments]

    async def commit(self):
        await self.session.commit()

    async def clear(self):
        await self.session.execute(delete(Comment))

    def _to_dict(self, comment: Comment) -> dict:
        return {
            "id": comment.id,
            "task_id": comment.task_id,
            "text": comment.text,
            "author_id": comment.author_id,
            "created_at": comment.created_at,
        }
