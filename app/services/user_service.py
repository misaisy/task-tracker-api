"""
Сервисный слой для пользователей.
Слой: бизнес-логика (services).
Зависит от: storage.
"""
import logging

from app.exceptions import UserNotFoundError
from app.storage.user_store import UserStore

logger = logging.getLogger(__name__)


class UserService:
    def __init__(self, store: UserStore):
        self.store = store

    def get_all_users(self) -> list[dict]:
        return self.store.get_all()

    def get_user_by_id(self, user_id: int) -> dict:
        user = self.store.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(user_id)
        return user

    def create_user(self, user_data: dict) -> dict:
        user = self.store.add(user_data)
        logger.info("User created: id=%d, username=%s", user["id"], user["username"])
        return user
