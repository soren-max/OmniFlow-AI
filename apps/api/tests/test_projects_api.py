"""Tests for the content project API endpoints."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any, cast

import pytest
from api.app.adapters.types import PlatformContent
from api.app.adapters.wechat_adapter import WeChatAdapter
from api.app.main import app
from api.app.repositories.project_repository import (
    ProjectRepository,
)
from httpx import ASGITransport, AsyncClient, Response

SAMPLE_TEXT = (
    "This is a sample article for testing the content project API. "
    "It contains enough text to pass all platform validation rules. "
    "We want to ensure that the API correctly creates projects and "
    "generates previews for multiple platforms.\n\n"
    "# Introduction\n\n"
    "This is the introduction section with some meaningful content "
    "that describes the topic at hand.\n\n"
    "## Analysis\n\n"
    "Here we dive deeper into the analysis with specific points.\n\n"
    "## Conclusion\n\n"
    "Final thoughts and summary of everything discussed."
)


def _unwrap_success(response: Response) -> dict[str, Any]:
    """Assert and unwrap the standard success envelope."""
    json_response = cast(dict[str, Any], response.json())
    assert json_response["success"] is True
    assert json_response["error"] is None
    assert json_response["data"] is not None
    return cast(dict[str, Any], json_response["data"])


def _assert_error(response: Response, code: str) -> dict[str, Any]:
    """Assert and return the standard error payload."""
    json_response = cast(dict[str, Any], response.json())
    assert json_response["success"] is False
    assert json_response["data"] is None
    assert json_response["error"]["code"] == code
    assert json_response["error"]["message"]
    return cast(dict[str, Any], json_response["error"])


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture(autouse=True)
def _clean_repo() -> None:
    """Clear the in-memory project repository before each test.

    Since the API uses a singleton service, we need to clear the
    underlying repository between tests to avoid state leakage.
    """
    from api.app.api.projects import _service

    repo: ProjectRepository = _service._repository
    repo.clear()


# ── Create Project ────────────────────────────────────────────────────────────


class TestCreateProject:
    async def test_create_project_minimal(self, client: AsyncClient) -> None:
        """Creating a project with just title and source_text should succeed."""
        response = await client.post(
            "/api/projects",
            json={
                "title": "Test Project",
                "source_text": SAMPLE_TEXT,
            },
        )
        assert response.status_code == 201
        data = _unwrap_success(response)
        assert data["title"] == "Test Project"
        assert data["source_text"] == SAMPLE_TEXT
        assert data["status"] == "created"
        assert "id" in data
        assert data["previews"] == []

    async def test_create_project_with_url(self, client: AsyncClient) -> None:
        """Optional source_url should be stored."""
        response = await client.post(
            "/api/projects",
            json={
                "title": "Project with URL",
                "source_text": SAMPLE_TEXT,
                "source_url": "https://example.com/article",
            },
        )
        assert response.status_code == 201
        data = _unwrap_success(response)
        assert data["source_url"] == "https://example.com/article"

    async def test_create_project_missing_title(self, client: AsyncClient) -> None:
        """Missing required title should return 422."""
        response = await client.post(
            "/api/projects",
            json={"source_text": SAMPLE_TEXT},
        )
        assert response.status_code == 422
        _assert_error(response, "VALIDATION_ERROR")

    async def test_create_project_empty_source(self, client: AsyncClient) -> None:
        """Empty source_text should return 422."""
        response = await client.post(
            "/api/projects",
            json={"title": "Test", "source_text": ""},
        )
        assert response.status_code == 422
        _assert_error(response, "VALIDATION_ERROR")

    async def test_create_project_blank_source(self, client: AsyncClient) -> None:
        """Blank source_text should return a structured validation error."""
        response = await client.post(
            "/api/projects",
            json={"title": "Test", "source_text": "   "},
        )
        assert response.status_code == 422
        error = _assert_error(response, "VALIDATION_ERROR")
        assert error["details"] is not None


# ── Get Project ───────────────────────────────────────────────────────────────


class TestGetProject:
    async def test_get_existing_project(self, client: AsyncClient) -> None:
        """Getting a project that exists should return it."""
        # Create first
        create_resp = await client.post(
            "/api/projects",
            json={"title": "My Project", "source_text": SAMPLE_TEXT},
        )
        project_id = _unwrap_success(create_resp)["id"]

        # Get
        response = await client.get(f"/api/projects/{project_id}")
        assert response.status_code == 200
        data = _unwrap_success(response)
        assert data["id"] == project_id
        assert data["title"] == "My Project"

    async def test_get_nonexistent_project(self, client: AsyncClient) -> None:
        """Getting a project that does not exist should return 404."""
        response = await client.get("/api/projects/nonexistent-id")
        assert response.status_code == 404
        error = _assert_error(response, "PROJECT_NOT_FOUND")
        assert "not found" in str(error["message"]).lower()


# ── Generate Preview ──────────────────────────────────────────────────────────


class TestGeneratePreview:
    async def _create_project(self, client: AsyncClient) -> str:
        """Helper: create a project and return its id."""
        resp = await client.post(
            "/api/projects",
            json={"title": "Preview Test", "source_text": SAMPLE_TEXT},
        )
        return str(_unwrap_success(resp)["id"])

    async def test_generate_single_platform_preview(
        self,
        client: AsyncClient,
    ) -> None:
        """Generate preview for a single valid platform."""
        project_id = await self._create_project(client)
        response = await client.post(
            f"/api/projects/{project_id}/preview",
            json={"platforms": ["wechat"]},
        )
        assert response.status_code == 200
        data = _unwrap_success(response)
        assert data["project_id"] == project_id
        assert data["project_title"] == "Preview Test"
        assert len(data["previews"]) == 1
        preview = data["previews"][0]
        assert preview["project_id"] == project_id
        assert preview["platform"] == "wechat"
        assert preview["platform_display_name"] == "WeChat Official Accounts"
        assert preview["title"]
        assert preview["content"]
        assert isinstance(preview["metadata"], dict)
        assert isinstance(preview["preview"], dict)
        assert isinstance(preview["validation"], dict)
        assert preview["preview"]["rendered_html"] == preview["rendered_html"]
        assert preview["validation"]["warnings"] == preview["warnings"]
        assert len(preview["rendered_html"]) > 0
        assert preview["word_count"] > 0
        assert preview["estimated_read_time_min"] >= 1

    async def test_generate_multi_platform_preview(
        self,
        client: AsyncClient,
    ) -> None:
        """Generate previews for all 5 platforms at once."""
        project_id = await self._create_project(client)
        response = await client.post(
            f"/api/projects/{project_id}/preview",
            json={
                "platforms": ["wechat", "zhihu", "bilibili", "xiaohongshu", "douyin"],
            },
        )
        assert response.status_code == 200
        data = _unwrap_success(response)
        assert len(data["previews"]) == 5
        platforms = {p["platform"] for p in data["previews"]}
        assert platforms == {"wechat", "zhihu", "bilibili", "xiaohongshu", "douyin"}

    async def test_generate_preview_supports_douyin(
        self,
        client: AsyncClient,
    ) -> None:
        """Generate preview for Douyin."""
        project_id = await self._create_project(client)
        response = await client.post(
            f"/api/projects/{project_id}/preview",
            json={
                "platforms": ["douyin"],
                "hooks": ["3秒看懂内容运营怎么提效"],
                "tags": ["AI工具", "内容运营", "效率提升"],
            },
        )
        assert response.status_code == 200
        data = _unwrap_success(response)
        assert len(data["previews"]) == 1
        preview = data["previews"][0]
        assert preview["platform"] == "douyin"
        assert preview["platform_display_name"] == "Douyin"
        assert preview["metadata"]["shot_list"]
        assert preview["metadata"]["call_to_action"]
        assert "Douyin Short Video Preview" in preview["rendered_html"]

    async def test_generate_preview_with_overrides(
        self,
        client: AsyncClient,
    ) -> None:
        """Generate preview with custom title, hooks, and tags."""
        project_id = await self._create_project(client)
        response = await client.post(
            f"/api/projects/{project_id}/preview",
            json={
                "platforms": ["zhihu"],
                "title": "Custom Title for Testing",
                "hooks": ["Did you know this?"],
                "tags": ["test", "api", "python"],
            },
        )
        assert response.status_code == 200
        data = _unwrap_success(response)
        assert len(data["previews"]) == 1
        # The transformed content should use the custom title
        assert "Custom Title" in data["previews"][0]["rendered_html"]

    async def test_generate_preview_nonexistent_project(
        self,
        client: AsyncClient,
    ) -> None:
        """Preview for a nonexistent project should return 404."""
        response = await client.post(
            "/api/projects/bad-id/preview",
            json={"platforms": ["wechat"]},
        )
        assert response.status_code == 404
        _assert_error(response, "PROJECT_NOT_FOUND")

    async def test_generate_preview_invalid_platform(
        self,
        client: AsyncClient,
    ) -> None:
        """Preview with an unsupported platform should return 400."""
        project_id = await self._create_project(client)
        response = await client.post(
            f"/api/projects/{project_id}/preview",
            json={"platforms": ["unknown_platform"]},
        )
        assert response.status_code == 400
        error = _assert_error(response, "INVALID_PLATFORM")
        assert "unknown" in str(error["message"]).lower()

    async def test_generate_preview_empty_platforms(
        self,
        client: AsyncClient,
    ) -> None:
        """Empty platforms list should return 422."""
        project_id = await self._create_project(client)
        response = await client.post(
            f"/api/projects/{project_id}/preview",
            json={"platforms": []},
        )
        assert response.status_code == 422
        _assert_error(response, "VALIDATION_ERROR")

    async def test_generate_preview_adapter_failure(
        self,
        client: AsyncClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Adapter failures should return a structured 500 error."""

        def failing_transform_content(
            _self: WeChatAdapter,
            _content: PlatformContent,
        ) -> PlatformContent:
            raise RuntimeError("preview pipeline exploded")

        project_id = await self._create_project(client)
        monkeypatch.setattr(WeChatAdapter, "transform_content", failing_transform_content)
        response = await client.post(
            f"/api/projects/{project_id}/preview",
            json={"platforms": ["wechat"]},
        )

        assert response.status_code == 500
        error = _assert_error(response, "ADAPTER_EXECUTION_FAILED")
        assert error["details"]["platform"] == "wechat"


