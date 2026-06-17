"""Input normalization node for the content preview workflow."""

from __future__ import annotations

from api.app.agents.state import ContentWorkflowState


def intake_node(state: ContentWorkflowState) -> ContentWorkflowState:
    """Normalize source content and record validation errors."""
    normalized_title = state["source_title"].strip()
    normalized_content = state["source_content"].strip()
    normalized_platforms = [
        platform.strip().lower() for platform in state["target_platforms"] if platform.strip()
    ]

    errors = list(state["errors"])
    if not normalized_title:
        errors.append("source_title must not be empty")
    if not normalized_content:
        errors.append("source_content must not be empty")
    if not normalized_platforms:
        errors.append("target_platforms must include at least one platform")

    return {
        **state,
        "source_title": normalized_title,
        "source_content": normalized_content,
        "target_platforms": normalized_platforms,
        "normalized_input": {
            "title": normalized_title,
            "content": normalized_content,
            "platforms": normalized_platforms,
        },
        "errors": errors,
        "status": "failed" if errors else "normalized",
    }
