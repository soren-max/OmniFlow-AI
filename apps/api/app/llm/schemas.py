"""Schemas for optional LLM content generation."""

from __future__ import annotations

from pydantic import BaseModel, Field


class LLMGenerateRequest(BaseModel):
    """Provider-agnostic request for platform content generation."""

    title: str
    source_text: str
    target_platforms: list[str] = Field(min_length=1)
    tone: str = Field(default="professional")
    requirements: str = Field(default="")


class LLMPlatformOutput(BaseModel):
    """Structured content generated for one platform."""

    platform: str
    title: str
    body: str
    hashtags: list[str] = Field(default_factory=list)
    summary: str = ""
    cta: str = ""
    notes: str = ""


class LLMGenerateResponse(BaseModel):
    """Provider-agnostic response for platform content generation."""

    platform_outputs: list[LLMPlatformOutput]
    provider: str
    model: str
    usage: dict[str, int] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


class LLMProjectGenerateRequest(BaseModel):
    """API request for optional LLM generation on an existing project."""

    platforms: list[str] = Field(min_length=1)
    tone: str = Field(default="professional")
    requirements: str = Field(default="")


class LLMProjectGenerateResponse(BaseModel):
    """API response for optional LLM generation on an existing project."""

    project_id: str
    run_id: str
    provider: str
    model: str
    platform_outputs: list[LLMPlatformOutput]
    usage: dict[str, int] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
