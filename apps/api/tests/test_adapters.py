"""Tests for the platform adapter abstraction layer.

Verifies the abstract interface contract and data structures.
Does NOT test any concrete platform implementation.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from api.app.adapters.base import PlatformAdapter
from api.app.adapters.types import (
    Platform,
    PlatformContent,
    PreviewResult,
    PublishResult,
    ValidationResult,
)
from pydantic import ValidationError

# ── Platform enum ──────────────────────────────────────────────────────


class TestPlatform:
    def test_enum_values(self) -> None:
        """Platform should contain exactly the five expected platforms."""
        assert set(Platform) == {
            Platform.WECHAT,
            Platform.ZHIHU,
            Platform.BILIBILI,
            Platform.XIAOHONGSHU,
            Platform.DOUYIN,
        }

    def test_enum_string_values(self) -> None:
        """Platform enum should have expected string values."""
        assert Platform.WECHAT.value == "wechat"
        assert Platform.ZHIHU.value == "zhihu"
        assert Platform.BILIBILI.value == "bilibili"
        assert Platform.XIAOHONGSHU.value == "xiaohongshu"
        assert Platform.DOUYIN.value == "douyin"

    def test_display_name(self) -> None:
        """Each platform should have a human-readable display name."""
        assert Platform.WECHAT.display_name == "WeChat Official Accounts"
        assert Platform.ZHIHU.display_name == "Zhihu"
        assert Platform.BILIBILI.display_name == "Bilibili"
        assert Platform.XIAOHONGSHU.display_name == "Xiaohongshu (RED)"
        assert Platform.DOUYIN.display_name == "Douyin"


# ── PlatformContent ────────────────────────────────────────────────────


class TestPlatformContent:
    def test_create_minimal(self) -> None:
        """PlatformContent should be creatable with just a platform."""
        content = PlatformContent(platform=Platform.WECHAT)
        assert content.platform == Platform.WECHAT
        assert content.title == ""
        assert content.body == ""
        assert content.hooks == []
        assert content.tags == []

    def test_create_full(self) -> None:
        """PlatformContent should accept all optional fields."""
        content = PlatformContent(
            platform=Platform.ZHIHU,
            title="Test Title",
            body="Test body content",
            summary="A short summary",
            hooks=["Did you know..."],
            tags=["python", "testing"],
            cover_image_url="https://example.com/cover.jpg",
            metadata={"column_id": "123"},
        )
        assert content.platform == Platform.ZHIHU
        assert content.title == "Test Title"
        assert content.body == "Test body content"
        assert len(content.hooks) == 1
        assert len(content.tags) == 2
        assert content.cover_image_url == "https://example.com/cover.jpg"
        assert content.metadata["column_id"] == "123"

    def test_platform_required(self) -> None:
        """PlatformContent must have a platform."""
        with pytest.raises(ValidationError):
            PlatformContent.model_validate({})


# ── ValidationResult ──────────────────────────────────────────────────


class TestValidationResult:
    def test_default_valid(self) -> None:
        """ValidationResult should default to valid."""
        result = ValidationResult()
        assert result.is_valid is True
        assert result.errors == []
        assert result.warnings == []
        assert result.has_errors is False

    def test_with_errors(self) -> None:
        """ValidationResult should correctly report errors."""
        result = ValidationResult(
            is_valid=False,
            errors=["Title exceeds 64 characters", "Cover image required"],
        )
        assert result.is_valid is False
        assert result.has_errors is True
        assert len(result.errors) == 2

    def test_with_warnings_only(self) -> None:
        """ValidationResult with warnings but no errors should still be valid."""
        result = ValidationResult(warnings=["Low-quality image recommended"])
        assert result.is_valid is True
        assert result.has_errors is False
        assert len(result.warnings) == 1


# ── PreviewResult ─────────────────────────────────────────────────────


class TestPreviewResult:
    def test_create_minimal(self) -> None:
        """PreviewResult should be creatable with just a platform."""
        preview = PreviewResult(platform=Platform.BILIBILI)
        assert preview.platform == Platform.BILIBILI
        assert preview.rendered_html == ""
        assert preview.word_count == 0
        assert preview.estimated_read_time_min == 0

    def test_with_content(self) -> None:
        """PreviewResult should accept full content data."""
        preview = PreviewResult(
            platform=Platform.XIAOHONGSHU,
            rendered_html="<h1>Hello</h1>",
            word_count=1200,
            estimated_read_time_min=4,
            screenshot_url="https://example.com/preview.png",
        )
        assert preview.word_count == 1200
        assert preview.estimated_read_time_min == 4
        assert preview.screenshot_url is not None


# ── PublishResult ─────────────────────────────────────────────────────


class TestPublishResult:
    def test_default_failed(self) -> None:
        """PublishResult should default to unsuccessful."""
        result = PublishResult(platform=Platform.WECHAT)
        assert result.success is False
        assert result.is_published is False
        assert result.published_url is None

    def test_successful_publish(self) -> None:
        """PublishResult should reflect a successful publish."""
        now = datetime.now(timezone.utc)
        result = PublishResult(
            platform=Platform.WECHAT,
            success=True,
            published_url="https://mp.weixin.qq.com/s/abc123",
            published_at=now,
        )
        assert result.is_published is True
        assert result.published_url is not None
        assert result.published_at == now

    def test_with_error(self) -> None:
        """PublishResult should carry error details."""
        result = PublishResult(
            platform=Platform.ZHIHU,
            success=False,
            error_message="API rate limit exceeded",
        )
        assert result.is_published is False
        assert result.error_message == "API rate limit exceeded"


# ── PlatformAdapter abstract interface ────────────────────────────────


class TestPlatformAdapterInterface:
    def test_abstract_class_cannot_be_instantiated(self) -> None:
        """PlatformAdapter should be abstract and not instantiable."""
        with pytest.raises(TypeError, match="abstract"):
            PlatformAdapter()  # type: ignore[abstract]

    def test_concrete_subclass_must_implement_all_methods(self) -> None:
        """A subclass missing methods should fail instantiation."""

        class IncompleteAdapter(PlatformAdapter):
            pass

        with pytest.raises(TypeError, match="abstract"):
            IncompleteAdapter()  # type: ignore[abstract]

    def test_concrete_subclass_can_be_instantiated(self) -> None:
        """A subclass implementing all methods should work."""

        class MockAdapter(PlatformAdapter):
            platform = Platform.WECHAT

            @property
            def platform_name(self) -> str:
                return "Mock Platform"

            def validate_content(self, content: PlatformContent) -> ValidationResult:
                return ValidationResult()

            def transform_content(self, content: PlatformContent) -> PlatformContent:
                return content

            def build_preview(self, content: PlatformContent) -> PreviewResult:
                return PreviewResult(platform=self.platform)

            def publish(self, content: PlatformContent) -> PublishResult:
                return PublishResult(platform=self.platform)

            def mock_publish(self, content: PlatformContent) -> PublishResult:
                return PublishResult(platform=self.platform, success=True)

        adapter = MockAdapter()
        assert adapter.platform == Platform.WECHAT
        assert adapter.platform_name == "Mock Platform"

        content = PlatformContent(platform=Platform.WECHAT, body="test")

        validation = adapter.validate_content(content)
        assert validation.is_valid is True

        transformed = adapter.transform_content(content)
        assert transformed.body == "test"

        preview = adapter.build_preview(content)
        assert preview.platform == Platform.WECHAT

        result = adapter.mock_publish(content)
        assert result.success is True

    def test_all_abstract_methods_defined(self) -> None:
        """PlatformAdapter should define the expected set of abstract methods."""
        abstract_methods = {
            name
            for name, method in PlatformAdapter.__dict__.items()
            if getattr(method, "__isabstractmethod__", False)
        }
        assert abstract_methods == {
            "platform_name",
            "validate_content",
            "transform_content",
            "build_preview",
            "publish",
            "mock_publish",
        }
