"""Agent Run trace query API routes."""

from __future__ import annotations

from api.app.schemas.common import ApiResponse, ok
from api.app.telemetry.schemas import AgentRun, AgentStep
from api.app.telemetry.service import AgentRunNotFoundError, trace_service
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/runs", tags=["agent-runs"])

_service = trace_service


@router.get("/{run_id}", response_model=ApiResponse[AgentRun])
async def get_run(run_id: str) -> ApiResponse[AgentRun]:
    """Return an Agent Run trace."""
    try:
        return ok(_service.get_run(run_id))
    except AgentRunNotFoundError:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "AGENT_RUN_NOT_FOUND",
                "message": f"Agent run not found: {run_id}",
                "details": {"run_id": run_id},
            },
        )


@router.get("/{run_id}/steps", response_model=ApiResponse[list[AgentStep]])
async def list_run_steps(run_id: str) -> ApiResponse[list[AgentStep]]:
    """Return Agent Step traces for a run."""
    try:
        return ok(_service.list_steps_by_run(run_id))
    except AgentRunNotFoundError:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "AGENT_RUN_NOT_FOUND",
                "message": f"Agent run not found: {run_id}",
                "details": {"run_id": run_id},
            },
        )
