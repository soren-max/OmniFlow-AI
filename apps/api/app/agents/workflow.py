"""LangGraph content preview workflow skeleton."""

from __future__ import annotations

from typing import Any

from api.app.agents.nodes import (
    finish_node,
    intake_node,
    platform_strategy_node,
    preview_generation_node,
)
from api.app.agents.state import ContentWorkflowState
from langgraph.graph import END, START, StateGraph


def build_content_preview_workflow() -> Any:
    """Build a deterministic LangGraph workflow for platform previews."""
    graph = StateGraph(ContentWorkflowState)
    graph.add_node("intake", intake_node)
    graph.add_node("platform_strategy", platform_strategy_node)
    graph.add_node("preview_generation", preview_generation_node)
    graph.add_node("finish", finish_node)

    graph.add_edge(START, "intake")
    graph.add_edge("intake", "platform_strategy")
    graph.add_edge("platform_strategy", "preview_generation")
    graph.add_edge("preview_generation", "finish")
    graph.add_edge("finish", END)

    return graph.compile()
