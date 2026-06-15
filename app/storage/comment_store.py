"""
Хранилище комментариев.
Слой: доступ к данным (storage).
"""
from datetime import UTC, datetime
from sqlalchemy import text
from app.db import get_connection

class CommentStore:
    def add(self, comment_data: dict) -> dict:
        conn = get_connection()
        try:
            result = conn.execute(
                text("""
                    INSERT INTO comments (task_id, author_id, text, created_at)
                    VALUES (:task_id, :author_id, :text, :created_at)
                    RETURNING id
                """),
                {
                    "task_id": comment_data["task_id"],
                    "author_id": comment_data["author_id"],
                    "text": comment_data["text"],
                    "created_at": datetime.now(UTC),
                }
            )
            comment_id = result.scalar()
            conn.commit()
            return self.get_by_id(comment_id)
        finally:
            conn.close()


    def get_by_task_id(self, task_id: int) -> list[dict]:
        conn = get_connection()
        try:
            rows = conn.execute(
                text("SELECT * FROM comments WHERE task_id = :task_id ORDER BY created_at"),
                {"task_id": task_id}
            ).fetchall()
            return [dict(r._mapping) for r in rows]
        finally:
            conn.close()


    def get_all(self) -> list[dict]:
        conn = get_connection()
        try:
            rows = conn.execute(text("SELECT * FROM comments")).fetchall()
            return [dict(r._mapping) for r in rows]
        finally:
            conn.close()


    def clear(self):
        conn = get_connection()
        try:
            conn.execute(text("DELETE FROM comments"))
            conn.commit()
        finally:
            conn.close()

comment_store = CommentStore()
