"""Tests for the deterministic LangGraph content preview workflow."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any, cast

import pytest
from api.app.agents.nodes import (
    intake_node,
    platform_strategy_node,
    preview_generation_node,
)
from api.app.agents.runner import run_content_preview_workflow
from api.app.agents.state import ContentWorkflowState
from api.app.api.projects import _service
from api.app.main import app
from api.app.repositories.project_repository import ProjectRepository
from httpx import ASGITransport, AsyncClient, Response

SAMPLE_CONTENT = (
    "This is a deterministic workflow test article with enough detail to pass "
    "platform adapter validation. It explains the topic clearly and includes "
    "multiple useful points for preview generation.\n\n"
    "## Key ideas\n\n"
    "The workflow should normalize input, build strategies, and call adapters."
)

ALL_PLATFORMS = ["wechat", "zhihu", "bilibili", "xiaohongshu", "douyin"]


def _base_state(source_content: str = SAMPLE_CONTENT) -> ContentWorkflowState:
    return {
        "run_id": None,
        "project_id": "project-1",
        "source_title": " Workflow Test ",
        "source_content": source_content,
        "target_platforms": ALL_PLATFORMS,
        "normalized_input": {},
        "platform_strategy": {},
        "previews": {},
        "errors": [],
        "status": "initialized",
    }


def _unwrap_success(response: Response) -> dict[str, Any]:
    json_response = cast(dict[str, Any], response.json())
    assert json_response["success"] is True
    assert json_response["error"] is None
    assert json_response["data"] is not None
    return cast(dict[str, Any], json_response["data"])


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client with a clean project repository."""
    repo: ProjectRepository = _service._repository
    repo.clear()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    repo.clear()


class TestContentWorkflowNodes:
    def test_workflow_state_can_be_created(self) -> None:
        state = _base_state()

        assert state["project_id"] == "project-1"
        assert state["status"] == "initialized"
        assert state["target_platforms"] == ALL_PLATFORMS

    def test_intake_node_normalizes_valid_input(self) -> None:
        state = intake_node(_base_state())

        assert state["status"] == "normalized"
        assert state["source_title"] == "Workflow Test"
        assert state["normalized_input"]["platforms"] == ALL_PLATFORMS
        assert state["errors"] == []

    def test_intake_node_records_empty_content_error(self) -> None:
        state = intake_node(_base_state(source_content="   "))

        assert state["status"] == "failed"
        assert "source_content must not be empty" in state["errors"]

    def test_platform_strategy_node_generates_five_platform_strategies(self) -> None:
        state = platform_strategy_node(intake_node(_base_state()))

        assert state["status"] == "strategy_ready"
        assert set(state["platform_strategy"]) == set(ALL_PLATFORMS)
        assert state["platform_strategy"]["wechat"]["format"] == "long-form article"
        assert state["platform_strategy"]["douyin"]["format"] == "short video script"

    def test_preview_generation_node_uses_adapters_for_five_platforms(self) -> None:
        state = preview_generation_node(platform_strategy_node(intake_node(_base_state())))

        assert state["status"] == "previews_ready"
        assert set(state["previews"]) == set(ALL_PLATFORMS)
        assert "WeChat" in state["previews"]["wechat"]["rendered_html"]
        assert state["previews"]["zhihu"]["platform_display_name"] == "Zhihu"


class TestContentWorkflowRunner:
    def test_runner_completes_full_workflow(self) -> None:
        state = run_content_preview_workflow(
            project_id="project-1",
            source_title="Workflow Test",
            source_content=SAMPLE_CONTENT,
            target_platforms=ALL_PLATFORMS,
        )

        assert state["status"] == "completed"
        assert state["errors"] == []
        assert set(state["previews"]) == set(ALL_PLATFORMS)


class TestAgentPreviewApi:
    async def test_agent_preview_api_returns_workflow_state(
        self,
        client: AsyncClient,
    ) -> None:
        create_response = await client.post(
            "/api/projects",
            json={"title": "Workflow Test", "source_text": SAMPLE_CONTENT},
        )
        project_id = _unwrap_success(create_response)["id"]

        response = await client.post(
            f"/api/projects/{project_id}/agent-preview",
            json={"platforms": ALL_PLATFORMS},
        )

        assert response.status_code == 200
        state = _unwrap_success(response)
        assert state["status"] == "completed"
        assert set(state["previews"]) == set(ALL_PLATFORMS)
