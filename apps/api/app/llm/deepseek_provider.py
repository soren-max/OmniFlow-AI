"""DeepSeek OpenAI-compatible chat completions provider."""

from __future__ import annotations

import json
from typing import Any, cast

import httpx
from api.app.llm.schemas import (
    LLMGenerateRequest,
    LLMGenerateResponse,
    LLMPlatformOutput,
)
from pydantic import TypeAdapter, ValidationError


class DeepSeekProviderError(RuntimeError):
    """Raised when DeepSeek generation fails."""


class DeepSeekProvider:
    """Generate platform content through DeepSeek chat completions."""

    provider_name = "deepseek"

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        model: str,
        timeout_seconds: float,
        client: httpx.Client | None = None,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self.model = model
        self._timeout_seconds = timeout_seconds
        self._client = client

    def generate_platform_content(
        self,
        request: LLMGenerateRequest,
    ) -> LLMGenerateResponse:
        """Call DeepSeek and parse structured JSON platform outputs."""
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You generate JSON only for a multi-platform content operations "
                        "workflow. Do not include markdown fences."
                    ),
                },
                {
                    "role": "user",
                    "content": self._build_prompt(request),
                },
            ],
            "temperature": 0.4,
            "response_format": {"type": "json_object"},
        }

        try:
            response_payload = self._post_chat_completion(payload)
            content = self._extract_content(response_payload)
            outputs, warnings = self._parse_outputs(content, request.target_platforms)
            usage = self._extract_usage(response_payload)
        except (httpx.HTTPError, KeyError, TypeError, ValueError, ValidationError) as exc:
            raise DeepSeekProviderError(f"DeepSeek generation failed: {exc}") from exc

        return LLMGenerateResponse(
            platform_outputs=outputs,
            provider=self.provider_name,
            model=self.model,
            usage=usage,
            warnings=warnings,
        )

    def _post_chat_completion(self, payload: dict[str, Any]) -> dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        url = f"{self._base_url}/chat/completions"

        if self._client is not None:
            response = self._client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return cast(dict[str, Any], response.json())

        with httpx.Client(timeout=self._timeout_seconds) as client:
            response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return cast(dict[str, Any], response.json())

    @staticmethod
    def _build_prompt(request: LLMGenerateRequest) -> str:
        return json.dumps(
            {
                "task": "Generate platform-specific content as JSON.",
                "output_contract": {
                    "platform_outputs": [
                        {
                            "platform": "wechat",
                            "title": "string",
                            "body": "string",
                            "hashtags": ["string"],
                            "summary": "string",
                            "cta": "string",
                            "notes": "string",
                        }
                    ]
                },
                "platforms": request.target_platforms,
                "tone": request.tone,
                "requirements": request.requirements,
                "source": {
                    "title": request.title,
                    "text": request.source_text,
                },
            },
            ensure_ascii=False,
        )

    @staticmethod
    def _extract_content(response_payload: dict[str, Any]) -> str:
        choices = response_payload["choices"]
        if not isinstance(choices, list) or not choices:
            raise ValueError("DeepSeek response did not include choices")
        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            raise ValueError("DeepSeek choice payload was invalid")
        message = first_choice["message"]
        if not isinstance(message, dict):
            raise ValueError("DeepSeek message payload was invalid")
        content = message["content"]
        if not isinstance(content, str) or not content.strip():
            raise ValueError("DeepSeek response content was empty")
        return content

    @staticmethod
    def _parse_outputs(
        content: str,
        target_platforms: list[str],
    ) -> tuple[list[LLMPlatformOutput], list[str]]:
        parsed = json.loads(DeepSeekProvider._strip_json_fence(content))
        raw_outputs = parsed.get("platform_outputs") if isinstance(parsed, dict) else parsed
        outputs = TypeAdapter(list[LLMPlatformOutput]).validate_python(raw_outputs)

        requested = set(target_platforms)
        returned = {output.platform for output in outputs}
        missing = requested - returned
        extras = returned - requested
        warnings: list[str] = []
        if missing:
            raise ValueError(f"DeepSeek response missing platforms: {sorted(missing)}")
        if extras:
            warnings.append(f"DeepSeek returned extra platforms that were ignored: {sorted(extras)}")

        filtered = [output for output in outputs if output.platform in requested]
        return filtered, warnings

    @staticmethod
    def _extract_usage(response_payload: dict[str, Any]) -> dict[str, int]:
        raw_usage = response_payload.get("usage")
        if not isinstance(raw_usage, dict):
            return {}
        usage: dict[str, int] = {}
        for key in ("prompt_tokens", "completion_tokens", "total_tokens"):
            value = raw_usage.get(key)
            if isinstance(value, int):
                usage[key] = value
        return usage

    @staticmethod
    def _strip_json_fence(content: str) -> str:
        stripped = content.strip()
        if not stripped.startswith("```"):
            return stripped
        lines = stripped.splitlines()
        if len(lines) >= 3 and lines[-1].strip() == "```":
            return "\n".join(lines[1:-1]).strip()
        return stripped
