"""
Хранилище комментариев.
Слой: доступ к данным (storage).
Зависит от: constants (только константы).
"""
from datetime import datetime, timezone


class CommentStore:
    def __init__(self):
        self._comments: list[dict] = []
        self._next_id: int = 1

    def add(self, comment_data: dict) -> dict:
        comment = {
            "id": self._next_id,
            "task_id": comment_data["task_id"],
            "text": comment_data["text"],
            "created_at": datetime.now(timezone.utc),
        }
        self._comments.append(comment)
        self._next_id += 1
        return comment

    def get_by_task_id(self, task_id: int) -> list[dict]:
        return [c for c in self._comments if c["task_id"] == task_id]

    def get_all(self) -> list[dict]:
        return self._comments


comment_store = CommentStore()