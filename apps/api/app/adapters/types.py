"""Data types for the platform adapter layer.

Defines shared schemas used across all platform adapters.
These types are protocol-agnostic — no platform-specific logic here.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class Platform(StrEnum):
    """Supported content platforms."""

    WECHAT = "wechat"
    ZHIHU = "zhihu"
    BILIBILI = "bilibili"
    XIAOHONGSHU = "xiaohongshu"
    DOUYIN = "douyin"

    @property
    def display_name(self) -> str:
        """Return a human-readable platform name."""
        names = {
            Platform.WECHAT: "WeChat Official Accounts",
            Platform.ZHIHU: "Zhihu",
            Platform.BILIBILI: "Bilibili",
            Platform.XIAOHONGSHU: "Xiaohongshu (RED)",
            Platform.DOUYIN: "Douyin",
        }
        return names[self]


class PlatformContent(BaseModel):
    """Content that has been adapted for a specific platform."""

    platform: Platform
    title: str = Field(default="", description="Platform-adapted title")
    body: str = Field(default="", description="Platform-adapted body content")
    summary: str = Field(default="", description="Short summary or excerpt")
    hooks: list[str] = Field(default_factory=list, description="Opening hooks")
    tags: list[str] = Field(default_factory=list, description="Platform tags")
    cover_image_url: str | None = Field(default=None, description="Cover image URL")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Platform-specific metadata (e.g. video ID, column ID)",
    )


class ValidationResult(BaseModel):
    """Result of validating content against platform rules."""

    is_valid: bool = Field(default=True, description="Whether content passes validation")
    errors: list[str] = Field(
        default_factory=list,
        description="Validation error messages",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Non-blocking warnings",
    )

    @property
    def has_errors(self) -> bool:
        """Convenience: true if there are blocking errors."""
        return len(self.errors) > 0


class PreviewResult(BaseModel):
    """Platform-specific preview data."""

    platform: Platform
    rendered_html: str = Field(default="", description="Rendered HTML preview")
    word_count: int = Field(default=0, description="Word count of adapted content")
    estimated_read_time_min: int = Field(
        default=0,
        description="Estimated reading time in minutes",
    )
    screenshot_url: str | None = Field(default=None, description="Preview screenshot URL")
    metadata: dict[str, Any] = Field(default_factory=dict)


class PublishResult(BaseModel):
    """Result of a publish or mock-publish operation."""

    platform: Platform
    success: bool = Field(default=False, description="Whether publish succeeded")
    published_url: str | None = Field(default=None, description="URL of published content")
    published_at: datetime | None = Field(default=None, description="Publish timestamp")
    error_message: str | None = Field(default=None, description="Error if publish failed")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Platform-specific response metadata",
    )

    @property
    def is_published(self) -> bool:
        """Convenience: true if content was successfully published."""
        return self.success and self.published_url is not None
