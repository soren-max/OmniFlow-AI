"""Tests for Agent run and step trace records."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any, cast

import pytest
from api.app.api.runs import _service as api_trace_service
from api.app.main import app
from api.app.telemetry.repository import TraceRepository
from api.app.telemetry.schemas import TraceStatus
from api.app.telemetry.service import (
    TraceService,
    TraceStatusTransitionError,
)
from httpx import ASGITransport, AsyncClient, Response
from sqlalchemy.orm import Session, sessionmaker


def _unwrap_success(response: Response) -> dict[str, Any]:
    json_response = cast(dict[str, Any], response.json())
    assert json_response["success"] is True
    assert json_response["error"] is None
    assert json_response["data"] is not None
    return cast(dict[str, Any], json_response["data"])


@pytest.fixture
def trace_service(db_session_factory: sessionmaker[Session]) -> TraceService:
    """Create an isolated trace service for unit tests."""
    return TraceService(repository=TraceRepository(session_factory=db_session_factory))


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client."""
    api_trace_service._repository.clear()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    api_trace_service._repository.clear()


class TestTraceService:
    def test_create_run(self, trace_service: TraceService) -> None:
        """Creating a run should store a running trace record."""
        run = trace_service.create_run(
            project_id="project-1",
            workflow_name="content_preview",
            input_snapshot={"platforms": ["wechat"]},
        )

        assert run.run_id
        assert run.project_id == "project-1"
        assert run.workflow_name == "content_preview"
        assert run.status == TraceStatus.RUNNING
        assert run.input_snapshot == {"platforms": ["wechat"]}
        assert run.output_snapshot is None
        assert run.error_message is None
        assert run.finished_at is None
        assert run.total_latency_ms is None

    def test_create_step(self, trace_service: TraceService) -> None:
        """Creating a step should attach it to an existing run."""
        run = trace_service.create_run("project-1", "content_preview")
        step = trace_service.create_step(
            run_id=run.run_id,
            node_name="preview_generation",
            input_snapshot={"platform": "wechat"},
            tool_calls=[{"name": "adapter.build_preview"}],
        )

        assert step.step_id
        assert step.run_id == run.run_id
        assert step.node_name == "preview_generation"
        assert step.status == TraceStatus.RUNNING
        assert step.input_snapshot == {"platform": "wechat"}
        assert step.tool_calls == [{"name": "adapter.build_preview"}]

    def test_finish_run(self, trace_service: TraceService) -> None:
        """Finishing a run should capture output and latency."""
        run = trace_service.create_run("project-1", "content_preview")

        finished = trace_service.finish_run(
            run.run_id,
            output_snapshot={"preview_count": 5},
        )

        assert finished.status == TraceStatus.COMPLETED
        assert finished.output_snapshot == {"preview_count": 5}
        assert finished.error_message is None
        assert finished.finished_at is not None
        assert finished.total_latency_ms is not None
        assert finished.total_latency_ms >= 0

    def test_fail_run(self, trace_service: TraceService) -> None:
        """Failing a run should capture the error message and latency."""
        run = trace_service.create_run("project-1", "content_preview")

        failed = trace_service.fail_run(run.run_id, "adapter failed")

        assert failed.status == TraceStatus.FAILED
        assert failed.error_message == "adapter failed"
        assert failed.finished_at is not None
        assert failed.total_latency_ms is not None
        assert failed.total_latency_ms >= 0

    def test_finish_step(self, trace_service: TraceService) -> None:
        """Finishing a step should capture output, tool calls, and latency."""
        run = trace_service.create_run("project-1", "content_preview")
        step = trace_service.create_step(run.run_id, "preview_generation")

        finished = trace_service.finish_step(
            step.step_id,
            output_snapshot={"status": "ok"},
            tool_calls=[{"name": "adapter.validate_content", "status": "ok"}],
        )

        assert finished.status == TraceStatus.COMPLETED
        assert finished.output_snapshot == {"status": "ok"}
        assert finished.tool_calls == [{"name": "adapter.validate_content", "status": "ok"}]
        assert finished.error_message is None
        assert finished.finished_at is not None
        assert finished.latency_ms is not None
        assert finished.latency_ms >= 0

    def test_fail_step(self, trace_service: TraceService) -> None:
        """Failing a step should capture the step error."""
        run = trace_service.create_run("project-1", "content_preview")
        step = trace_service.create_step(run.run_id, "preview_generation")

        failed = trace_service.fail_step(step.step_id, "validation failed")

        assert failed.status == TraceStatus.FAILED
        assert failed.error_message == "validation failed"
        assert failed.finished_at is not None
        assert failed.latency_ms is not None
        assert failed.latency_ms >= 0

    def test_list_steps_by_run(self, trace_service: TraceService) -> None:
        """Steps should be queryable by their run id."""
        run = trace_service.create_run("project-1", "content_preview")
        other_run = trace_service.create_run("project-2", "content_preview")
        first = trace_service.create_step(run.run_id, "content_intake")
        second = trace_service.create_step(run.run_id, "preview_generation")
        trace_service.create_step(other_run.run_id, "content_intake")

        steps = trace_service.list_steps_by_run(run.run_id)

        assert [step.step_id for step in steps] == [first.step_id, second.step_id]

    def test_status_cannot_transition_after_finish(
        self,
        trace_service: TraceService,
    ) -> None:
        """Completed records cannot be completed again."""
        run = trace_service.create_run("project-1", "content_preview")
        step = trace_service.create_step(run.run_id, "content_intake")

        trace_service.finish_run(run.run_id)
        trace_service.fail_step(step.step_id, "node error")

        with pytest.raises(TraceStatusTransitionError):
            trace_service.fail_run(run.run_id, "late error")
        with pytest.raises(TraceStatusTransitionError):
            trace_service.finish_step(step.step_id)


class TestAgentRunApi:
    async def test_get_run(self, client: AsyncClient) -> None:
        """GET /api/runs/{run_id} should return a trace run."""
        run = api_trace_service.create_run("project-1", "content_preview")

        response = await client.get(f"/api/runs/{run.run_id}")

        assert response.status_code == 200
        data = _unwrap_success(response)
        assert data["run_id"] == run.run_id
        assert data["project_id"] == "project-1"
        assert data["status"] == "running"

    async def test_get_run_steps(self, client: AsyncClient) -> None:
        """GET /api/runs/{run_id}/steps should return run steps."""
        run = api_trace_service.create_run("project-1", "content_preview")
        step = api_trace_service.create_step(run.run_id, "preview_generation")

        response = await client.get(f"/api/runs/{run.run_id}/steps")

        assert response.status_code == 200
        data = cast(list[dict[str, Any]], response.json()["data"])
        assert len(data) == 1
        assert data[0]["step_id"] == step.step_id
        assert data[0]["run_id"] == run.run_id
        assert data[0]["node_name"] == "preview_generation"
