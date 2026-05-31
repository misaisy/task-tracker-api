"""
Хранилище комментариев.
Слой: доступ к данным (storage).
Зависит от: constants (только константы).
"""
from datetime import UTC, datetime


class CommentStore:
    _comments: dict[int, dict]
    _next_id: int

    def __init__(self) -> None:
        self._comments = {}
        self._next_id = 1

    def add(self, comment_data: dict) -> dict:
        comment = {
            "id": self._next_id,
            "task_id": comment_data["task_id"],
            "text": comment_data["text"],
            "created_at": datetime.now(UTC),
        }
        self._comments[self._next_id] = comment
        self._next_id += 1
        return comment

    def get_by_task_id(self, task_id: int) -> list[dict]:
        return [c for c in self._comments.values() if c["task_id"] == task_id]

    def get_all(self) -> list[dict]:
        return list(self._comments.values())


comment_store = CommentStore()
