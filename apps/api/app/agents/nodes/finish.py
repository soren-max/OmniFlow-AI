"""Finish node for the content preview workflow."""

from __future__ import annotations

from api.app.agents.state import ContentWorkflowState


def finish_node(state: ContentWorkflowState) -> ContentWorkflowState:
    """Mark the workflow complete unless a previous node recorded errors."""
    return {
        **state,
        "status": "failed" if state["errors"] else "completed",
    }
