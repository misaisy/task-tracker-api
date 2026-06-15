"""
Хранилище пользователей.
Слой: доступ к данным (storage).
"""
from datetime import UTC, datetime
from sqlalchemy import text
from sqlalchemy.orm import Session


class UserStore:
    def __init__(self, session: Session):
        self.session = session

    def add(self, user_data: dict) -> dict:
        result = self.session.execute(
            text("""
                INSERT INTO users (username, email, created_at)
                VALUES (:username, :email, :created_at)
                RETURNING id
            """),
            {
                "username": user_data["username"],
                "email": user_data["email"],
                "created_at": datetime.now(UTC),
            }
        )
        user_id = result.scalar()
        return self.get_by_id(user_id)

    def get_all(self) -> list[dict]:
        rows = self.session.execute(text("SELECT * FROM users")).fetchall()
        return [dict(row._mapping) for row in rows]

    def get_by_id(self, user_id: int) -> dict | None:
        row = self.session.execute(
            text("SELECT * FROM users WHERE id = :id"), {"id": user_id}
        ).fetchone()
        return dict(row._mapping) if row else None
    
    def commit(self):
        self.session.commit()

    def clear(self):
        self.session.execute(text("DELETE FROM users"))