"""Base protocol for optional LLM providers."""

from __future__ import annotations

from typing import Protocol

from api.app.llm.schemas import LLMGenerateRequest, LLMGenerateResponse


class LLMProvider(Protocol):
    """Provider interface for platform content generation."""

    provider_name: str
    model: str

    def generate_platform_content(
        self,
        request: LLMGenerateRequest,
    ) -> LLMGenerateResponse:
        """Generate structured platform content."""
        ...
