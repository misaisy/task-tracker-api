"""
Хранилище пользователей.
Слой: доступ к данным (storage).
Зависит от: constants (только константы).
"""
from datetime import UTC, datetime


class UserStore:
    _users: dict[int, dict]
    _next_id: int

    def __init__(self) -> None:
        self._users = {}
        self._next_id = 1

    def add(self, user_data: dict) -> dict:
        user = {
            "id": self._next_id,
            "username": user_data["username"],
            "email": user_data["email"],
            "created_at": datetime.now(UTC),
        }
        self._users[self._next_id] = user
        self._next_id += 1
        return user

    def get_all(self) -> list[dict]:
        return list(self._users.values())

    def get_by_id(self, user_id: int) -> dict | None:
        return self._users.get(user_id)


user_store = UserStore()
