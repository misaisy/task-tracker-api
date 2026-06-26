"""
Сервисный слой для пользователей.
Слой: бизнес-логика (services).
Зависит от: storage.
"""
import asyncio
import logging
from uuid import UUID

import bcrypt
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound

from app.errors.exceptions import ConflictError, UserNotFoundError
from app.models.orm import User
from app.storage.user_store import UserStore

logger = logging.getLogger(__name__)


class UserService:
    def __init__(self, store: UserStore):
        self.store = store

    @staticmethod
    async def hash_password(password: str) -> str:
        result = await asyncio.to_thread(
            bcrypt.hashpw, password.encode(), bcrypt.gensalt()
        )
        return result.decode()

    @staticmethod
    async def verify_password(plain_password: str, hashed: str) -> bool:
        return await asyncio.to_thread(
            bcrypt.checkpw, plain_password.encode(), hashed.encode()
        )

    async def get_all_users(self) -> list[User]:
        return await self.store.get_all()

    async def get_user_by_id(self, user_id: int) -> User:
        try:
            return await self.store.get_by_id(user_id)
        except NoResultFound as e:
            raise UserNotFoundError(user_id) from e

    async def get_by_username(self, username: str) -> User | None:
        return await self.store.get_by_username(username)

    async def create_user(self, user_data: dict) -> User:
        if "password" in user_data:
            user_data["password_hash"] = await self.hash_password(user_data.pop("password"))

        try:
            user = await self.store.add(user_data)
            await self.store.commit()
        except IntegrityError:
            await self.store.session.rollback()
            raise ConflictError("User with this email already exists") from None
        logger.info("User created: id=%s, username=%s", user.id, user.username)
        return user

    async def update_user_role(self, user_id: UUID, role: str) -> User:
        user = await self.get_user_by_id(user_id)
        user.role = role
        await self.store.commit()
        return user

    async def deactivate_user(self, user_id: UUID) -> User:
        user = await self.get_user_by_id(user_id)
        user.is_active = False
        await self.store.commit()
        return user