# ── Publish Drafts ────────────────────────────────────────────────────────────


class TestPublishDrafts:
    async def _create_project(self, client: AsyncClient) -> str:
        response = await client.post(
            "/api/projects",
            json={"title": "Draft Project", "source_text": SAMPLE_TEXT},
        )
        return str(_unwrap_success(response)["id"])

    async def _create_draft(self, client: AsyncClient, project_id: str) -> dict[str, Any]:
        response = await client.post(
            f"/api/projects/{project_id}/drafts",
            json={
                "platform": "xiaohongshu",
                "title": "Draft title",
                "body": "Draft body for manual publishing.",
                "hashtags": ["AI", "内容运营"],
                "summary": "Short summary",
                "cta": "Follow for more",
                "notes": "Check images before manual submit.",
            },
        )
        assert response.status_code == 201
        return _unwrap_success(response)

    async def test_create_publish_draft_success(self, client: AsyncClient) -> None:
        project_id = await self._create_project(client)

        draft = await self._create_draft(client, project_id)

        assert draft["project_id"] == project_id
        assert draft["platform"] == "xiaohongshu"
        assert draft["title"] == "Draft title"
        assert draft["body"] == "Draft body for manual publishing."
        assert draft["hashtags"] == ["AI", "内容运营"]
        assert draft["status"] == "draft"
        assert draft["draft_id"]

    async def test_list_project_publish_drafts_success(self, client: AsyncClient) -> None:
        project_id = await self._create_project(client)
        draft = await self._create_draft(client, project_id)

        response = await client.get(f"/api/projects/{project_id}/drafts")

        assert response.status_code == 200
        drafts = cast(list[dict[str, Any]], _unwrap_success(response))
        assert len(drafts) == 1
        assert drafts[0]["draft_id"] == draft["draft_id"]

    async def test_update_publish_draft_success(self, client: AsyncClient) -> None:
        project_id = await self._create_project(client)
        draft = await self._create_draft(client, project_id)

        response = await client.patch(
            f"/api/drafts/{draft['draft_id']}",
            json={
                "title": "Edited title",
                "body": "Edited body.",
                "hashtags": ["edited"],
                "notes": "Ready for manual copy.",
                "status": "reviewed",
            },
        )

        assert response.status_code == 200
        updated = _unwrap_success(response)
        assert updated["title"] == "Edited title"
        assert updated["body"] == "Edited body."
        assert updated["hashtags"] == ["edited"]
        assert updated["notes"] == "Ready for manual copy."
        assert updated["status"] == "reviewed"

    async def test_create_publish_draft_nonexistent_project(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/projects/missing-project/drafts",
            json={
                "platform": "wechat",
                "title": "Draft title",
                "body": "Draft body",
            },
        )

        assert response.status_code == 404
        _assert_error(response, "PROJECT_NOT_FOUND")

    async def test_update_nonexistent_publish_draft(self, client: AsyncClient) -> None:
        response = await client.patch(
            "/api/drafts/missing-draft",
            json={"title": "Edited title"},
        )

        assert response.status_code == 404
        _assert_error(response, "DRAFT_NOT_FOUND")

    async def test_create_publish_draft_unsupported_platform(
        self,
        client: AsyncClient,
    ) -> None:
        project_id = await self._create_project(client)

        response = await client.post(
            f"/api/projects/{project_id}/drafts",
            json={
                "platform": "threads",
                "title": "Draft title",
                "body": "Draft body",
            },
        )

        assert response.status_code == 400
        _assert_error(response, "INVALID_PLATFORM")


