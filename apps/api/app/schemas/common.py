"""Shared API response schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ApiError(BaseModel):
    """Structured API error payload."""

    code: str = Field(..., description="Stable machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    details: dict[str, Any] | None = Field(
        default=None,
        description="Optional structured error details",
    )


class ApiResponse[T](BaseModel):
    """Standard API response envelope."""

    success: bool
    data: T | None = None
    error: ApiError | None = None


def ok[T](data: T) -> ApiResponse[T]:
    """Build a successful API response."""
    return ApiResponse(success=True, data=data, error=None)
