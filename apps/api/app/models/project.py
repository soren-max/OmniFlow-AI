"""SQLAlchemy models for content projects, previews, and mock publishes."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from api.app.core.database import Base
from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class ContentProjectModel(Base):
    """Persisted source content project."""

    __tablename__ = "content_projects"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    source_text: Mapped[str] = mapped_column(Text, nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="created")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    previews: Mapped[list[PlatformContentModel]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="PlatformContentModel.created_at",
    )
    publish_tasks: Mapped[list[PublishTaskModel]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )


class PlatformContentModel(Base):
    """Persisted platform-specific preview/adaptation output."""

    __tablename__ = "platform_contents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("content_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    platform: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    platform_display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    preview_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    validation_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    rendered_html: Mapped[str] = mapped_column(Text, nullable=False)
    word_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    estimated_read_time_min: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    warnings_json: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    project: Mapped[ContentProjectModel] = relationship(back_populates="previews")


class PublishTaskModel(Base):
    """Persisted mock publish task for a project."""

    __tablename__ = "publish_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("content_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    mode: Mapped[str] = mapped_column(String(20), nullable=False, default="mock")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="completed")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    project: Mapped[ContentProjectModel] = relationship(back_populates="publish_tasks")
    results: Mapped[list[PublishResultModel]] = relationship(
        back_populates="task",
        cascade="all, delete-orphan",
        order_by="PublishResultModel.id",
    )


class PublishResultModel(Base):
    """Persisted per-platform mock publish result."""

    __tablename__ = "publish_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(
        ForeignKey("publish_tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    platform_display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    mock_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    task: Mapped[PublishTaskModel] = relationship(back_populates="results")
