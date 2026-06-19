"""Service and factory for optional LLM generation."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from api.app.core.config import settings
from api.app.llm.base import LLMProvider
from api.app.llm.deepseek_provider import DeepSeekProvider, DeepSeekProviderError
from api.app.llm.mock_provider import MockLLMProvider
from api.app.llm.schemas import (
    LLMGenerateRequest,
    LLMProjectGenerateResponse,
)
from api.app.telemetry.service import TraceService, trace_service


class LLMProviderConfigurationError(ValueError):
    """Raised when the selected provider is not configured."""


class LLMProviderError(RuntimeError):
    """Raised when provider execution fails."""


ProviderFactory = Callable[[], LLMProvider]


def build_llm_provider(
    *,
    provider_name: str,
    api_key: str,
    base_url: str,
    model: str,
    timeout_seconds: float,
) -> LLMProvider:
    """Build the configured LLM provider without requiring secrets at startup."""
    normalized_provider = provider_name.strip().lower() or "mock"

    if normalized_provider == "mock":
        return MockLLMProvider()

    if normalized_provider == "deepseek":
        if not api_key.strip():
            raise LLMProviderConfigurationError(
                "LLM_PROVIDER=deepseek requires LLM_API_KEY to be configured."
            )
        return DeepSeekProvider(
            api_key=api_key,
            base_url=base_url,
            model=model,
            timeout_seconds=timeout_seconds,
        )

    raise LLMProviderConfigurationError(f"Unsupported LLM_PROVIDER: {provider_name!r}")


def build_configured_provider() -> LLMProvider:
    """Build a provider from application settings."""
    return build_llm_provider(
        provider_name=settings.llm_provider,
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        model=settings.llm_model,
        timeout_seconds=settings.llm_timeout_seconds,
    )


class LLMService:
    """Coordinate optional LLM generation and safe trace recording."""

    def __init__(
        self,
        *,
        provider_factory: ProviderFactory = build_configured_provider,
        trace: TraceService = trace_service,
    ) -> None:
        self._provider_factory = provider_factory
        self._trace = trace

    def generate_for_project(
        self,
        *,
        project: dict[str, Any],
        target_platforms: list[str],
        tone: str,
        requirements: str,
    ) -> LLMProjectGenerateResponse:
        """Generate LLM platform content for an existing project."""
        provider = self._provider_factory()
        project_id = str(project["id"])
        run = self._trace.create_run(
            project_id=project_id,
            workflow_name="llm_generation",
            input_snapshot={
                "provider": provider.provider_name,
                "model": provider.model,
                "target_platforms": target_platforms,
                "tone": tone,
                "requirements_present": bool(requirements.strip()),
            },
        )
        step = self._trace.create_step(
            run_id=run.run_id,
            node_name="llm_generation",
            input_snapshot={
                "provider": provider.provider_name,
                "model": provider.model,
                "target_platforms": target_platforms,
            },
        )

        try:
            response = provider.generate_platform_content(
                LLMGenerateRequest(
                    title=str(project["title"]),
                    source_text=str(project["source_text"]),
                    target_platforms=target_platforms,
                    tone=tone,
                    requirements=requirements,
                )
            )
        except (DeepSeekProviderError, RuntimeError, ValueError) as exc:
            safe_message = str(exc)
            self._trace.fail_step(
                step.step_id,
                safe_message,
                output_snapshot={
                    "provider": provider.provider_name,
                    "model": provider.model,
                },
            )
            self._trace.fail_run(
                run.run_id,
                safe_message,
                output_snapshot={
                    "provider": provider.provider_name,
                    "model": provider.model,
                },
            )
            raise LLMProviderError(safe_message) from exc

        output_snapshot = {
            "provider": response.provider,
            "model": response.model,
            "platform_count": len(response.platform_outputs),
            "usage": response.usage,
            "warnings": response.warnings,
        }
        self._trace.finish_step(step.step_id, output_snapshot=output_snapshot)
        self._trace.finish_run(run.run_id, output_snapshot=output_snapshot)

        return LLMProjectGenerateResponse(
            project_id=project_id,
            run_id=run.run_id,
            provider=response.provider,
            model=response.model,
            platform_outputs=response.platform_outputs,
            usage=response.usage,
            warnings=response.warnings,
        )
