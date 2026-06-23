"""Content project service — orchestrates project creation and preview generation.

Coordinates between API routes, repository, and platform adapters.
"""

from __future__ import annotations

import json
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
DRAFT_STATUS_DRAFT = "draft"
DRAFT_STATUS_EXPORTED = "exported"
DRAFT_STATUS_HANDOFF_OPENED = "handoff_opened"
DRAFT_STATUSES = {"draft", "reviewed", "exported", "handoff_opened", "archived"}
OFFICIAL_PUBLISH_URLS = {
    Platform.WECHAT.value: "https://mp.weixin.qq.com/",
    Platform.ZHIHU.value: "https://www.zhihu.com/creator",
    Platform.BILIBILI.value: "https://member.bilibili.com/platform/home",
    Platform.XIAOHONGSHU.value: "https://creator.xiaohongshu.com/",
    Platform.DOUYIN.value: "https://creator.douyin.com/",
}


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


class ExportRequiresPreviewError(ValueError):
    """Raised when a publish package is requested before previews exist."""

    def __init__(self, project_id: str) -> None:
        self.project_id = project_id
        super().__init__(f"Project {project_id} needs at least one preview before export.")


class DraftNotFoundError(LookupError):
    """Raised when a requested publish draft does not exist."""

    def __init__(self, draft_id: str) -> None:
        self.draft_id = draft_id
        super().__init__(f"Publish draft not found: {draft_id}")


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

    def build_publish_package(self, project_id: str) -> dict[str, Any]:
        """Build an export package for manual platform publishing."""
        project = self.get_project(project_id)
        previews = project.get("previews")
        if not isinstance(previews, list) or len(previews) == 0:
            raise ExportRequiresPreviewError(project_id)

        platform_contents = [
            self._publish_package_platform_content(preview)
            for preview in previews
            if isinstance(preview, dict)
        ]
        evaluation = self._repository.get_latest_evaluation_report(project_id)
        warnings: list[str] = []
        if project["status"] == REVIEW_PENDING:
            warnings.append("Project is pending review; export is marked as draft.")
        elif project["status"] == REVIEW_REJECTED:
            warnings.append("Project was rejected in Human Review; inspect before publishing.")

        from datetime import datetime, timezone

        return {
            "project_id": project_id,
            "title": project["title"],
            "created_at": project["created_at"],
            "platforms": [content["platform"] for content in platform_contents],
            "platform_contents": platform_contents,
            "review_status": project["status"],
            "package_status": "approved" if project["status"] == REVIEW_APPROVED else "draft",
            "warnings": warnings,
            "evaluation_summary": self._evaluation_summary(evaluation),
            "exported_at": datetime.now(timezone.utc),
        }

    def build_publish_package_markdown(self, project_id: str) -> str:
        """Render a publish package as Markdown for manual publishing."""
        package = self.build_publish_package(project_id)
        lines = [
            f"# 发布包: {package['title']}",
            "",
            f"- Project ID: `{package['project_id']}`",
            f"- Review status: `{package['review_status']}`",
            f"- Package status: `{package['package_status']}`",
            f"- Exported at: {package['exported_at'].isoformat()}",
            "",
        ]

        warnings = package.get("warnings", [])
        if warnings:
            lines.extend(["## Warnings", ""])
            lines.extend(f"- {warning}" for warning in warnings)
            lines.append("")

        lines.extend(["## Evaluation Summary", ""])
        evaluation = package["evaluation_summary"]
        if evaluation.get("message"):
            lines.extend([str(evaluation["message"]), ""])
        else:
            lines.extend([f"- Average score: {evaluation['average_score']}", ""])
            if evaluation.get("issues"):
                lines.append("### Issues")
                lines.extend(f"- {issue}" for issue in evaluation["issues"])
                lines.append("")
            if evaluation.get("suggestions"):
                lines.append("### Suggestions")
                lines.extend(f"- {suggestion}" for suggestion in evaluation["suggestions"])
                lines.append("")

        for content in package["platform_contents"]:
            lines.extend(
                [
                    f"## {content['platform']}",
                    "",
                    "### 标题",
                    content["title"],
                    "",
                    "### 正文",
                    content["body"],
                    "",
                    "### 标签",
                    ", ".join(content["hashtags"]) if content["hashtags"] else "无",
                    "",
                    "### 摘要",
                    content["summary"] or "无",
                    "",
                    "### CTA",
                    content["cta"] or "无",
                    "",
                    "### Notes",
                    content["notes"] or "无",
                    "",
                ]
            )

        return "\n".join(lines).rstrip() + "\n"

    def create_publish_draft(
        self,
        project_id: str,
        platform: str,
        title: str,
        body: str,
        hashtags: list[str] | None = None,
        summary: str = "",
        cta: str = "",
        notes: str = "",
    ) -> dict[str, Any]:
        """Save platform content as an OmniFlow-AI system draft."""
        self.get_project(project_id)
        platform_enum = self._platform_enum(platform)
        draft = self._repository.add_publish_draft(
            project_id,
            {
                "platform": platform_enum.value,
                "title": title.strip(),
                "body": body.strip(),
                "hashtags": self._string_list(hashtags or []),
                "summary": summary,
                "cta": cta,
                "notes": notes,
                "status": DRAFT_STATUS_DRAFT,
            },
        )
        if draft is None:
            raise ProjectNotFoundError(project_id)
        return draft

    def list_publish_drafts(self, project_id: str) -> list[dict[str, Any]]:
        """List OmniFlow-AI system drafts for a project."""
        drafts = self._repository.list_publish_drafts(project_id)
        if drafts is None:
            raise ProjectNotFoundError(project_id)
        return drafts

    def get_publish_draft(self, draft_id: str) -> dict[str, Any]:
        """Return one OmniFlow-AI system draft."""
        draft = self._repository.get_publish_draft(draft_id)
        if draft is None:
            raise DraftNotFoundError(draft_id)
        return draft

    def update_publish_draft(
        self,
        draft_id: str,
        updates: dict[str, Any],
    ) -> dict[str, Any]:
        """Edit an OmniFlow-AI system draft."""
        if "platform" in updates:
            self._platform_enum(str(updates["platform"]))
        if "status" in updates and updates["status"] is not None:
            status = str(updates["status"])
            if status not in DRAFT_STATUSES:
                raise ValueError(f"Unsupported draft status: {status!r}")

        draft = self._repository.update_publish_draft(draft_id, updates)
        if draft is None:
            raise DraftNotFoundError(draft_id)
        return draft

    def export_publish_draft(self, draft_id: str, export_format: str) -> dict[str, Any]:
        """Export a single system draft as Markdown or JSON content."""
        draft = self.get_publish_draft(draft_id)
        if export_format not in {"json", "markdown"}:
            raise ValueError(f"Unsupported draft export format: {export_format!r}")

        from datetime import datetime, timezone

        exported_at = datetime.now(timezone.utc)
        if export_format == "json":
            content = json.dumps(
                {
                    **draft,
                    "created_at": draft["created_at"].isoformat(),
                    "updated_at": draft["updated_at"].isoformat(),
                    "exported_at": exported_at.isoformat(),
                    "manual_publish_required": True,
                    "system_draft_only": True,
                },
                ensure_ascii=False,
                indent=2,
            )
        else:
            content = self._draft_markdown(draft, exported_at)

        updated = self._repository.update_publish_draft(
            draft_id,
            {"status": DRAFT_STATUS_EXPORTED},
        )
        if updated is None:
            raise DraftNotFoundError(draft_id)

        return {
            "draft_id": draft_id,
            "format": export_format,
            "filename": f"omniflow-draft-{draft_id}.{ 'json' if export_format == 'json' else 'md' }",
            "content": content,
            "exported_at": exported_at,
        }

    def open_publish_draft_handoff(self, draft_id: str) -> dict[str, Any]:
        """Mark a system draft as handed off to a manual official publish page."""
        draft = self.get_publish_draft(draft_id)
        official_url = OFFICIAL_PUBLISH_URLS.get(str(draft["platform"]))
        if official_url is None:
            raise InvalidPlatformError(str(draft["platform"]))

        updated = self._repository.update_publish_draft(
            draft_id,
            {"status": DRAFT_STATUS_HANDOFF_OPENED},
        )
        if updated is None:
            raise DraftNotFoundError(draft_id)
        return {
            "draft": updated,
            "official_publish_url": official_url,
            "message": (
                "这是 OmniFlow-AI 系统内草稿箱, 不是平台官方草稿箱。"
                "发布仍需要你进入平台官方发布页手动确认提交。"
            ),
        }

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

    @staticmethod
    def _platform_enum(platform: str) -> Platform:
        try:
            return Platform(platform)
        except ValueError:
            raise InvalidPlatformError(platform)

    @staticmethod
    def _publish_package_platform_content(preview: dict[str, Any]) -> dict[str, Any]:
        metadata = preview.get("metadata", {})
        metadata = metadata if isinstance(metadata, dict) else {}
        hashtags = ContentProjectService._string_list(
            metadata.get("hashtags") or metadata.get("tags")
        )
        summary = str(metadata.get("summary") or "")
        cta = str(metadata.get("call_to_action") or metadata.get("cta") or "")
        warnings = ContentProjectService._string_list(preview.get("warnings"))
        notes = "; ".join(warnings)
        body = str(preview.get("content") or "")
        title = str(preview.get("title") or "")
        copy_parts = [title, "", body]
        if hashtags:
            copy_parts.extend(["", " ".join(f"#{tag}" for tag in hashtags)])
        if cta:
            copy_parts.extend(["", cta])

        return {
            "platform": str(preview.get("platform") or ""),
            "title": title,
            "body": body,
            "hashtags": hashtags,
            "summary": summary,
            "cta": cta,
            "notes": notes,
            "copy_text": "\n".join(copy_parts).strip(),
        }

    @staticmethod
    def _evaluation_summary(evaluation: dict[str, Any] | None) -> dict[str, Any]:
        if evaluation is None:
            return {
                "average_score": None,
                "issues": [],
                "suggestions": [],
                "message": "Evaluation not generated yet.",
            }
        return {
            "average_score": int(evaluation["average_score"]),
            "issues": list(evaluation.get("issues", [])),
            "suggestions": list(evaluation.get("suggestions", [])),
            "message": None,
        }

    @staticmethod
    def _string_list(value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        return [str(item) for item in value if str(item).strip()]

    @staticmethod
    def _draft_markdown(draft: dict[str, Any], exported_at: Any) -> str:
        hashtags = draft.get("hashtags", [])
        tag_text = " ".join(f"#{tag}" for tag in hashtags) if hashtags else "无"
        lines = [
            f"# {draft['title']}",
            "",
            f"- Draft ID: `{draft['draft_id']}`",
            f"- Project ID: `{draft['project_id']}`",
            f"- Platform: `{draft['platform']}`",
            f"- Status: `{draft['status']}`",
            f"- Exported at: {exported_at.isoformat()}",
            "",
            "> 这是 OmniFlow-AI 系统内草稿箱, 不是平台官方草稿箱。发布仍需要你进入平台官方发布页手动确认提交。",
            "",
            "## 正文",
            "",
            str(draft["body"]),
            "",
            "## 标签",
            "",
            tag_text,
            "",
            "## 摘要",
            "",
            str(draft.get("summary") or "无"),
            "",
            "## CTA",
            "",
            str(draft.get("cta") or "无"),
            "",
            "## Notes",
            "",
            str(draft.get("notes") or "无"),
            "",
        ]
        return "\n".join(lines)
