"""Tests for optional LLM provider integration."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any, cast

import pytest
from api.app.llm import (
    LLMGenerateRequest,
    LLMProviderConfigurationError,
    build_llm_provider,
)
from api.app.llm.deepseek_provider import DeepSeekProvider
from api.app.llm.mock_provider import MockLLMProvider
from api.app.main import app
from api.app.repositories.project_repository import ProjectRepository
from api.app.telemetry.service import trace_service
from httpx import ASGITransport, AsyncClient, Response

SAMPLE_TEXT = (
    "Optional LLM provider test content with enough detail for platform-specific "
    "generation. It should run through the mock provider without external API keys."
)
ALL_PLATFORMS = ["wechat", "zhihu", "bilibili", "xiaohongshu", "douyin"]


def _unwrap_success(response: Response) -> dict[str, Any]:
    json_response = cast(dict[str, Any], response.json())
    assert json_response["success"] is True
    assert json_response["error"] is None
    assert json_response["data"] is not None
    return cast(dict[str, Any], json_response["data"])


def _assert_error(response: Response, code: str) -> dict[str, Any]:
    json_response = cast(dict[str, Any], response.json())
    assert json_response["success"] is False
    assert json_response["data"] is None
    assert json_response["error"]["code"] == code
    return cast(dict[str, Any], json_response["error"])


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client."""
    from api.app.api import projects

    repo: ProjectRepository = projects._service._repository
    repo.clear()
    trace_service.clear()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    repo.clear()
    trace_service.clear()


def test_mock_provider_runs_without_api_key() -> None:
    provider = MockLLMProvider()

    response = provider.generate_platform_content(
        LLMGenerateRequest(
            title="Mock Title",
            source_text=SAMPLE_TEXT,
            target_platforms=["wechat", "douyin"],
            tone="professional",
            requirements="personal content ops",
        )
    )

    assert response.provider == "mock"
    assert len(response.platform_outputs) == 2
    assert response.platform_outputs[0].platform == "wechat"
    assert response.usage == {}


def test_provider_factory_selects_mock_by_default() -> None:
    provider = build_llm_provider(
        provider_name="mock",
        api_key="",
        base_url="https://api.deepseek.com",
        model="deepseek-v4-flash",
        timeout_seconds=30,
    )

    assert isinstance(provider, MockLLMProvider)


def test_provider_factory_selects_deepseek_when_configured() -> None:
    provider = build_llm_provider(
        provider_name="deepseek",
        api_key="test-key",
        base_url="https://api.deepseek.com",
        model="deepseek-v4-flash",
        timeout_seconds=30,
    )

    assert isinstance(provider, DeepSeekProvider)


def test_deepseek_provider_requires_api_key() -> None:
    with pytest.raises(LLMProviderConfigurationError, match="LLM_API_KEY"):
        build_llm_provider(
            provider_name="deepseek",
            api_key="",
            base_url="https://api.deepseek.com",
            model="deepseek-v4-flash",
            timeout_seconds=30,
        )


async def test_llm_generate_api_contract_uses_mock_without_key(client: AsyncClient) -> None:
    create_response = await client.post(
        "/api/projects",
        json={"title": "LLM API", "source_text": SAMPLE_TEXT},
    )
    project_id = _unwrap_success(create_response)["id"]

    response = await client.post(
        f"/api/projects/{project_id}/llm-generate",
        json={
            "platforms": ALL_PLATFORMS,
            "tone": "professional",
            "requirements": "适合个人内容运营发布",
        },
    )

    assert response.status_code == 200
    data = _unwrap_success(response)
    assert data["project_id"] == project_id
    assert data["run_id"]
    assert data["provider"] == "mock"
    assert len(data["platform_outputs"]) == 5
    assert {item["platform"] for item in data["platform_outputs"]} == set(ALL_PLATFORMS)


async def test_deepseek_missing_key_returns_clear_api_error(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from api.app.core.config import settings

    monkeypatch.setattr(settings, "llm_provider", "deepseek")
    monkeypatch.setattr(settings, "llm_api_key", "")

    create_response = await client.post(
        "/api/projects",
        json={"title": "DeepSeek Missing Key", "source_text": SAMPLE_TEXT},
    )
    project_id = _unwrap_success(create_response)["id"]

    response = await client.post(
        f"/api/projects/{project_id}/llm-generate",
        json={"platforms": ["wechat"], "tone": "professional", "requirements": ""},
    )

    assert response.status_code == 400
    error = _assert_error(response, "LLM_PROVIDER_NOT_CONFIGURED")
    assert "LLM_API_KEY" in error["message"]


async def test_llm_generate_does_not_expose_api_key_in_response_or_trace(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from api.app.core.config import settings

    secret = "placeholder-test-value"
    monkeypatch.setattr(settings, "llm_provider", "mock")
    monkeypatch.setattr(settings, "llm_api_key", secret)

    create_response = await client.post(
        "/api/projects",
        json={"title": "No Secret Leak", "source_text": SAMPLE_TEXT},
    )
    project_id = _unwrap_success(create_response)["id"]

    response = await client.post(
        f"/api/projects/{project_id}/llm-generate",
        json={"platforms": ["wechat"], "tone": "professional", "requirements": "safe"},
    )
    data = _unwrap_success(response)
    serialized_response = response.text
    assert secret not in serialized_response

    steps_response = await client.get(f"/api/runs/{data['run_id']}/steps")
    serialized_steps = steps_response.text
    assert secret not in serialized_steps
    steps = cast(list[dict[str, Any]], steps_response.json()["data"])
    assert steps[0]["node_name"] == "llm_generation"
    assert steps[0]["output_snapshot"]["provider"] == "mock"
