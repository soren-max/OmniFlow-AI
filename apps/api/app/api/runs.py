"""Agent run trace API routes."""

from __future__ import annotations

from api.app.schemas.common import ApiResponse, ok
from api.app.schemas.trace import AgentRun, AgentStep
from api.app.services.trace_service import AgentRunNotFoundError, AgentTraceService
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/runs", tags=["agent-runs"])

_service = AgentTraceService()


@router.get("/{run_id}", response_model=ApiResponse[AgentRun])
async def get_run(run_id: str) -> ApiResponse[AgentRun]:
    """Get an Agent run trace by id."""
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
    """List Agent step traces for a run."""
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
