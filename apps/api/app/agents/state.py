"""Typed state for deterministic content preview workflows."""

from __future__ import annotations

from typing import Any, TypedDict


class ContentWorkflowState(TypedDict):
    """Shared state passed between LangGraph preview workflow nodes."""

    run_id: str | None
    project_id: str
    source_title: str
    source_content: str
    target_platforms: list[str]
    normalized_input: dict[str, Any]
    platform_strategy: dict[str, Any]
    previews: dict[str, Any]
    errors: list[str]
    status: str
