"""Database access layer.

Current stage: In-memory storage only.
Will be replaced with SQLAlchemy + PostgreSQL in a future stage.
"""

from .project_repository import ProjectRecord, ProjectRepository

__all__ = [
    "ProjectRecord",
    "ProjectRepository",
]
