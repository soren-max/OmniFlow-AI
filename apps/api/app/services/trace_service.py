"""Service layer for Agent execution trace records."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from api.app.repositories.trace_repository import TraceRepository
from api.app.schemas.trace import AgentRun, AgentStep, TraceStatus


class AgentRunNotFoundError(LookupError):
    """Raised when an Agent run does not exist."""

    def __init__(self, run_id: str) -> None:
        self.run_id = run_id
        super().__init__(f"Agent run not found: {run_id}")


class AgentStepNotFoundError(LookupError):
    """Raised when an Agent step does not exist."""

    def __init__(self, step_id: str) -> None:
        self.step_id = step_id
        super().__init__(f"Agent step not found: {step_id}")


class TraceStatusTransitionError(ValueError):
    """Raised when a trace record is completed more than once."""

    def __init__(self, record_id: str, status: TraceStatus) -> None:
        self.record_id = record_id
        self.status = status
        super().__init__(f"Trace record {record_id!r} is already {status.value}.")


class AgentTraceService:
    """Business logic for Agent run and step lifecycle tracking."""

    def __init__(self, repository: TraceRepository | None = None) -> None:
        self._repository = repository or TraceRepository()

    def create_run(
        self,
        project_id: str,
        workflow_name: str,
        input_snapshot: dict[str, Any] | None = None,
    ) -> AgentRun:
        """Create a running Agent workflow trace."""
        now = datetime.now(timezone.utc)
        run = AgentRun(
            run_id=uuid4().hex,
            project_id=project_id,
            workflow_name=workflow_name,
            status=TraceStatus.RUNNING,
            input_snapshot=input_snapshot or {},
            started_at=now,
            created_at=now,
        )
        return self._repository.save_run(run)

    def get_run(self, run_id: str) -> AgentRun:
        """Return an Agent run by id."""
        run = self._repository.find_run_by_id(run_id)
        if run is None:
            raise AgentRunNotFoundError(run_id)
        return run

    def finish_run(
        self,
        run_id: str,
        output_snapshot: dict[str, Any] | None = None,
    ) -> AgentRun:
        """Mark a running Agent run as succeeded."""
        run = self.get_run(run_id)
        self._ensure_running(run.run_id, run.status)
        finished_at = datetime.now(timezone.utc)
        run.status = TraceStatus.SUCCEEDED
        run.output_snapshot = output_snapshot or {}
        run.error_message = None
        run.finished_at = finished_at
        run.total_latency_ms = self._latency_ms(run.started_at, finished_at)
        return self._repository.save_run(run)

    def fail_run(self, run_id: str, error_message: str) -> AgentRun:
        """Mark a running Agent run as failed."""
        run = self.get_run(run_id)
        self._ensure_running(run.run_id, run.status)
        finished_at = datetime.now(timezone.utc)
        run.status = TraceStatus.FAILED
        run.error_message = error_message
        run.finished_at = finished_at
        run.total_latency_ms = self._latency_ms(run.started_at, finished_at)
        return self._repository.save_run(run)

    def create_step(
        self,
        run_id: str,
        node_name: str,
        input_snapshot: dict[str, Any] | None = None,
        tool_calls: list[dict[str, Any]] | None = None,
    ) -> AgentStep:
        """Create a running Agent node trace within an existing run."""
        self.get_run(run_id)
        now = datetime.now(timezone.utc)
        step = AgentStep(
            step_id=uuid4().hex,
            run_id=run_id,
            node_name=node_name,
            status=TraceStatus.RUNNING,
            input_snapshot=input_snapshot or {},
            tool_calls=tool_calls or [],
            started_at=now,
            created_at=now,
        )
        return self._repository.save_step(step)

    def finish_step(
        self,
        step_id: str,
        output_snapshot: dict[str, Any] | None = None,
        tool_calls: list[dict[str, Any]] | None = None,
    ) -> AgentStep:
        """Mark a running Agent step as succeeded."""
        step = self._get_step(step_id)
        self._ensure_running(step.step_id, step.status)
        finished_at = datetime.now(timezone.utc)
        step.status = TraceStatus.SUCCEEDED
        step.output_snapshot = output_snapshot or {}
        if tool_calls is not None:
            step.tool_calls = tool_calls
        step.error_message = None
        step.finished_at = finished_at
        step.latency_ms = self._latency_ms(step.started_at, finished_at)
        return self._repository.save_step(step)

    def fail_step(self, step_id: str, error_message: str) -> AgentStep:
        """Mark a running Agent step as failed."""
        step = self._get_step(step_id)
        self._ensure_running(step.step_id, step.status)
        finished_at = datetime.now(timezone.utc)
        step.status = TraceStatus.FAILED
        step.error_message = error_message
        step.finished_at = finished_at
        step.latency_ms = self._latency_ms(step.started_at, finished_at)
        return self._repository.save_step(step)

    def list_steps_by_run(self, run_id: str) -> list[AgentStep]:
        """Return all steps for an Agent run."""
        self.get_run(run_id)
        return self._repository.list_steps_by_run(run_id)

    def _get_step(self, step_id: str) -> AgentStep:
        step = self._repository.find_step_by_id(step_id)
        if step is None:
            raise AgentStepNotFoundError(step_id)
        return step

    @staticmethod
    def _ensure_running(record_id: str, status: TraceStatus) -> None:
        if status != TraceStatus.RUNNING:
            raise TraceStatusTransitionError(record_id, status)

    @staticmethod
    def _latency_ms(started_at: datetime, finished_at: datetime) -> int:
        return max(0, int((finished_at - started_at).total_seconds() * 1000))