# ── Mock Publish ──────────────────────────────────────────────────────────────


class TestMockPublish:
    async def _create_project_with_previews(self, client: AsyncClient) -> str:
        """Create a project, generate previews, and return the project id."""
        create_resp = await client.post(
            "/api/projects",
            json={"title": "Publish Test", "source_text": SAMPLE_TEXT},
        )
        project_id = str(_unwrap_success(create_resp)["id"])
        preview_resp = await client.post(
            f"/api/projects/{project_id}/preview",
            json={
                "platforms": ["wechat", "zhihu", "bilibili", "xiaohongshu", "douyin"],
                "tags": ["AI工具", "内容运营", "效率提升"],
            },
        )
        assert preview_resp.status_code == 200
        return project_id

    async def _approve_project(self, client: AsyncClient, project_id: str) -> None:
        """Approve a project for mock publish."""
        response = await client.post(f"/api/projects/{project_id}/review/approve")
        assert response.status_code == 200
        assert _unwrap_success(response)["status"] == "approved"

    async def test_mock_publish_single_platform_success(self, client: AsyncClient) -> None:
        """Mock publish should succeed for one platform."""
        project_id = await self._create_project_with_previews(client)
        await self._approve_project(client, project_id)
        response = await client.post(
            f"/api/projects/{project_id}/publish",
            json={"target_platforms": ["douyin"], "mode": "mock"},
        )

        assert response.status_code == 200
        data = _unwrap_success(response)
        assert data["project_id"] == project_id
        assert data["mode"] == "mock"
        assert len(data["results"]) == 1
        result = data["results"][0]
        assert result["platform"] == "douyin"
        assert result["status"] == "success"
        assert str(result["mock_url"]).startswith("mock://douyin/post/")
        assert result["message"] == "Mock published to Douyin successfully."

    async def test_mock_publish_all_platforms_success(self, client: AsyncClient) -> None:
        """Mock publish should succeed for all five platforms."""
        project_id = await self._create_project_with_previews(client)
        await self._approve_project(client, project_id)
        response = await client.post(
            f"/api/projects/{project_id}/publish",
            json={
                "target_platforms": ["wechat", "zhihu", "bilibili", "xiaohongshu", "douyin"],
                "mode": "mock",
            },
        )

        assert response.status_code == 200
        data = _unwrap_success(response)
        assert len(data["results"]) == 5
        platforms = {result["platform"] for result in data["results"]}
        assert platforms == {"wechat", "zhihu", "bilibili", "xiaohongshu", "douyin"}
        assert all(result["status"] == "success" for result in data["results"])

    async def test_mock_publish_invalid_platform(self, client: AsyncClient) -> None:
        """Invalid publish platforms should return a structured error."""
        project_id = await self._create_project_with_previews(client)
        await self._approve_project(client, project_id)
        response = await client.post(
            f"/api/projects/{project_id}/publish",
            json={"target_platforms": ["unknown_platform"], "mode": "mock"},
        )

        assert response.status_code == 400
        _assert_error(response, "INVALID_PLATFORM")

    async def test_mock_publish_empty_platforms(self, client: AsyncClient) -> None:
        """Empty target_platforms should fail validation."""
        project_id = await self._create_project_with_previews(client)
        await self._approve_project(client, project_id)
        response = await client.post(
            f"/api/projects/{project_id}/publish",
            json={"target_platforms": [], "mode": "mock"},
        )

        assert response.status_code == 422
        _assert_error(response, "VALIDATION_ERROR")

    async def test_real_publish_not_supported(self, client: AsyncClient) -> None:
        """Real publish mode should be explicitly blocked."""
        project_id = await self._create_project_with_previews(client)
        await self._approve_project(client, project_id)
        response = await client.post(
            f"/api/projects/{project_id}/publish",
            json={"target_platforms": ["wechat"], "mode": "real"},
        )

        assert response.status_code == 400
        error = _assert_error(response, "REAL_PUBLISH_NOT_SUPPORTED")
        assert error["message"] == "Real publishing is not supported in the current MVP."

    async def test_mock_publish_nonexistent_project(self, client: AsyncClient) -> None:
        """Publishing a missing project should return PROJECT_NOT_FOUND."""
        response = await client.post(
            "/api/projects/bad-id/publish",
            json={"target_platforms": ["wechat"], "mode": "mock"},
        )

        assert response.status_code == 404
        _assert_error(response, "PROJECT_NOT_FOUND")

    async def test_preview_moves_project_to_pending_review(self, client: AsyncClient) -> None:
        """Generated previews should require human review before publish."""
        project_id = await self._create_project_with_previews(client)

        response = await client.get(f"/api/projects/{project_id}")

        assert response.status_code == 200
        assert _unwrap_success(response)["status"] == "pending"

    async def test_approve_project_enables_mock_publish(self, client: AsyncClient) -> None:
        """Approved projects should pass the publish gate."""
        project_id = await self._create_project_with_previews(client)

        approval_response = await client.post(f"/api/projects/{project_id}/review/approve")
        publish_response = await client.post(
            f"/api/projects/{project_id}/publish",
            json={"target_platforms": ["wechat"], "mode": "mock"},
        )

        assert approval_response.status_code == 200
        assert _unwrap_success(approval_response)["status"] == "approved"
        assert publish_response.status_code == 200
        assert _unwrap_success(publish_response)["results"][0]["status"] == "success"

    async def test_reject_project_blocks_mock_publish(self, client: AsyncClient) -> None:
        """Rejected projects should not be publishable."""
        project_id = await self._create_project_with_previews(client)

        reject_response = await client.post(f"/api/projects/{project_id}/review/reject")
        publish_response = await client.post(
            f"/api/projects/{project_id}/publish",
            json={"target_platforms": ["wechat"], "mode": "mock"},
        )

        assert reject_response.status_code == 200
        assert _unwrap_success(reject_response)["status"] == "rejected"
        assert publish_response.status_code == 409
        error = _assert_error(publish_response, "PROJECT_REVIEW_REQUIRED")
        assert error["details"]["status"] == "rejected"

    async def test_pending_project_cannot_mock_publish(self, client: AsyncClient) -> None:
        """Pending review projects should not publish until approved."""
        project_id = await self._create_project_with_previews(client)

        response = await client.post(
            f"/api/projects/{project_id}/publish",
            json={"target_platforms": ["wechat"], "mode": "mock"},
        )

        assert response.status_code == 409
        error = _assert_error(response, "PROJECT_REVIEW_REQUIRED")
        assert error["details"]["status"] == "pending"

    async def test_approve_nonexistent_project_returns_404(self, client: AsyncClient) -> None:
        """Approving a missing project should return PROJECT_NOT_FOUND."""
        response = await client.post("/api/projects/bad-id/review/approve")

        assert response.status_code == 404
        _assert_error(response, "PROJECT_NOT_FOUND")


