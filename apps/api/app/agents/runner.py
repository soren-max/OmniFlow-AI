"""Runner API for deterministic LangGraph content preview workflow."""

from __future__ import annotations

from typing import cast

from api.app.agents.state import ContentWorkflowState
from api.app.agents.workflow import build_content_preview_workflow
from api.app.telemetry.service import TraceService, trace_service


def run_content_preview_workflow(
    project_id: str,
    source_title: str,
    source_content: str,
    target_platforms: list[str],
    service: TraceService = trace_service,
) -> ContentWorkflowState:
    """Run the content preview workflow without exposing LangGraph internals."""
    run = service.create_run(
        project_id=project_id,
        workflow_name="content_preview",
        input_snapshot={
            "source_title": source_title,
            "source_content": source_content,
            "target_platforms": target_platforms,
        },
    )
    initial_state: ContentWorkflowState = {
        "run_id": run.run_id,
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
    workflow = build_content_preview_workflow(service)
    try:
        final_state = cast(ContentWorkflowState, workflow.invoke(initial_state))
    except Exception as exc:
        service.fail_run(run.run_id, str(exc), output_snapshot=initial_state)
        raise

    if final_state["status"] == "failed":
        service.fail_run(
            run_id=run.run_id,
            error_message="; ".join(final_state["errors"]) or "workflow failed",
            output_snapshot=final_state,
        )
    else:
        service.finish_run(run.run_id, output_snapshot=final_state)
    return final_state
