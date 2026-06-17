"""In-memory repository for content projects.

Current stage: In-memory storage only.
Will be replaced with SQLAlchemy + PostgreSQL in a future stage.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


class ProjectRecord:
    """Internal record representing a stored content project."""

    def __init__(
        self,
        title: str,
        source_text: str,
        source_url: str | None = None,
    ) -> None:
        self.id: str = uuid4().hex[:12]
        self.title: str = title
        self.source_text: str = source_text
        self.source_url: str | None = source_url
        self.status: str = "created"
        self.created_at: datetime = datetime.now(timezone.utc)
        self.previews: list[dict[str, Any]] = []

    def to_dict(self) -> dict[str, Any]:
        """Convert record to a dictionary for API responses."""
        return {
            "id": self.id,
            "title": self.title,
            "source_text": self.source_text,
            "source_url": self.source_url,
            "status": self.status,
            "created_at": self.created_at,
            "previews": self.previews,
        }


class ProjectRepository:
    """In-memory store for content projects.

    Thread-safe for single-process development.
    Will be replaced with a database-backed repository.
    """

    def __init__(self) -> None:
        self._store: dict[str, ProjectRecord] = {}

    def save(self, record: ProjectRecord) -> ProjectRecord:
        """Persist a project record (create or update)."""
        self._store[record.id] = record
        return record

    def find_by_id(self, project_id: str) -> ProjectRecord | None:
        """Look up a project by its id."""
        return self._store.get(project_id)

    def add_preview(
        self,
        project_id: str,
        preview: dict[str, Any],
    ) -> ProjectRecord | None:
        """Append a preview result to a project's preview list."""
        record = self._store.get(project_id)
        if record is None:
            return None
        record.previews.append(preview)
        return record

    def delete(self, project_id: str) -> bool:
        """Remove a project from the store. Returns True if deleted."""
        if project_id in self._store:
            del self._store[project_id]
            return True
        return False

    def count(self) -> int:
        """Return the number of stored projects."""
        return len(self._store)

    def clear(self) -> None:
        """Remove all projects (useful for testing)."""
        self._store.clear()
