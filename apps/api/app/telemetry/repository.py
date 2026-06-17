"""In-memory repository for Agent trace records."""

from __future__ import annotations

from api.app.telemetry.schemas import AgentRun, AgentStep


class TraceRepository:
    """Store Agent Run and Agent Step traces in memory."""

    def __init__(self) -> None:
        self._runs: dict[str, AgentRun] = {}
        self._steps: dict[str, AgentStep] = {}

    def save_run(self, run: AgentRun) -> AgentRun:
        """Create or replace an Agent Run record."""
        stored = run.model_copy(deep=True)
        self._runs[run.run_id] = stored
        return stored.model_copy(deep=True)

    def get_run(self, run_id: str) -> AgentRun | None:
        """Return an Agent Run by id."""
        run = self._runs.get(run_id)
        return run.model_copy(deep=True) if run is not None else None

    def save_step(self, step: AgentStep) -> AgentStep:
        """Create or replace an Agent Step record."""
        stored = step.model_copy(deep=True)
        self._steps[step.step_id] = stored
        return stored.model_copy(deep=True)

    def get_step(self, step_id: str) -> AgentStep | None:
        """Return an Agent Step by id."""
        step = self._steps.get(step_id)
        return step.model_copy(deep=True) if step is not None else None

    def list_steps_by_run(self, run_id: str) -> list[AgentStep]:
        """Return all steps for a run in insertion order."""
        return [
            step.model_copy(deep=True) for step in self._steps.values() if step.run_id == run_id
        ]

    def clear(self) -> None:
        """Remove all trace records."""
        self._runs.clear()
        self._steps.clear()
