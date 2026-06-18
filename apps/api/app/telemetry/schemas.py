"""Pydantic schemas for Agent execution traces."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class TraceStatus(StrEnum):
    """Lifecycle status for Agent runs and steps."""

    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentRun(BaseModel):
    """A single LangGraph workflow execution trace."""

    run_id: str
    project_id: str
    workflow_name: str
    status: TraceStatus
    input_snapshot: dict[str, Any]
    output_snapshot: dict[str, Any] | None = None
    error_message: str | None = None
    started_at: datetime
    finished_at: datetime | None = None
    total_latency_ms: int | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AgentStep(BaseModel):
    """A single LangGraph node execution trace."""

    step_id: str
    run_id: str
    node_name: str
    status: TraceStatus
    input_snapshot: dict[str, Any]
    output_snapshot: dict[str, Any] | None = None
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    error_message: str | None = None
    latency_ms: int | None = None
    started_at: datetime
    finished_at: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
