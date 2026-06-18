"""In-memory repository for Agent run and step trace records."""

from __future__ import annotations

from api.app.schemas.trace import AgentRun, AgentStep


class TraceRepository:
    """In-memory store for Agent execution traces.

    Current stage: in-memory storage only. This boundary can be replaced by a
    database-backed repository when SQLAlchemy models are introduced.
    """

    def __init__(self) -> None:
        self._runs: dict[str, AgentRun] = {}
        self._steps: dict[str, AgentStep] = {}

    def save_run(self, run: AgentRun) -> AgentRun:
        """Persist an Agent run record."""
        stored = run.model_copy(deep=True)
        self._runs[stored.run_id] = stored
        return stored.model_copy(deep=True)

    def find_run_by_id(self, run_id: str) -> AgentRun | None:
        """Look up an Agent run by id."""
        run = self._runs.get(run_id)
        return run.model_copy(deep=True) if run is not None else None

    def save_step(self, step: AgentStep) -> AgentStep:
        """Persist an Agent step record."""
        stored = step.model_copy(deep=True)
        self._steps[stored.step_id] = stored
        return stored.model_copy(deep=True)

    def find_step_by_id(self, step_id: str) -> AgentStep | None:
        """Look up an Agent step by id."""
        step = self._steps.get(step_id)
        return step.model_copy(deep=True) if step is not None else None

    def list_steps_by_run(self, run_id: str) -> list[AgentStep]:
        """Return steps for a run in creation order."""
        return [
            step.model_copy(deep=True) for step in self._steps.values() if step.run_id == run_id
        ]

    def clear(self) -> None:
        """Remove all trace records."""
        self._runs.clear()
        self._steps.clear()
