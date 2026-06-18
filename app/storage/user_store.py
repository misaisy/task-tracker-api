"""
Хранилище пользователей.
Слой: доступ к данным (storage).
"""
from datetime import UTC, datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.orm import User


class UserStore:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, user_data: dict) -> User:
        user = User(
            username=user_data["username"],
            email=user_data["email"],
            created_at=datetime.now(UTC),
        )
        self.session.add(user)
        await self.session.flush()
        return user

    async def get_all(self) -> list[User]:
        stmt = select(User).order_by(User.id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, user_id: int) -> User:
        return await self.session.get_one(User, user_id)

    async def commit(self):
        await self.session.commit()

    async def clear(self):
        await self.session.execute(delete(User))
