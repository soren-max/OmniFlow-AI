"""Database-backed repository for Agent run and step trace records."""

from __future__ import annotations

from collections.abc import Callable
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any

from api.app.core.database import SessionLocal
from api.app.models.trace import AgentRunModel, AgentStepModel
from api.app.schemas.trace import AgentRun, AgentStep, TraceStatus
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

SessionFactory = Callable[[], Session]


class TraceRepository:
    """Persist Agent execution traces in the database."""

    def __init__(self, session_factory: SessionFactory = SessionLocal) -> None:
        self._session_factory = session_factory

    def save_run(self, run: AgentRun) -> AgentRun:
        """Persist an Agent run record."""
        with self._session_scope() as session:
            model = session.get(AgentRunModel, run.run_id)
            if model is None:
                model = AgentRunModel(run_id=run.run_id)
                session.add(model)
            model.project_id = run.project_id
            model.workflow_name = run.workflow_name
            model.status = run.status.value
            model.input_snapshot = run.input_snapshot
            model.output_snapshot = run.output_snapshot
            model.error_message = run.error_message
            model.started_at = run.started_at
            model.finished_at = run.finished_at
            model.total_latency_ms = run.total_latency_ms
            model.created_at = run.created_at
        return run.model_copy(deep=True)

    def find_run_by_id(self, run_id: str) -> AgentRun | None:
        """Look up an Agent run by id."""
        with self._session_scope(commit=False) as session:
            model = session.get(AgentRunModel, run_id)
            return self._run_from_model(model) if model is not None else None

    def save_step(self, step: AgentStep) -> AgentStep:
        """Persist an Agent step record."""
        with self._session_scope() as session:
            model = session.get(AgentStepModel, step.step_id)
            if model is None:
                model = AgentStepModel(step_id=step.step_id)
                session.add(model)
            model.run_id = step.run_id
            model.node_name = step.node_name
            model.status = step.status.value
            model.input_snapshot = step.input_snapshot
            model.output_snapshot = step.output_snapshot
            model.tool_calls = step.tool_calls
            model.error_message = step.error_message
            model.latency_ms = step.latency_ms
            model.started_at = step.started_at
            model.finished_at = step.finished_at
            model.created_at = step.created_at
        return step.model_copy(deep=True)

    def find_step_by_id(self, step_id: str) -> AgentStep | None:
        """Look up an Agent step by id."""
        with self._session_scope(commit=False) as session:
            model = session.get(AgentStepModel, step_id)
            return self._step_from_model(model) if model is not None else None

    def list_steps_by_run(self, run_id: str) -> list[AgentStep]:
        """Return steps for a run in creation order."""
        with self._session_scope(commit=False) as session:
            models = session.scalars(
                select(AgentStepModel)
                .where(AgentStepModel.run_id == run_id)
                .order_by(AgentStepModel.created_at, AgentStepModel.step_id)
            ).all()
            return [self._step_from_model(model) for model in models]

    def clear(self) -> None:
        """Remove all trace records."""
        with self._session_scope() as session:
            session.execute(delete(AgentStepModel))
            session.execute(delete(AgentRunModel))

    @contextmanager
    def _session_scope(self, *, commit: bool = True) -> Any:
        session = self._session_factory()
        try:
            yield session
            if commit:
                session.commit()
        except Exception:
            if commit:
                session.rollback()
            raise
        finally:
            session.close()

    @staticmethod
    def _run_from_model(model: AgentRunModel) -> AgentRun:
        return AgentRun(
            run_id=model.run_id,
            project_id=model.project_id,
            workflow_name=model.workflow_name,
            status=TraceStatus(model.status),
            input_snapshot=model.input_snapshot or {},
            output_snapshot=model.output_snapshot or {},
            error_message=model.error_message,
            started_at=TraceRepository._aware(model.started_at),
            finished_at=TraceRepository._optional_aware(model.finished_at),
            total_latency_ms=model.total_latency_ms,
            created_at=TraceRepository._aware(model.created_at),
        )

    @staticmethod
    def _step_from_model(model: AgentStepModel) -> AgentStep:
        return AgentStep(
            step_id=model.step_id,
            run_id=model.run_id,
            node_name=model.node_name,
            status=TraceStatus(model.status),
            input_snapshot=model.input_snapshot or {},
            output_snapshot=model.output_snapshot or {},
            tool_calls=model.tool_calls,
            error_message=model.error_message,
            latency_ms=model.latency_ms,
            started_at=TraceRepository._aware(model.started_at),
            finished_at=TraceRepository._optional_aware(model.finished_at),
            created_at=TraceRepository._aware(model.created_at),
        )

    @staticmethod
    def _aware(value: datetime) -> datetime:
        if value.tzinfo is not None:
            return value
        return value.replace(tzinfo=timezone.utc)

    @staticmethod
    def _optional_aware(value: datetime | None) -> datetime | None:
        return None if value is None else TraceRepository._aware(value)