# ── Evaluation ────────────────────────────────────────────────────────────────


class TestEvaluation:
    async def _create_project_with_previews(self, client: AsyncClient) -> str:
        """Create a project with all five platform previews."""
        create_resp = await client.post(
            "/api/projects",
            json={"title": "Evaluation Test", "source_text": SAMPLE_TEXT},
        )
        project_id = str(_unwrap_success(create_resp)["id"])
        preview_resp = await client.post(
            f"/api/projects/{project_id}/preview",
            json={
                "platforms": ["wechat", "zhihu", "bilibili", "xiaohongshu", "douyin"],
                "hooks": ["A practical hook"],
                "tags": ["AI", "content", "workflow"],
            },
        )
        assert preview_resp.status_code == 200
        return project_id

    async def test_create_evaluation_for_five_platforms(
        self,
        client: AsyncClient,
    ) -> None:
        """POST /evaluation should create rule-based platform scores."""
        project_id = await self._create_project_with_previews(client)

        response = await client.post(f"/api/projects/{project_id}/evaluation")

        assert response.status_code == 200
        data = _unwrap_success(response)
        assert data["project_id"] == project_id
        assert 0 <= data["average_score"] <= 100
        assert len(data["platform_scores"]) == 5
        platforms = {score["platform"] for score in data["platform_scores"]}
        assert platforms == {"wechat", "zhihu", "bilibili", "xiaohongshu", "douyin"}
        for score in data["platform_scores"]:
            assert 0 <= score["format_score"] <= 100
            assert 0 <= score["style_score"] <= 100
            assert 0 <= score["consistency_score"] <= 100
            assert 0 <= score["compliance_score"] <= 100
            assert 0 <= score["completeness_score"] <= 100
            assert 0 <= score["overall_score"] <= 100
            assert isinstance(score["issues"], list)
            assert isinstance(score["suggestions"], list)
        assert isinstance(data["issues"], list)
        assert isinstance(data["suggestions"], list)

    async def test_get_latest_evaluation(
        self,
        client: AsyncClient,
    ) -> None:
        """GET /evaluation should return the latest saved report."""
        project_id = await self._create_project_with_previews(client)
        create_response = await client.post(f"/api/projects/{project_id}/evaluation")
        created = _unwrap_success(create_response)

        response = await client.get(f"/api/projects/{project_id}/evaluation")

        assert response.status_code == 200
        data = _unwrap_success(response)
        assert data["project_id"] == project_id
        assert data["average_score"] == created["average_score"]
        assert len(data["platform_scores"]) == 5

    async def test_evaluation_requires_preview(self, client: AsyncClient) -> None:
        """Evaluation should require generated previews."""
        create_resp = await client.post(
            "/api/projects",
            json={"title": "No Preview", "source_text": SAMPLE_TEXT},
        )
        project_id = str(_unwrap_success(create_resp)["id"])

        response = await client.post(f"/api/projects/{project_id}/evaluation")

        assert response.status_code == 409
        _assert_error(response, "EVALUATION_REQUIRES_PREVIEW")

    async def test_get_missing_evaluation_returns_404(self, client: AsyncClient) -> None:
        """GET /evaluation should return 404 before a report is created."""
        project_id = await self._create_project_with_previews(client)

        response = await client.get(f"/api/projects/{project_id}/evaluation")

        assert response.status_code == 404
        _assert_error(response, "EVALUATION_NOT_FOUND")

    async def test_evaluation_for_missing_project_returns_404(
        self,
        client: AsyncClient,
    ) -> None:
        """Evaluation requests for missing projects should return PROJECT_NOT_FOUND."""
        post_response = await client.post("/api/projects/bad-id/evaluation")
        get_response = await client.get("/api/projects/bad-id/evaluation")

        assert post_response.status_code == 404
        assert get_response.status_code == 404
        _assert_error(post_response, "PROJECT_NOT_FOUND")
        _assert_error(get_response, "PROJECT_NOT_FOUND")


