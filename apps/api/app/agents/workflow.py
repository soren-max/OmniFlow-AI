"""LangGraph content preview workflow skeleton."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, cast

from api.app.agents.nodes import (
    finish_node,
    intake_node,
    platform_strategy_node,
    preview_generation_node,
)
from api.app.agents.state import ContentWorkflowState
from api.app.telemetry.service import TraceService, trace_service
from langgraph.graph import END, START, StateGraph


def traced_node(
    node_name: str,
    node_fn: Callable[[ContentWorkflowState], ContentWorkflowState],
    service: TraceService,
) -> Callable[[ContentWorkflowState], ContentWorkflowState]:
    """Wrap a LangGraph node with Agent Step trace recording."""

    def wrapped(state: ContentWorkflowState) -> ContentWorkflowState:
        run_id = state.get("run_id")
        if run_id is None:
            return node_fn(state)

        step = service.create_step(
            run_id=run_id,
            node_name=node_name,
            input_snapshot=state,
        )
        try:
            next_state = node_fn(state)
        except Exception as exc:
            service.fail_step(step.step_id, str(exc))
            raise

        if next_state["status"] == "failed":
            error_message = "; ".join(next_state["errors"]) or "workflow node failed"
            service.fail_step(
                step_id=step.step_id,
                error_message=error_message,
                output_snapshot=next_state,
            )
        else:
            service.finish_step(
                step_id=step.step_id,
                output_snapshot=next_state,
            )
        return next_state

    return wrapped


def _as_langgraph_node(
    node_name: str,
    node_fn: Callable[[ContentWorkflowState], ContentWorkflowState],
    service: TraceService,
) -> Any:
    return cast(Any, traced_node(node_name, node_fn, service))


def build_content_preview_workflow(service: TraceService = trace_service) -> Any:
    """Build a deterministic LangGraph workflow for platform previews."""
    graph = StateGraph(ContentWorkflowState)
    graph.add_node("intake", _as_langgraph_node("intake", intake_node, service))
    graph.add_node(
        "platform_strategy",
        _as_langgraph_node("platform_strategy", platform_strategy_node, service),
    )
    graph.add_node(
        "preview_generation",
        _as_langgraph_node("preview_generation", preview_generation_node, service),
    )
    graph.add_node("finish", _as_langgraph_node("finish", finish_node, service))

    graph.add_edge(START, "intake")
    graph.add_edge("intake", "platform_strategy")
    graph.add_edge("platform_strategy", "preview_generation")
    graph.add_edge("preview_generation", "finish")
    graph.add_edge("finish", END)

    return graph.compile()
