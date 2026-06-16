"""
Хранилище пользователей.
Слой: доступ к данным (storage).
"""
from datetime import UTC, datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models_sql import User


class UserStore:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, user_data: dict) -> dict:
        user = User(
            username=user_data["username"],
            email=user_data["email"],
            created_at=datetime.now(UTC),
        )
        self.session.add(user)
        await self.session.flush()
        return self._to_dict(user)

    async def get_all(self) -> list[dict]:
        stmt = select(User).order_by(User.id)
        result = await self.session.execute(stmt)
        users = result.scalars().all()
        return [self._to_dict(u) for u in users]

    async def get_by_id(self, user_id: int) -> dict | None:
        user = await self.session.get(User, user_id)
        return self._to_dict(user) if user else None

    async def commit(self):
        await self.session.commit()

    async def clear(self):
        await self.session.execute(delete(User))

    def _to_dict(self, user: User) -> dict:
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "created_at": user.created_at,
        }
