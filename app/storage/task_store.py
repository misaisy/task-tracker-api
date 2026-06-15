"""
Хранилище задач.
Слой: доступ к данным (storage).
"""
from datetime import UTC, datetime
from typing import Optional
from sqlalchemy import text
from app.db import get_connection
from app.constants import DEFAULT_STATUS, DEFAULT_PRIORITY

class TaskStore:
    def add(self, task_data: dict) -> dict:
        conn = get_connection()
        try:
            result = conn.execute(
                text("""
                    INSERT INTO tasks (title, description, priority, status, owner_id, created_at, updated_at)
                    VALUES (:title, :description, :priority, :status, :owner_id, :created_at, :updated_at)
                    RETURNING id
                """),
                {
                    "title": task_data["title"],
                    "description": task_data.get("description"),
                    "priority": task_data.get("priority", DEFAULT_PRIORITY),
                    "status": DEFAULT_STATUS,
                    "owner_id": task_data.get("owner_id"),
                    "created_at": datetime.now(UTC),
                    "updated_at": datetime.now(UTC),
                }
            )
            task_id = result.scalar()
            conn.commit()
            return self.get_by_id(task_id)
        finally:
            conn.close()


    def get_all(self) -> list[dict]:
        conn = get_connection()
        try:
            rows = conn.execute(text("SELECT * FROM tasks")).fetchall()
            return [dict(r._mapping) for r in rows]
        finally:
            conn.close()


    def get_by_id(self, task_id: int) -> Optional[dict]:
        conn = get_connection()
        try:
            row = conn.execute(text("SELECT * FROM tasks WHERE id = :id"), {"id": task_id}).fetchone()
            return dict(row._mapping) if row else None
        finally:
            conn.close()


    def update(self, task_id: int, data: dict) -> Optional[dict]:
        conn = get_connection()
        try:
            pass
        finally:
            conn.close()


    def assign(self, task_id: int, user_id: int) -> Optional[dict]:
        conn = get_connection()
        try:
            conn.execute(
                text("""
                    UPDATE tasks
                    SET assignee_id = :user_id,
                        status = CASE WHEN status = :todo THEN :in_progress ELSE status END,
                        updated_at = :now
                    WHERE id = :id
                """),
                {
                    "user_id": user_id,
                    "todo": "TODO",
                    "in_progress": "IN_PROGRESS",
                    "now": datetime.now(UTC),
                    "id": task_id,
                }
            )
            conn.commit()
            return self.get_by_id(task_id)
        finally:
            conn.close()


    def archive(self, task_id: int) -> Optional[dict]:
        conn = get_connection()
        try:
            conn.execute(
                text("""
                    UPDATE tasks
                    SET status = 'ARCHIVED',
                        updated_at = :now
                    WHERE id = :id AND status != 'ARCHIVED'
                """),
                {"now": datetime.now(UTC), "id": task_id}
            )
            conn.commit()
            return self.get_by_id(task_id)
        finally:
            conn.close()


    def clear(self):
        conn = get_connection()
        try:
            conn.execute(text("DELETE FROM tasks"))
            conn.commit()
        finally:
            conn.close()


    def complete(self, task_id: int) -> dict | None:
        conn = get_connection()
        try:
            result = conn.execute(
                text("""
                    UPDATE tasks
                    SET status = 'DONE',
                        closed_at = :closed_at,
                        updated_at = :now
                    WHERE id = :id
                    RETURNING *
                """),
                {
                    "closed_at": datetime.now(UTC),
                    "now": datetime.now(UTC),
                    "id": task_id,
                }
            )
            conn.commit()
            row = result.fetchone()
            return dict(row._mapping) if row else None
        finally:
            conn.close()


    def _touch(self, task_id: int) -> None:
        conn = get_connection()
        try:
            conn.execute(
                text("""
                    UPDATE tasks
                    SET updated_at = :now
                    WHERE id = :id
                """),
                {"now": datetime.now(UTC), "id": task_id}
            )
            conn.commit()
        finally:
            conn.close()
    

    def get_filtered_tasks(
        self,
        status: str | None = None,
        priority: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> list[dict]:
        conn = get_connection()
        try:
            query = "SELECT * FROM tasks"
            params = {}

            conditions = []
            if status:
                conditions.append("status = :status")
                params["status"] = status
            if priority:
                conditions.append("priority = :priority")
                params["priority"] = priority

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            allowed_sort_fields = {"created_at", "priority", "status"}
            if sort_by not in allowed_sort_fields:
                sort_by = "created_at"
            order_direction = "DESC" if sort_order.lower() == "desc" else "ASC"
            if sort_by == "priority":
                query += f" ORDER BY CASE priority WHEN 'low' THEN 0 WHEN 'medium' THEN 1 WHEN 'high' THEN 2 END {order_direction}"
            elif sort_by == "status":
                query += f" ORDER BY CASE status WHEN 'TODO' THEN 0 WHEN 'IN_PROGRESS' THEN 1 WHEN 'REVIEW' THEN 2 WHEN 'DONE' THEN 3 WHEN 'ARCHIVED' THEN 4 END {order_direction}"
            else:
                query += f" ORDER BY created_at {order_direction}"

            rows = conn.execute(text(query), params).fetchall()
            return [dict(row._mapping) for row in rows]
        finally:
            conn.close()
    

    def get_summary(self) -> dict:
        conn = get_connection()
        try:
            status_rows = conn.execute(
                text("""
                    SELECT status, COUNT(*) as count
                    FROM tasks
                    GROUP BY status
                """)
            ).fetchall()
            by_status = {row.status: row.count for row in status_rows}

            priority_rows = conn.execute(
                text("""
                    SELECT priority, COUNT(*) as count
                    FROM tasks
                    GROUP BY priority
                """)
            ).fetchall()
            by_priority = {row.priority: row.count for row in priority_rows}

            total_row = conn.execute(text("SELECT COUNT(*) FROM tasks")).fetchone()
            total = total_row[0]

            return {
                "total": total,
                "by_status": by_status,
                "by_priority": by_priority,
            }
        finally:
            conn.close()

task_store = TaskStore()
