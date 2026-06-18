"""
Сервисный слой для пользователей.
Слой: бизнес-логика (services).
Зависит от: storage.
"""
import logging

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound

from app.errors.exceptions import ConflictError, UserNotFoundError
from app.storage.user_store import UserStore

logger = logging.getLogger(__name__)


class UserService:
    def __init__(self, store: UserStore):
        self.store = store

    async def get_all_users(self) -> list[dict]:
        return await self.store.get_all()

    async def get_user_by_id(self, user_id: int) -> dict:
        try:
            return await self.store.get_by_id(user_id)
        except NoResultFound as e:
            raise UserNotFoundError(user_id) from e

    async def create_user(self, user_data: dict) -> dict:
        try:
            user = await self.store.add(user_data)
            await self.store.commit()
        except IntegrityError:
            await self.store.session.rollback()
            raise ConflictError("User with this email already exists") from None
        logger.info("User created: id=%d, username=%s", user["id"], user["username"])
        return user
