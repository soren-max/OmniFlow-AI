"""Content project service — orchestrates project creation and preview generation.

Coordinates between API routes, repository, and platform adapters.
"""

from __future__ import annotations

from typing import Any

from api.app.adapters.registry import get_adapter
from api.app.adapters.types import (
    Platform,
    PlatformContent,
)
from api.app.evaluators import evaluate_project_previews
from api.app.repositories.project_repository import (
    ProjectRecord,
    ProjectRepository,
)

REVIEW_PENDING = "pending"
REVIEW_APPROVED = "approved"
REVIEW_REJECTED = "rejected"


class ProjectNotFoundError(LookupError):
    """Raised when a requested project does not exist."""

    def __init__(self, project_id: str) -> None:
        self.project_id = project_id
        super().__init__(f"Project not found: {project_id}")


class InvalidPlatformError(ValueError):
    """Raised when a requested platform identifier is unsupported."""

    def __init__(self, platform: str) -> None:
        self.platform = platform
        super().__init__(f"Unknown platform: {platform!r}")


class AdapterExecutionError(RuntimeError):
    """Raised when a platform adapter fails during preview or publish execution."""

    def __init__(self, platform: str, reason: str) -> None:
        self.platform = platform
        self.reason = reason
        super().__init__(f"Adapter failed for platform {platform!r}: {reason}")


class RealPublishNotSupportedError(ValueError):
    """Raised when real publishing is requested before it is supported."""

    def __init__(self) -> None:
        super().__init__("Real publishing is not supported in the current MVP.")


class UnsupportedPublishModeError(ValueError):
    """Raised when a publish mode other than mock is requested."""

    def __init__(self, mode: str) -> None:
        self.mode = mode
        super().__init__(f"Unsupported publish mode: {mode!r}")


class ProjectNotApprovedError(PermissionError):
    """Raised when a project has not passed human review before publish."""

    def __init__(self, project_id: str, status: str) -> None:
        self.project_id = project_id
        self.status = status
        super().__init__(
            f"Project {project_id} must be approved before mock publish. "
            f"Current status: {status}."
        )


class EvaluationRequiresPreviewError(ValueError):
    """Raised when evaluation is requested before any preview exists."""

    def __init__(self, project_id: str) -> None:
        self.project_id = project_id
        super().__init__(f"Project {project_id} needs at least one preview before evaluation.")


class EvaluationNotFoundError(LookupError):
    """Raised when no evaluation report exists for a project."""

    def __init__(self, project_id: str) -> None:
        self.project_id = project_id
        super().__init__(f"Evaluation report not found for project: {project_id}")


