"""Preview generation node for the content preview workflow."""

from __future__ import annotations

from typing import Any

from api.app.adapters.registry import get_adapter
from api.app.adapters.types import Platform, PlatformContent
from api.app.agents.state import ContentWorkflowState


def preview_generation_node(state: ContentWorkflowState) -> ContentWorkflowState:
    """Generate previews through the PlatformAdapter registry."""
    if state["errors"]:
        return state

    previews: dict[str, Any] = {}
    errors = list(state["errors"])

    for platform_name in state["target_platforms"]:
        try:
            platform = Platform(platform_name)
            adapter = get_adapter(platform)
            content = PlatformContent(
                platform=platform,
                title=state["source_title"],
                body=state["source_content"],
                metadata={
                    "workflow": "content_preview",
                    "strategy": state["platform_strategy"].get(platform_name, {}),
                },
            )
            transformed = adapter.transform_content(content)
            validation = adapter.validate_content(transformed)
            preview = adapter.build_preview(transformed)
        except Exception as exc:
            errors.append(f"{platform_name}: {exc}")
            continue

        previews[platform.value] = {
            "platform": platform.value,
            "platform_display_name": platform.display_name,
            "title": transformed.title,
            "content": transformed.body,
            "metadata": {
                **transformed.metadata,
                "hooks": transformed.hooks,
                "tags": transformed.tags,
                "summary": transformed.summary,
            },
            "validation": {
                "is_valid": validation.is_valid,
                "errors": validation.errors,
                "warnings": validation.warnings,
            },
            "preview": {
                "rendered_html": preview.rendered_html,
                "word_count": preview.word_count,
                "estimated_read_time_min": preview.estimated_read_time_min,
                "screenshot_url": preview.screenshot_url,
                "metadata": preview.metadata,
            },
            "rendered_html": preview.rendered_html,
            "word_count": preview.word_count,
            "estimated_read_time_min": preview.estimated_read_time_min,
            "warnings": validation.warnings,
        }

    return {
        **state,
        "previews": previews,
        "errors": errors,
        "status": "failed" if errors else "previews_ready",
    }
