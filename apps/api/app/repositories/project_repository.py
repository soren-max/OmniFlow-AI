"""Database-backed repository for content projects."""

from __future__ import annotations

from collections.abc import Callable
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from api.app.core.database import SessionLocal
from api.app.models.project import (
    ContentProjectModel,
    EvaluationReportModel,
    PlatformContentModel,
    PublishDraftModel,
    PublishResultModel,
    PublishTaskModel,
)
from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

SessionFactory = Callable[[], Session]


class ProjectRecord:
    """Internal record representing a stored content project."""

    def __init__(
        self,
        title: str,
        source_text: str,
        source_url: str | None = None,
        *,
        project_id: str | None = None,
        status: str = "created",
        created_at: datetime | None = None,
        previews: list[dict[str, Any]] | None = None,
    ) -> None:
        self.id: str = project_id or uuid4().hex[:12]
        self.title: str = title
        self.source_text: str = source_text
        self.source_url: str | None = source_url
        self.status: str = status
        self.created_at: datetime = created_at or datetime.now(timezone.utc)
        self.previews: list[dict[str, Any]] = previews or []

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
    """Persist content projects, previews, and mock publish results."""

    def __init__(self, session_factory: SessionFactory = SessionLocal) -> None:
        self._session_factory = session_factory

    def save(self, record: ProjectRecord) -> ProjectRecord:
        """Persist a project record."""
        with self._session_scope() as session:
            existing = session.get(ContentProjectModel, record.id)
            if existing is None:
                model = ContentProjectModel(
                    id=record.id,
                    title=record.title,
                    source_text=record.source_text,
                    source_url=record.source_url,
                    status=record.status,
                    created_at=record.created_at,
                )
                session.add(model)
            else:
                existing.title = record.title
                existing.source_text = record.source_text
                existing.source_url = record.source_url
                existing.status = record.status
        return record

    def find_by_id(self, project_id: str) -> ProjectRecord | None:
        """Look up a project by its id."""
        with self._session_scope(commit=False) as session:
            statement = (
                select(ContentProjectModel)
                .options(selectinload(ContentProjectModel.previews))
                .where(ContentProjectModel.id == project_id)
            )
            model = session.scalar(statement)
            if model is None:
                return None
            return self._to_record(model)

    def add_preview(
        self,
        project_id: str,
        preview: dict[str, Any],
    ) -> ProjectRecord | None:
        """Persist a platform preview for a project."""
        with self._session_scope() as session:
            project = session.get(ContentProjectModel, project_id)
            if project is None:
                return None

            session.add(
                PlatformContentModel(
                    project_id=project_id,
                    platform=str(preview["platform"]),
                    platform_display_name=str(preview["platform_display_name"]),
                    title=str(preview["title"]),
                    content=str(preview["content"]),
                    metadata_json=dict(preview.get("metadata", {})),
                    preview_json=dict(preview.get("preview", {})),
                    validation_json=dict(preview.get("validation", {})),
                    rendered_html=str(preview["rendered_html"]),
                    word_count=int(preview.get("word_count", 0)),
                    estimated_read_time_min=int(preview.get("estimated_read_time_min", 1)),
                    warnings_json=list(preview.get("warnings", [])),
                )
            )
        return self.find_by_id(project_id)

    def add_publish_results(
        self,
        project_id: str,
        mode: str,
        results: list[dict[str, Any]],
    ) -> None:
        """Persist mock publish task results."""
        with self._session_scope() as session:
            project = session.get(ContentProjectModel, project_id)
            if project is None:
                return

            task = PublishTaskModel(project_id=project_id, mode=mode, status="completed")
            task.results = [
                PublishResultModel(
                    platform=str(result["platform"]),
                    platform_display_name=str(result["platform_display_name"]),
                    status=str(result["status"]),
                    mock_url=(
                        str(result["mock_url"]) if result.get("mock_url") is not None else None
                    ),
                    message=str(result["message"]),
                    metadata_json=dict(result.get("metadata", {})),
                )
                for result in results
            ]
            session.add(task)

    def add_evaluation_report(
        self,
        project_id: str,
        report: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Persist a rule-based evaluation report."""
        with self._session_scope() as session:
            project = session.get(ContentProjectModel, project_id)
            if project is None:
                return None

            model = EvaluationReportModel(
                project_id=project_id,
                average_score=int(report["average_score"]),
                platform_scores_json=list(report.get("platform_scores", [])),
                issues_json=list(report.get("issues", [])),
                suggestions_json=list(report.get("suggestions", [])),
                created_at=datetime.now(timezone.utc),
            )
            session.add(model)
            session.flush()
            created_at = model.created_at

        return {
            "project_id": project_id,
            "average_score": int(report["average_score"]),
            "platform_scores": list(report.get("platform_scores", [])),
            "issues": list(report.get("issues", [])),
            "suggestions": list(report.get("suggestions", [])),
            "created_at": created_at,
        }

    def get_latest_evaluation_report(self, project_id: str) -> dict[str, Any] | None:
        """Return the latest rule-based evaluation report for a project."""
        with self._session_scope(commit=False) as session:
            statement = (
                select(EvaluationReportModel)
                .where(EvaluationReportModel.project_id == project_id)
                .order_by(EvaluationReportModel.created_at.desc(), EvaluationReportModel.id.desc())
                .limit(1)
            )
            model = session.scalar(statement)
            if model is None:
                return None
            return {
                "project_id": model.project_id,
                "average_score": model.average_score,
                "platform_scores": model.platform_scores_json,
                "issues": model.issues_json,
                "suggestions": model.suggestions_json,
                "created_at": model.created_at,
            }

    def add_publish_draft(
        self,
        project_id: str,
        draft: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Persist a system-internal publishing draft for a project."""
        with self._session_scope() as session:
            project = session.get(ContentProjectModel, project_id)
            if project is None:
                return None

            model = PublishDraftModel(
                draft_id=uuid4().hex[:12],
                project_id=project_id,
                platform=str(draft["platform"]),
                title=str(draft["title"]),
                body=str(draft["body"]),
                hashtags_json=list(draft.get("hashtags", [])),
                summary=str(draft.get("summary", "")),
                cta=str(draft.get("cta", "")),
                notes=str(draft.get("notes", "")),
                status=str(draft.get("status", "draft")),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            session.add(model)
            session.flush()
            return self._draft_to_dict(model)

    def list_publish_drafts(self, project_id: str) -> list[dict[str, Any]] | None:
        """List system drafts for a project, newest first."""
        with self._session_scope(commit=False) as session:
            if session.get(ContentProjectModel, project_id) is None:
                return None

            statement = (
                select(PublishDraftModel)
                .where(PublishDraftModel.project_id == project_id)
                .order_by(PublishDraftModel.updated_at.desc(), PublishDraftModel.created_at.desc())
            )
            return [self._draft_to_dict(model) for model in session.scalars(statement).all()]

    def get_publish_draft(self, draft_id: str) -> dict[str, Any] | None:
        """Return one system draft by id."""
        with self._session_scope(commit=False) as session:
            model = session.get(PublishDraftModel, draft_id)
            if model is None:
                return None
            return self._draft_to_dict(model)

    def update_publish_draft(
        self,
        draft_id: str,
        updates: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Update editable fields on a system draft."""
        with self._session_scope() as session:
            model = session.get(PublishDraftModel, draft_id)
            if model is None:
                return None

            for field in ("title", "body", "summary", "cta", "notes", "status"):
                if field in updates and updates[field] is not None:
                    setattr(model, field, str(updates[field]))
            if "hashtags" in updates and updates["hashtags"] is not None:
                model.hashtags_json = list(updates["hashtags"])
            model.updated_at = datetime.now(timezone.utc)
            session.flush()
            return self._draft_to_dict(model)

    def update_status(self, project_id: str, status: str) -> ProjectRecord | None:
        """Update a project's workflow status."""
        with self._session_scope() as session:
            project = session.get(ContentProjectModel, project_id)
            if project is None:
                return None
            project.status = status
        return self.find_by_id(project_id)

    def delete(self, project_id: str) -> bool:
        """Remove a project from the store. Returns True if deleted."""
        with self._session_scope() as session:
            deleted = session.execute(
                delete(ContentProjectModel).where(ContentProjectModel.id == project_id)
            ).rowcount
        return bool(deleted)

    def count(self) -> int:
        """Return the number of stored projects."""
        with self._session_scope(commit=False) as session:
            return len(session.scalars(select(ContentProjectModel.id)).all())

    def clear(self) -> None:
        """Remove all project data (useful for testing)."""
        with self._session_scope() as session:
            session.execute(delete(PublishDraftModel))
            session.execute(delete(EvaluationReportModel))
            session.execute(delete(PublishResultModel))
            session.execute(delete(PublishTaskModel))
            session.execute(delete(PlatformContentModel))
            session.execute(delete(ContentProjectModel))

    @contextmanager
    def _session_scope(self, *, commit: bool = True) -> Any:
        session = self._session_factory()
        try:
            yield session
            if commit:
                session.commit()
        except Exception:
            if commit:
                session.rollback()
            raise
        finally:
            session.close()

    @staticmethod
    def _to_record(model: ContentProjectModel) -> ProjectRecord:
        return ProjectRecord(
            project_id=model.id,
            title=model.title,
            source_text=model.source_text,
            source_url=model.source_url,
            status=model.status,
            created_at=model.created_at,
            previews=[
                {
                    "project_id": preview.project_id,
                    "platform": preview.platform,
                    "platform_display_name": preview.platform_display_name,
                    "title": preview.title,
                    "content": preview.content,
                    "metadata": preview.metadata_json,
                    "preview": preview.preview_json,
                    "validation": preview.validation_json,
                    "rendered_html": preview.rendered_html,
                    "word_count": preview.word_count,
                    "estimated_read_time_min": preview.estimated_read_time_min,
                    "warnings": preview.warnings_json,
                }
                for preview in model.previews
            ],
        )

    @staticmethod
    def _draft_to_dict(model: PublishDraftModel) -> dict[str, Any]:
        return {
            "draft_id": model.draft_id,
            "project_id": model.project_id,
            "platform": model.platform,
            "title": model.title,
            "body": model.body,
            "hashtags": model.hashtags_json,
            "summary": model.summary,
            "cta": model.cta,
            "notes": model.notes,
            "status": model.status,
            "created_at": model.created_at,
            "updated_at": model.updated_at,
        }
