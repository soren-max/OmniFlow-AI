"""Service layer for Agent Run and Agent Step traces."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from api.app.telemetry.repository import TraceRepository
from api.app.telemetry.schemas import AgentRun, AgentStep, TraceStatus
from fastapi.encoders import jsonable_encoder


class AgentRunNotFoundError(LookupError):
    """Raised when an Agent Run cannot be found."""

    def __init__(self, run_id: str) -> None:
        self.run_id = run_id
        super().__init__(f"Agent run not found: {run_id}")


class AgentStepNotFoundError(LookupError):
    """Raised when an Agent Step cannot be found."""

    def __init__(self, step_id: str) -> None:
        self.step_id = step_id
        super().__init__(f"Agent step not found: {step_id}")


class TraceService:
    """Manage trace lifecycle transitions for LangGraph workflows."""

    def __init__(self, repository: TraceRepository | None = None) -> None:
        self._repository = repository or TraceRepository()

    def create_run(
        self,
        project_id: str,
        workflow_name: str,
        input_snapshot: Mapping[str, Any],
    ) -> AgentRun:
        """Create a running Agent Run trace."""
        now = datetime.now(timezone.utc)
        run = AgentRun(
            run_id=uuid4().hex,
            project_id=project_id,
            workflow_name=workflow_name,
            status=TraceStatus.RUNNING,
            input_snapshot=self._safe_snapshot(input_snapshot),
            started_at=now,
            created_at=now,
        )
        return self._repository.save_run(run)

    def finish_run(
        self,
        run_id: str,
        output_snapshot: Mapping[str, Any],
    ) -> AgentRun:
        """Mark an Agent Run as completed."""
        run = self.get_run(run_id)
        finished_at = datetime.now(timezone.utc)
        run.status = TraceStatus.COMPLETED
        run.output_snapshot = self._safe_snapshot(output_snapshot)
        run.error_message = None
        run.finished_at = finished_at
        run.total_latency_ms = self._latency_ms(run.started_at, finished_at)
        return self._repository.save_run(run)

    def fail_run(
        self,
        run_id: str,
        error_message: str,
        output_snapshot: Mapping[str, Any] | None = None,
    ) -> AgentRun:
        """Mark an Agent Run as failed."""
        run = self.get_run(run_id)
        finished_at = datetime.now(timezone.utc)
        run.status = TraceStatus.FAILED
        run.output_snapshot = (
            self._safe_snapshot(output_snapshot) if output_snapshot is not None else None
        )
        run.error_message = error_message
        run.finished_at = finished_at
        run.total_latency_ms = self._latency_ms(run.started_at, finished_at)
        return self._repository.save_run(run)

    def get_run(self, run_id: str) -> AgentRun:
        """Return an Agent Run by id."""
        run = self._repository.get_run(run_id)
        if run is None:
            raise AgentRunNotFoundError(run_id)
        return run

    def create_step(
        self,
        run_id: str,
        node_name: str,
        input_snapshot: Mapping[str, Any],
        tool_calls: list[dict[str, Any]] | None = None,
    ) -> AgentStep:
        """Create a running Agent Step trace."""
        self.get_run(run_id)
        now = datetime.now(timezone.utc)
        step = AgentStep(
            step_id=uuid4().hex,
            run_id=run_id,
            node_name=node_name,
            status=TraceStatus.RUNNING,
            input_snapshot=self._safe_snapshot(input_snapshot),
            tool_calls=tool_calls or [],
            started_at=now,
            created_at=now,
        )
        return self._repository.save_step(step)

    def finish_step(
        self,
        step_id: str,
        output_snapshot: Mapping[str, Any],
        tool_calls: list[dict[str, Any]] | None = None,
    ) -> AgentStep:
        """Mark an Agent Step as completed."""
        step = self._get_step(step_id)
        finished_at = datetime.now(timezone.utc)
        step.status = TraceStatus.COMPLETED
        step.output_snapshot = self._safe_snapshot(output_snapshot)
        if tool_calls is not None:
            step.tool_calls = tool_calls
        step.error_message = None
        step.finished_at = finished_at
        step.latency_ms = self._latency_ms(step.started_at, finished_at)
        return self._repository.save_step(step)

    def fail_step(
        self,
        step_id: str,
        error_message: str,
        output_snapshot: Mapping[str, Any] | None = None,
    ) -> AgentStep:
        """Mark an Agent Step as failed."""
        step = self._get_step(step_id)
        finished_at = datetime.now(timezone.utc)
        step.status = TraceStatus.FAILED
        step.output_snapshot = (
            self._safe_snapshot(output_snapshot) if output_snapshot is not None else None
        )
        step.error_message = error_message
        step.finished_at = finished_at
        step.latency_ms = self._latency_ms(step.started_at, finished_at)
        return self._repository.save_step(step)

    def list_steps_by_run(self, run_id: str) -> list[AgentStep]:
        """Return all steps for an Agent Run."""
        self.get_run(run_id)
        return self._repository.list_steps_by_run(run_id)

    def clear(self) -> None:
        """Remove all trace records."""
        self._repository.clear()

    def _get_step(self, step_id: str) -> AgentStep:
        step = self._repository.get_step(step_id)
        if step is None:
            raise AgentStepNotFoundError(step_id)
        return step

    @staticmethod
    def _latency_ms(started_at: datetime, finished_at: datetime) -> int:
        return max(0, int((finished_at - started_at).total_seconds() * 1000))

    @staticmethod
    def _safe_snapshot(snapshot: Mapping[str, Any]) -> dict[str, Any]:
        encoded = jsonable_encoder(dict(snapshot))
        return encoded if isinstance(encoded, dict) else {"value": encoded}


trace_service = TraceService()
