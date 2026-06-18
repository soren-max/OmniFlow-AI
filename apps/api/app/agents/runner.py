"""Runner API for deterministic LangGraph content preview workflow."""

from __future__ import annotations

from typing import cast

from api.app.agents.state import ContentWorkflowState
from api.app.agents.workflow import build_content_preview_workflow


def run_content_preview_workflow(
    project_id: str,
    source_title: str,
    source_content: str,
    target_platforms: list[str],
) -> ContentWorkflowState:
    """Run the content preview workflow without exposing LangGraph internals."""
    initial_state: ContentWorkflowState = {
        "project_id": project_id,
        "source_title": source_title,
        "source_content": source_content,
        "target_platforms": target_platforms,
        "normalized_input": {},
        "platform_strategy": {},
        "previews": {},
        "errors": [],
        "status": "initialized",
    }
    workflow = build_content_preview_workflow()
    return cast(ContentWorkflowState, workflow.invoke(initial_state))
