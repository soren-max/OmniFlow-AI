"""SQLAlchemy models for Agent run and step traces."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from api.app.core.database import Base
from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class AgentRunModel(Base):
    """Persisted LangGraph workflow execution trace."""

    __tablename__ = "agent_runs"

    run_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    workflow_name: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    input_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    output_snapshot: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    total_latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    steps: Mapped[list[AgentStepModel]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
        order_by="AgentStepModel.created_at",
    )


class AgentStepModel(Base):
    """Persisted LangGraph node execution trace."""

    __tablename__ = "agent_steps"

    step_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    run_id: Mapped[str] = mapped_column(
        ForeignKey("agent_runs.run_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    node_name: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    input_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    output_snapshot: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    tool_calls: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    run: Mapped[AgentRunModel] = relationship(back_populates="steps")
