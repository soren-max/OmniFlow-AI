"""ContentOps Agent - FastAPI application entry point."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .api import api_router
from .core import settings
from .schemas.common import ApiError, ApiResponse

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Enterprise AI Agent platform for multi-platform content operations.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1):[0-9]+$",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


def _error_response(
    status_code: int,
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> JSONResponse:
    """Build a standardized error response."""
    payload = ApiResponse[None](
        success=False,
        data=None,
        error=ApiError(code=code, message=message, details=details),
    )
    return JSONResponse(
        status_code=status_code,
        content=payload.model_dump(mode="json"),
    )


def _validation_errors(exc: RequestValidationError) -> list[dict[str, Any]]:
    """Return JSON-serializable validation errors."""
    errors: list[dict[str, Any]] = []
    for error in exc.errors():
        normalized = dict(error)
        raw_context = normalized.get("ctx")
        if isinstance(raw_context, dict):
            normalized["ctx"] = {key: str(value) for key, value in raw_context.items()}
        errors.append(normalized)
    return errors


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(_request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Convert HTTP exceptions into the standard API envelope."""
    code = "HTTP_ERROR"
    raw_detail: object = exc.detail
    message = str(raw_detail)
    details: dict[str, Any] | None = None

    if isinstance(raw_detail, dict):
        detail = raw_detail
        code = str(detail.get("code", code))
        message = str(detail.get("message", message))
        raw_details = detail.get("details")
        details = raw_details if isinstance(raw_details, dict) else None

    return _error_response(
        status_code=exc.status_code,
        code=code,
        message=message,
        details=details,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    _request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Convert request validation errors into the standard API envelope."""
    return _error_response(
        status_code=422,
        code="VALIDATION_ERROR",
        message="Request validation failed",
        details={"errors": _validation_errors(exc)},
    )


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint - redirects to /docs in development."""
    return {
        "service": settings.app_name,
        "docs": "/docs",
        "health": "/health",
    }