class ContentProjectService:
    """Business logic for content project CRUD and preview generation."""

    def __init__(self, repository: ProjectRepository | None = None) -> None:
        self._repository = repository or ProjectRepository()

    def supported_platforms(self) -> list[Platform]:
        """Return all supported platforms."""
        return list(Platform)

    def create_project(
        self,
        title: str,
        source_text: str,
        source_url: str | None = None,
    ) -> dict[str, Any]:
        """Create a new content project.

        Args:
            title: Project title.
            source_text: Source article body or content idea.
            source_url: Optional original URL.

        Returns:
            Project data dict as stored.
        """
        record = ProjectRecord(
            title=title,
            source_text=source_text,
            source_url=source_url,
        )
        self._repository.save(record)
        return record.to_dict()

    def get_project(self, project_id: str) -> dict[str, Any]:
        """Retrieve a project by its id.

        Args:
            project_id: The project's unique identifier.

        Returns:
            Project data dict.

        Raises:
            ProjectNotFoundError: If the project does not exist.
        """
        record = self._repository.find_by_id(project_id)
        if record is None:
            raise ProjectNotFoundError(project_id)
        return record.to_dict()

    def generate_previews(
        self,
        project_id: str,
        platforms: list[str],
        title_override: str | None = None,
        hooks: list[str] | None = None,
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        """Generate previews for the given platforms.

        For each platform:
        1. Parse platform identifier → Platform enum.
        2. Get adapter from registry.
        3. Build PlatformContent from project source + overrides.
        4. Transform content → validate → build preview.

        Args:
            project_id: The project to generate previews for.
            platforms: List of platform identifiers (e.g. ['wechat', 'zhihu']).
            title_override: Optional title to use instead of project title.
            hooks: Optional opening hooks.
            tags: Optional tags.

        Returns:
            Dict with project_id, project_title, previews list.

        Raises:
            ProjectNotFoundError: If the project does not exist.
            AdapterNotFoundError: If a platform has no registered adapter.
        """
        project = self.get_project(project_id)

        preview_results: list[dict[str, Any]] = []

        for platform_str in platforms:
            # Resolve platform enum
            try:
                platform_enum = Platform(platform_str)
            except ValueError:
                raise InvalidPlatformError(platform_str)

            # Get adapter
            adapter = get_adapter(platform_enum)

            # Build content for this platform
            content = PlatformContent(
                platform=platform_enum,
                title=title_override or project["title"],
                body=project["source_text"],
                hooks=hooks or [],
                tags=tags or [],
            )

            # Run the mock adaptation pipeline
            try:
                transformed = adapter.transform_content(content)
                validation = adapter.validate_content(transformed)
                preview = adapter.build_preview(transformed)
            except Exception as exc:
                raise AdapterExecutionError(platform_enum.value, str(exc))

            validation_payload: dict[str, Any] = {
                "is_valid": validation.is_valid,
                "errors": validation.errors,
                "warnings": validation.warnings,
            }
            preview_payload: dict[str, Any] = {
                "rendered_html": preview.rendered_html,
                "word_count": preview.word_count,
                "estimated_read_time_min": preview.estimated_read_time_min,
                "screenshot_url": preview.screenshot_url,
                "metadata": preview.metadata,
            }
            metadata: dict[str, Any] = {
                **transformed.metadata,
                "hooks": transformed.hooks,
                "tags": transformed.tags,
                "summary": transformed.summary,
            }

            preview_item: dict[str, Any] = {
                "project_id": project_id,
                "platform": platform_enum.value,
                "platform_display_name": platform_enum.display_name,
                "title": transformed.title,
                "content": transformed.body,
                "metadata": metadata,
                "preview": preview_payload,
                "validation": validation_payload,
                "rendered_html": preview.rendered_html,
                "word_count": preview.word_count,
                "estimated_read_time_min": preview.estimated_read_time_min,
                "warnings": validation.warnings,
            }

            preview_results.append(preview_item)

            # Persist preview to the project record
            self._repository.add_preview(project_id, preview_item)

        updated_project = self._repository.update_status(project_id, REVIEW_PENDING)
        if updated_project is None:
            raise ProjectNotFoundError(project_id)

        from datetime import datetime, timezone

        return {
            "project_id": project_id,
            "project_title": project["title"],
            "previews": preview_results,
            "generated_at": datetime.now(timezone.utc),
        }

    def approve_project(self, project_id: str) -> dict[str, Any]:
        """Mark a project as approved for mock publish."""
        return self._set_review_status(project_id, REVIEW_APPROVED)

    def reject_project(self, project_id: str) -> dict[str, Any]:
        """Mark a project as rejected and block mock publish."""
        return self._set_review_status(project_id, REVIEW_REJECTED)

    def publish_project(
        self,
        project_id: str,
        target_platforms: list[str],
        mode: str = "mock",
    ) -> dict[str, Any]:
        """Mock-publish a project to the requested platforms.

        Current MVP supports only mock publishing. Real publishing is intentionally
        blocked until human review, authorization, and platform credentials are
        designed.
        """
        if mode == "real":
            raise RealPublishNotSupportedError()
        if mode != "mock":
            raise UnsupportedPublishModeError(mode)

        project = self.get_project(project_id)
        if project["status"] != REVIEW_APPROVED:
            raise ProjectNotApprovedError(project_id, str(project["status"]))

        publish_results: list[dict[str, Any]] = []

        for platform_str in target_platforms:
            try:
                platform_enum = Platform(platform_str)
            except ValueError:
                raise InvalidPlatformError(platform_str)

            adapter = get_adapter(platform_enum)
            content = self._content_for_publish(project, platform_enum)

            try:
                result = adapter.mock_publish(content)
            except Exception as exc:
                raise AdapterExecutionError(platform_enum.value, str(exc))

            publish_results.append(
                {
                    "platform": platform_enum.value,
                    "platform_display_name": platform_enum.display_name,
                    "status": "success" if result.success else "failed",
                    "mock_url": result.published_url,
                    "message": (
                        str(result.metadata.get("message"))
                        if result.metadata.get("message")
                        else (
                            f"Mock published to {platform_enum.display_name} successfully."
                            if result.success
                            else (result.error_message or "Mock publish failed.")
                        )
                    ),
                    "metadata": result.metadata,
                }
            )

        self._repository.add_publish_results(
            project_id=project_id,
            mode=mode,
            results=publish_results,
        )

        from datetime import datetime, timezone

        return {
            "project_id": project_id,
            "mode": mode,
            "results": publish_results,
            "published_at": datetime.now(timezone.utc),
        }

    def evaluate_project(self, project_id: str) -> dict[str, Any]:
        """Run rule-based quality evaluation for persisted previews."""
        project = self.get_project(project_id)
        if not project.get("previews"):
            raise EvaluationRequiresPreviewError(project_id)

        report = evaluate_project_previews(project)
        saved_report = self._repository.add_evaluation_report(project_id, report)
        if saved_report is None:
            raise ProjectNotFoundError(project_id)
        return saved_report

    def get_evaluation(self, project_id: str) -> dict[str, Any]:
        """Return the latest evaluation report for a project."""
        self.get_project(project_id)
        report = self._repository.get_latest_evaluation_report(project_id)
        if report is None:
            raise EvaluationNotFoundError(project_id)
        return report

    def _set_review_status(self, project_id: str, status: str) -> dict[str, Any]:
        updated_project = self._repository.update_status(project_id, status)
        if updated_project is None:
            raise ProjectNotFoundError(project_id)
        return updated_project.to_dict()

    def _content_for_publish(
        self,
        project: dict[str, Any],
        platform: Platform,
    ) -> PlatformContent:
        """Build platform content for mock publishing from the latest preview if available."""
        previews = project.get("previews", [])
        if isinstance(previews, list):
            for preview in reversed(previews):
                if isinstance(preview, dict) and preview.get("platform") == platform.value:
                    return PlatformContent(
                        platform=platform,
                        title=str(preview.get("title") or project["title"]),
                        body=str(preview.get("content") or project["source_text"]),
                        summary=str(preview.get("metadata", {}).get("summary", "")),
                        hooks=list(preview.get("metadata", {}).get("hooks", [])),
                        tags=list(preview.get("metadata", {}).get("tags", [])),
                        metadata=dict(preview.get("metadata", {})),
                    )

        adapter = get_adapter(platform)
        content = PlatformContent(
            platform=platform,
            title=str(project["title"]),
            body=str(project["source_text"]),
        )
        return adapter.transform_content(content)
