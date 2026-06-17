"""Pydantic schemas for Agent execution traces."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class TraceStatus(StrEnum):
    """Lifecycle status for Agent runs and steps."""

    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class AgentRun(BaseModel):
    """A single Agent workflow execution record."""

    run_id: str
    project_id: str
    workflow_name: str
    status: TraceStatus = TraceStatus.RUNNING
    input_snapshot: dict[str, Any] = Field(default_factory=dict)
    output_snapshot: dict[str, Any] = Field(default_factory=dict)
    error_message: str | None = None
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: datetime | None = None
    total_latency_ms: int | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AgentStep(BaseModel):
    """A single Agent node execution record within a run."""

    step_id: str
    run_id: str
    node_name: str
    status: TraceStatus = TraceStatus.RUNNING
    input_snapshot: dict[str, Any] = Field(default_factory=dict)
    output_snapshot: dict[str, Any] = Field(default_factory=dict)
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    error_message: str | None = None
    latency_ms: int | None = None
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
