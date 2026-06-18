"""Pydantic schemas for content project management."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class CreateContentProjectRequest(BaseModel):
    """Request body for creating a new content project."""

    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Project title or content topic",
    )
    source_text: str = Field(
        ...,
        min_length=1,
        description="Source article body or content idea description",
    )
    source_url: str | None = Field(
        default=None,
        description="Original URL if the content comes from a web source",
    )

    @field_validator("title", "source_text")
    @classmethod
    def validate_non_blank(cls, value: str) -> str:
        """Reject strings that contain only whitespace."""
        if not value.strip():
            raise ValueError("Field must not be blank")
        return value


class ProjectPreviewItem(BaseModel):
    """Preview result for a single platform."""

    project_id: str
    platform: str
    platform_display_name: str
    title: str
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    preview: dict[str, Any] = Field(default_factory=dict)
    validation: dict[str, Any] = Field(default_factory=dict)
    rendered_html: str
    word_count: int
    estimated_read_time_min: int
    warnings: list[str] = Field(default_factory=list)


class ContentProjectResponse(BaseModel):
    """Response body for a content project."""

    id: str
    title: str
    source_text: str
    source_url: str | None
    status: str = Field(default="created")
    created_at: datetime
    previews: list[ProjectPreviewItem] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class GeneratePreviewRequest(BaseModel):
    """Request body for generating platform previews."""

    platforms: list[str] = Field(
        ...,
        min_length=1,
        description="List of target platform identifiers (e.g. ['wechat', 'zhihu'])",
    )
    title: str | None = Field(
        default=None,
        description="Optional override title for platform adaptation",
    )
    hooks: list[str] | None = Field(
        default=None,
        description="Optional opening hooks for platform adaptation",
    )
    tags: list[str] | None = Field(
        default=None,
        description="Optional tags for platform adaptation",
    )


class PlatformPreviewResponse(BaseModel):
    """Response body containing previews for requested platforms."""

    project_id: str
    project_title: str
    previews: list[ProjectPreviewItem]
    generated_at: datetime


class PublishProjectRequest(BaseModel):
    """Request body for publishing a project to target platforms."""

    target_platforms: list[str] = Field(
        ...,
        min_length=1,
        description="List of platform identifiers to publish to",
    )
    mode: str = Field(
        default="mock",
        description="Publish mode. Current MVP supports only 'mock'.",
    )


class PlatformPublishResultItem(BaseModel):
    """Publish result for a single platform."""

    platform: str
    platform_display_name: str
    status: str
    mock_url: str | None = None
    message: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class PublishProjectResponse(BaseModel):
    """Response body containing publish results for requested platforms."""

    project_id: str
    mode: str
    results: list[PlatformPublishResultItem]
    published_at: datetime


class PlatformEvaluationScore(BaseModel):
    """Rule-based evaluation scores for one platform preview."""

    platform: str
    platform_display_name: str
    format_score: int
    style_score: int
    consistency_score: int
    compliance_score: int
    completeness_score: int
    overall_score: int
    issues: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)


class EvaluationReportResponse(BaseModel):
    """Rule-based content quality evaluation report."""

    project_id: str
    average_score: int
    platform_scores: list[PlatformEvaluationScore]
    issues: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    created_at: datetime