# ── Publish Package Export ───────────────────────────────────────────────────


class TestPublishPackageExport:
    async def _create_project_with_previews(self, client: AsyncClient) -> str:
        """Create a project with generated previews."""
        create_resp = await client.post(
            "/api/projects",
            json={"title": "Export Test", "source_text": SAMPLE_TEXT},
        )
        project_id = str(_unwrap_success(create_resp)["id"])
        preview_resp = await client.post(
            f"/api/projects/{project_id}/preview",
            json={
                "platforms": ["wechat", "zhihu"],
                "hooks": ["Manual publish hook"],
                "tags": ["AI", "export"],
            },
        )
        assert preview_resp.status_code == 200
        return project_id

    async def test_export_json_success(self, client: AsyncClient) -> None:
        """Publish package JSON should include platform content and evaluation summary."""
        project_id = await self._create_project_with_previews(client)
        await client.post(f"/api/projects/{project_id}/evaluation")

        response = await client.get(f"/api/projects/{project_id}/export/json")

        assert response.status_code == 200
        data = _unwrap_success(response)
        assert data["project_id"] == project_id
        assert data["title"] == "Export Test"
        assert data["review_status"] == "pending"
        assert data["package_status"] == "draft"
        assert data["platforms"] == ["wechat", "zhihu"]
        assert len(data["platform_contents"]) == 2
        assert data["platform_contents"][0]["copy_text"]
        assert data["evaluation_summary"]["average_score"] is not None

    async def test_export_markdown_success(self, client: AsyncClient) -> None:
        """Publish package Markdown should render manual publishing sections."""
        project_id = await self._create_project_with_previews(client)

        response = await client.get(f"/api/projects/{project_id}/export/markdown")

        assert response.status_code == 200
        assert "text/markdown" in response.headers["content-type"]
        assert "# 发布包: Export Test" in response.text
        assert "## wechat" in response.text
        assert "### 标题" in response.text
        assert "Evaluation not generated yet." in response.text

    async def test_export_missing_project_returns_404(self, client: AsyncClient) -> None:
        """Exporting a missing project should return PROJECT_NOT_FOUND."""
        response = await client.get("/api/projects/bad-id/export/json")

        assert response.status_code == 404
        _assert_error(response, "PROJECT_NOT_FOUND")

    async def test_export_requires_preview(self, client: AsyncClient) -> None:
        """Exporting before preview generation should return a clear error."""
        create_resp = await client.post(
            "/api/projects",
            json={"title": "No Preview Export", "source_text": SAMPLE_TEXT},
        )
        project_id = str(_unwrap_success(create_resp)["id"])

        response = await client.get(f"/api/projects/{project_id}/export/json")

        assert response.status_code == 409
        _assert_error(response, "EXPORT_REQUIRES_PREVIEW")
