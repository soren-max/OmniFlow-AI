"""Tests for Agent Run and Agent Step tracing."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any, cast

import pytest
from api.app.agents.runner import run_content_preview_workflow
from api.app.api.projects import _service
from api.app.main import app
from api.app.repositories.project_repository import ProjectRepository
from api.app.telemetry.repository import TraceRepository
from api.app.telemetry.schemas import TraceStatus
from api.app.telemetry.service import TraceService, trace_service
from httpx import ASGITransport, AsyncClient, Response
from sqlalchemy.orm import Session, sessionmaker

SAMPLE_CONTENT = (
    "Trace workflow test content with enough detail for adapter preview generation. "
    "It contains multiple sentences so validation and preview rendering can run "
    "through the deterministic LangGraph skeleton without calling an LLM.\n\n"
    "## Details\n\n"
    "The test verifies Agent Run and Agent Step trace records."
)

ALL_PLATFORMS = ["wechat", "zhihu", "bilibili", "xiaohongshu", "douyin"]


def _unwrap_success(response: Response) -> dict[str, Any]:
    json_response = cast(dict[str, Any], response.json())
    assert json_response["success"] is True
    assert json_response["error"] is None
    assert json_response["data"] is not None
    return cast(dict[str, Any], json_response["data"])


@pytest.fixture
def service(db_session_factory: sessionmaker[Session]) -> TraceService:
    """Create an isolated trace service."""
    return TraceService(repository=TraceRepository(session_factory=db_session_factory))


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client with clean in-memory stores."""
    repo: ProjectRepository = _service._repository
    repo.clear()
    trace_service.clear()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    repo.clear()
    trace_service.clear()


class TestTraceService:
    def test_run_lifecycle(self, service: TraceService) -> None:
        run = service.create_run(
            project_id="project-1",
            workflow_name="content_preview",
            input_snapshot={"platforms": ["wechat"]},
        )
        assert run.status == TraceStatus.RUNNING

        completed = service.finish_run(
            run.run_id,
            output_snapshot={"status": "completed"},
        )
        assert completed.status == TraceStatus.COMPLETED
        assert completed.output_snapshot == {"status": "completed"}
        assert completed.total_latency_ms is not None
        assert completed.total_latency_ms >= 0

    def test_fail_run_records_error_message(self, service: TraceService) -> None:
        run = service.create_run("project-1", "content_preview", {})

        failed = service.fail_run(run.run_id, "workflow failed")

        assert failed.status == TraceStatus.FAILED
        assert failed.error_message == "workflow failed"
        assert failed.total_latency_ms is not None
        assert failed.total_latency_ms >= 0

    def test_step_lifecycle_and_list_by_run(self, service: TraceService) -> None:
        run = service.create_run("project-1", "content_preview", {})
        step = service.create_step(
            run_id=run.run_id,
            node_name="intake",
            input_snapshot={"status": "initialized"},
        )
        assert step.status == TraceStatus.RUNNING

        completed = service.finish_step(
            step.step_id,
            output_snapshot={"status": "normalized"},
        )
        assert completed.status == TraceStatus.COMPLETED
        assert completed.latency_ms is not None
        assert completed.latency_ms >= 0

        failed_step = service.create_step(run.run_id, "preview_generation", {})
        failed = service.fail_step(failed_step.step_id, "adapter failed")
        assert failed.status == TraceStatus.FAILED
        assert failed.error_message == "adapter failed"

        steps = service.list_steps_by_run(run.run_id)
        assert [item.node_name for item in steps] == ["intake", "preview_generation"]


class TestWorkflowTracing:
    def test_runner_creates_completed_run_and_steps(self, service: TraceService) -> None:
        state = run_content_preview_workflow(
            project_id="project-1",
            source_title="Trace Test",
            source_content=SAMPLE_CONTENT,
            target_platforms=ALL_PLATFORMS,
            service=service,
        )

        run_id = state["run_id"]
        assert run_id is not None
        run = service.get_run(run_id)
        assert run.status == TraceStatus.COMPLETED
        assert run.total_latency_ms is not None

        steps = service.list_steps_by_run(run_id)
        assert [step.node_name for step in steps] == [
            "intake",
            "platform_strategy",
            "preview_generation",
            "finish",
        ]
        assert all(step.status == TraceStatus.COMPLETED for step in steps)
        assert all(step.input_snapshot for step in steps)
        assert all(step.output_snapshot is not None for step in steps)

    def test_runner_marks_run_failed_when_workflow_records_errors(
        self,
        service: TraceService,
    ) -> None:
        state = run_content_preview_workflow(
            project_id="project-1",
            source_title="Trace Test",
            source_content="",
            target_platforms=ALL_PLATFORMS,
            service=service,
        )

        run_id = state["run_id"]
        assert run_id is not None
        run = service.get_run(run_id)
        assert run.status == TraceStatus.FAILED
        assert "source_content must not be empty" in (run.error_message or "")
        assert any(step.status == TraceStatus.FAILED for step in service.list_steps_by_run(run_id))


class TestTraceApi:
    async def test_get_run_and_steps(self, client: AsyncClient) -> None:
        create_response = await client.post(
            "/api/projects",
            json={"title": "Trace API", "source_text": SAMPLE_CONTENT},
        )
        project_id = _unwrap_success(create_response)["id"]

        preview_response = await client.post(
            f"/api/projects/{project_id}/agent-preview",
            json={"platforms": ALL_PLATFORMS},
        )
        state = _unwrap_success(preview_response)
        run_id = state["run_id"]
        assert run_id

        run_response = await client.get(f"/api/runs/{run_id}")
        run = _unwrap_success(run_response)
        assert run["run_id"] == run_id
        assert run["status"] == "completed"
        assert run["total_latency_ms"] is not None

        steps_response = await client.get(f"/api/runs/{run_id}/steps")
        steps = cast(list[dict[str, Any]], steps_response.json()["data"])
        assert [step["node_name"] for step in steps] == [
            "intake",
            "platform_strategy",
            "preview_generation",
            "finish",
        ]
        assert all(step["status"] == "completed" for step in steps)

    async def test_missing_run_returns_error(self, client: AsyncClient) -> None:
        response = await client.get("/api/runs/missing-run")

        assert response.status_code == 404
        body = response.json()
        assert body["success"] is False
        assert body["error"]["code"] == "AGENT_RUN_NOT_FOUND"
