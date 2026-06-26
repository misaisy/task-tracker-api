import asyncio
import csv
import io
import logging
import time
from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi.responses import JSONResponse, PlainTextResponse
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.storage.task_store import TaskStore

logger = logging.getLogger(__name__)


class ExportService:
    def __init__(self, session_factory: async_sessionmaker):
        self.session_factory = session_factory
        self._results: dict[UUID, dict] = {}
        self._running_tasks: dict[UUID, asyncio.Task] = {}

    async def start_export(self, format: str) -> UUID:
        export_id = uuid4()
        self._results[export_id] = {"status": "processing", "result": None, "format": format}
        self._running_tasks[export_id] = asyncio.create_task(self._run_export(export_id, format))
        return export_id

    async def _run_export(self, export_id: UUID, format: str):
        logger.debug("Export %s started (format=%s)", export_id, format)
        start = time.monotonic()
        try:
            async with self.session_factory() as session:
                task_store = TaskStore(session)
                tasks = await task_store.get_all()
                if format == "csv":
                    result = await asyncio.to_thread(self._generate_csv, tasks)
                else:
                    result = self._generate_json(tasks)
            elapsed = time.monotonic() - start
            self._results[export_id] = {"status": "completed", "result": result, "format": format}
            logger.info("Export %s completed (%.3fs)", export_id, elapsed)
        except Exception as exc:
            elapsed = time.monotonic() - start
            logger.error("Export %s failed after %.3fs: %s", export_id, elapsed, exc)
            self._results[export_id] = {"status": "failed", "error": str(exc)}

    async def get_export_response(self, export_id: UUID):
        export = self._results.get(export_id)
        if not export:
            return JSONResponse(status_code=404, content={"detail": "Export not found"})
        if export["status"] == "processing":
            return JSONResponse(status_code=200, content={"export_id": str(export_id), "status": "processing"})
        if export["status"] == "failed":
            return JSONResponse(status_code=500, content={"detail": export.get("error", "Export failed")})

        result = export["result"]
        if export["format"] == "csv":
            return PlainTextResponse(content=result, media_type="text/csv")
        return JSONResponse(content=result)

    def _generate_csv(self, tasks) -> str:
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=["id", "title", "status", "priority", "created_at"])
        writer.writeheader()
        for task in tasks:
            writer.writerow({
                "id": str(task.id),
                "title": task.title,
                "status": task.status,
                "priority": task.priority,
                "created_at": task.created_at,
            })
        return output.getvalue()

    def _generate_json(self, tasks) -> dict:
        return {
            "exported_at": datetime.now(UTC).isoformat(),
            "format": "json",
            "tasks": [
                {
                    "id": str(t.id),
                    "title": t.title,
                    "description": t.description,
                    "priority": t.priority,
                    "status": t.status,
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                    "updated_at": t.updated_at.isoformat() if t.updated_at else None,
                    "closed_at": t.closed_at.isoformat() if t.closed_at else None,
                    "owner_id": str(t.owner_id),
                    "assignee_id": str(t.assignee_id),
                }
                for t in tasks
            ],
        }
