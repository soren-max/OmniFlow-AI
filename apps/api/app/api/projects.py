"""Content project API routes.

Thin layer — delegates all business logic to ContentProjectService.
"""

from __future__ import annotations

from typing import Any

from api.app.adapters.registry import AdapterNotFoundError
from api.app.agents.runner import run_content_preview_workflow
from api.app.schemas.common import ApiResponse, ok
from api.app.schemas.project import (
    ContentProjectResponse,
    CreateContentProjectRequest,
    GeneratePreviewRequest,
    PlatformPreviewResponse,
    PublishProjectRequest,
    PublishProjectResponse,
)
from api.app.services.project_service import (
    AdapterExecutionError,
    ContentProjectService,
    InvalidPlatformError,
    ProjectNotApprovedError,
    ProjectNotFoundError,
    RealPublishNotSupportedError,
    UnsupportedPublishModeError,
)
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/projects", tags=["projects"])

# Singleton service instance (will be replaced with DI in future)
_service = ContentProjectService()


@router.post("", response_model=ApiResponse[ContentProjectResponse], status_code=201)
async def create_project(body: CreateContentProjectRequest) -> ApiResponse[dict[str, Any]]:
    """Create a new content project."""
    return ok(
        _service.create_project(
            title=body.title,
            source_text=body.source_text,
            source_url=body.source_url,
        )
    )


@router.get("/{project_id}", response_model=ApiResponse[ContentProjectResponse])
async def get_project(project_id: str) -> ApiResponse[dict[str, Any]]:
    """Get a content project by its id."""
    try:
        return ok(_service.get_project(project_id))
    except ProjectNotFoundError:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "PROJECT_NOT_FOUND",
                "message": f"Project not found: {project_id}",
                "details": {"project_id": project_id},
            },
        )


@router.post("/{project_id}/preview", response_model=ApiResponse[PlatformPreviewResponse])
async def generate_preview(
    project_id: str,
    body: GeneratePreviewRequest,
) -> ApiResponse[dict[str, Any]]:
    """Generate platform previews for a content project."""
    try:
        return ok(
            _service.generate_previews(
                project_id=project_id,
                platforms=body.platforms,
                title_override=body.title,
                hooks=body.hooks,
                tags=body.tags,
            )
        )
    except ProjectNotFoundError:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "PROJECT_NOT_FOUND",
                "message": f"Project not found: {project_id}",
                "details": {"project_id": project_id},
            },
        )
    except InvalidPlatformError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_PLATFORM",
                "message": str(exc),
                "details": {
                    "platform": exc.platform,
                    "valid_platforms": [
                        platform.value for platform in _service.supported_platforms()
                    ],
                },
            },
        )
    except AdapterExecutionError as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "ADAPTER_EXECUTION_FAILED",
                "message": str(exc),
                "details": {"platform": exc.platform, "reason": exc.reason},
            },
        )
    except AdapterNotFoundError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "ADAPTER_NOT_FOUND",
                "message": str(exc),
                "details": {"platform": str(exc.platform)},
            },
        )


@router.post("/{project_id}/agent-preview", response_model=ApiResponse[dict[str, Any]])
async def generate_agent_preview(
    project_id: str,
    body: GeneratePreviewRequest,
) -> ApiResponse[dict[str, Any]]:
    """Run the experimental deterministic Agent preview workflow."""
    try:
        project = _service.get_project(project_id)
    except ProjectNotFoundError:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "PROJECT_NOT_FOUND",
                "message": f"Project not found: {project_id}",
                "details": {"project_id": project_id},
            },
        )

    state = run_content_preview_workflow(
        project_id=project_id,
        source_title=str(project["title"]),
        source_content=str(project["source_text"]),
        target_platforms=body.platforms,
    )
    return ok(dict(state))


@router.post("/{project_id}/review/approve", response_model=ApiResponse[ContentProjectResponse])
async def approve_project(project_id: str) -> ApiResponse[dict[str, Any]]:
    """Approve a reviewed project for mock publish."""
    try:
        return ok(_service.approve_project(project_id))
    except ProjectNotFoundError:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "PROJECT_NOT_FOUND",
                "message": f"Project not found: {project_id}",
                "details": {"project_id": project_id},
            },
        )


@router.post("/{project_id}/review/reject", response_model=ApiResponse[ContentProjectResponse])
async def reject_project(project_id: str) -> ApiResponse[dict[str, Any]]:
    """Reject a reviewed project and block mock publish."""
    try:
        return ok(_service.reject_project(project_id))
    except ProjectNotFoundError:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "PROJECT_NOT_FOUND",
                "message": f"Project not found: {project_id}",
                "details": {"project_id": project_id},
            },
        )


@router.post("/{project_id}/publish", response_model=ApiResponse[PublishProjectResponse])
async def publish_project(
    project_id: str,
    body: PublishProjectRequest,
) -> ApiResponse[dict[str, Any]]:
    """Mock-publish a project to selected platforms."""
    try:
        return ok(
            _service.publish_project(
                project_id=project_id,
                target_platforms=body.target_platforms,
                mode=body.mode,
            )
        )
    except ProjectNotFoundError:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "PROJECT_NOT_FOUND",
                "message": f"Project not found: {project_id}",
                "details": {"project_id": project_id},
            },
        )
    except RealPublishNotSupportedError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "REAL_PUBLISH_NOT_SUPPORTED",
                "message": str(exc),
                "details": {"mode": body.mode},
            },
        )
    except UnsupportedPublishModeError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "UNSUPPORTED_PUBLISH_MODE",
                "message": str(exc),
                "details": {"mode": exc.mode, "supported_modes": ["mock"]},
            },
        )
    except ProjectNotApprovedError as exc:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "PROJECT_REVIEW_REQUIRED",
                "message": str(exc),
                "details": {
                    "project_id": exc.project_id,
                    "status": exc.status,
                    "required_status": "approved",
                },
            },
        )
    except InvalidPlatformError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_PLATFORM",
                "message": str(exc),
                "details": {
                    "platform": exc.platform,
                    "valid_platforms": [
                        platform.value for platform in _service.supported_platforms()
                    ],
                },
            },
        )
    except AdapterExecutionError as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "ADAPTER_EXECUTION_FAILED",
                "message": str(exc),
                "details": {"platform": exc.platform, "reason": exc.reason},
            },
        )
    except AdapterNotFoundError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "ADAPTER_NOT_FOUND",
                "message": str(exc),
                "details": {"platform": str(exc.platform)},
            },
        )
