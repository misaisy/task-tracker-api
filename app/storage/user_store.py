"""
Хранилище пользователей.
Слой: доступ к данным (storage).
Зависит от: constants (только константы).
"""
from datetime import datetime, timezone


class UserStore:
    def __init__(self):
        self._users: list[dict] = []
        self._next_id: int = 1

    def add(self, user_data: dict) -> dict:
        user = {
            "id": self._next_id,
            "username": user_data["username"],
            "email": user_data["email"],
            "created_at": datetime.now(timezone.utc),
        }
        self._users.append(user)
        self._next_id += 1
        return user

    def get_all(self) -> list[dict]:
        return self._users

    def get_by_id(self, user_id: int) -> dict | None:
        for user in self._users:
            if user["id"] == user_id:
                return user
        return None


user_store = UserStore()