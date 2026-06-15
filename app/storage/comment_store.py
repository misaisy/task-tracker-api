"""
Хранилище комментариев.
Слой: доступ к данным (storage).
"""
from datetime import UTC, datetime
from sqlalchemy import text
from sqlalchemy.orm import Session


class CommentStore:
    def __init__(self, session: Session):
        self.session = session

    def add(self, comment_data: dict) -> dict:
        result = self.session.execute(
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
        return self.get_by_id(comment_id)

    def get_by_id(self, comment_id: int) -> dict | None:
        row = self.session.execute(
            text("SELECT * FROM comments WHERE id = :id"), {"id": comment_id}
        ).fetchone()
        return dict(row._mapping) if row else None

    def get_by_task_id(self, task_id: int) -> list[dict]:
        rows = self.session.execute(
            text("SELECT * FROM comments WHERE task_id = :task_id ORDER BY created_at"),
            {"task_id": task_id}
        ).fetchall()
        return [dict(row._mapping) for row in rows]

    def get_all(self) -> list[dict]:
        rows = self.session.execute(text("SELECT * FROM comments")).fetchall()
        return [dict(row._mapping) for row in rows]
    
    def commit(self):
        self.session.commit()

    def clear(self):
        self.session.execute(text("DELETE FROM comments"))