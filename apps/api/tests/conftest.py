"""Shared database fixtures for API tests."""

from __future__ import annotations

from collections.abc import Generator

import pytest
from api.app.core.database import Base
from api.app.repositories.project_repository import ProjectRepository
from api.app.telemetry.repository import TraceRepository as TelemetryTraceRepository
from api.app.telemetry.service import TraceService
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool


@pytest.fixture
def db_session_factory() -> Generator[sessionmaker[Session], None, None]:
    """Create an isolated in-memory SQLite database for one test."""
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    try:
        yield factory
    finally:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture(autouse=True)
def _use_sqlite_repositories(
    db_session_factory: sessionmaker[Session],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Point API singletons at the isolated test database."""
    from api.app.agents import runner
    from api.app.api import projects, runs
    from api.app.telemetry import service as telemetry_service_module

    project_repository = ProjectRepository(session_factory=db_session_factory)
    trace_repository = TelemetryTraceRepository(session_factory=db_session_factory)
    trace_service = TraceService(repository=trace_repository)

    monkeypatch.setattr(projects._service, "_repository", project_repository)
    monkeypatch.setattr(runs._service, "_repository", trace_repository)
    monkeypatch.setattr(runner, "trace_service", trace_service)
    monkeypatch.setattr(telemetry_service_module.trace_service, "_repository", trace_repository)
