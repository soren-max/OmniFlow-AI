"""Content project API routes.

Thin layer — delegates all business logic to ContentProjectService.
"""

from __future__ import annotations

from typing import Any

from api.app.adapters.registry import AdapterNotFoundError
from api.app.adapters.types import Platform
from api.app.agents.runner import run_content_preview_workflow
from api.app.llm.schemas import LLMProjectGenerateRequest, LLMProjectGenerateResponse
from api.app.llm.service import (
    LLMProviderConfigurationError,
    LLMProviderError,
    LLMService,
)
from api.app.schemas.common import ApiResponse, ok
from api.app.schemas.project import (
    ContentProjectResponse,
    CreateContentProjectRequest,
    CreatePublishDraftRequest,
    DraftHandoffResponse,
    EvaluationReportResponse,
    ExportPublishDraftRequest,
    ExportPublishDraftResponse,
    GeneratePreviewRequest,
    PlatformPreviewResponse,
    PublishDraftResponse,
    PublishPackageResponse,
    PublishProjectRequest,
    PublishProjectResponse,
    UpdatePublishDraftRequest,
)
from api.app.services.project_service import (
    AdapterExecutionError,
    ContentProjectService,
    DraftNotFoundError,
    EvaluationNotFoundError,
    EvaluationRequiresPreviewError,
    ExportRequiresPreviewError,
    InvalidPlatformError,
    ProjectNotApprovedError,
    ProjectNotFoundError,
    RealPublishNotSupportedError,
    UnsupportedPublishModeError,
)
from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse

router = APIRouter(prefix="/api/projects", tags=["projects"])
draft_router = APIRouter(prefix="/api/drafts", tags=["drafts"])

# Singleton service instance (will be replaced with DI in future)
_service = ContentProjectService()
_llm_service = LLMService()


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
    except ExportRequiresPreviewError as exc:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "EXPORT_REQUIRES_PREVIEW",
                "message": str(exc),
                "details": {"project_id": exc.project_id},
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


@router.get("/{project_id}/export", response_model=ApiResponse[PublishPackageResponse])
async def export_publish_package(project_id: str) -> ApiResponse[dict[str, Any]]:
    """Return a JSON publish package for manual platform publishing."""
    try:
        return ok(_service.build_publish_package(project_id))
    except ProjectNotFoundError:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "PROJECT_NOT_FOUND",
                "message": f"Project not found: {project_id}",
                "details": {"project_id": project_id},
            },
        )
    except ExportRequiresPreviewError as exc:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "EXPORT_REQUIRES_PREVIEW",
                "message": str(exc),
                "details": {"project_id": exc.project_id},
            },
        )


@router.get("/{project_id}/export/json", response_model=ApiResponse[PublishPackageResponse])
async def export_publish_package_json(project_id: str) -> ApiResponse[dict[str, Any]]:
    """Return the same JSON publish package through an explicit export path."""
    return await export_publish_package(project_id)


@router.get("/{project_id}/export/markdown", response_class=PlainTextResponse)
async def export_publish_package_markdown(project_id: str) -> PlainTextResponse:
    """Return a Markdown publish package for manual platform publishing."""
    try:
        markdown = _service.build_publish_package_markdown(project_id)
        return PlainTextResponse(markdown, media_type="text/markdown; charset=utf-8")
    except ProjectNotFoundError:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "PROJECT_NOT_FOUND",
                "message": f"Project not found: {project_id}",
                "details": {"project_id": project_id},
            },
        )


@router.post(
    "/{project_id}/drafts",
    response_model=ApiResponse[PublishDraftResponse],
    status_code=201,
)
async def create_publish_draft(
    project_id: str,
    body: CreatePublishDraftRequest,
) -> ApiResponse[dict[str, Any]]:
    """Save platform content as an OmniFlow-AI system draft."""
    try:
        return ok(
            _service.create_publish_draft(
                project_id=project_id,
                platform=body.platform,
                title=body.title,
                body=body.body,
                hashtags=body.hashtags,
                summary=body.summary,
                cta=body.cta,
                notes=body.notes,
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


@router.get("/{project_id}/drafts", response_model=ApiResponse[list[PublishDraftResponse]])
async def list_publish_drafts(project_id: str) -> ApiResponse[list[dict[str, Any]]]:
    """List OmniFlow-AI system drafts for a project."""
    try:
        return ok(_service.list_publish_drafts(project_id))
    except ProjectNotFoundError:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "PROJECT_NOT_FOUND",
                "message": f"Project not found: {project_id}",
                "details": {"project_id": project_id},
            },
        )


@draft_router.get("/{draft_id}", response_model=ApiResponse[PublishDraftResponse])
async def get_publish_draft(draft_id: str) -> ApiResponse[dict[str, Any]]:
    """Get one OmniFlow-AI system draft."""
    try:
        return ok(_service.get_publish_draft(draft_id))
    except DraftNotFoundError:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "DRAFT_NOT_FOUND",
                "message": f"Publish draft not found: {draft_id}",
                "details": {"draft_id": draft_id},
            },
        )


@draft_router.patch("/{draft_id}", response_model=ApiResponse[PublishDraftResponse])
async def update_publish_draft(
    draft_id: str,
    body: UpdatePublishDraftRequest,
) -> ApiResponse[dict[str, Any]]:
    """Edit one OmniFlow-AI system draft."""
    try:
        return ok(
            _service.update_publish_draft(
                draft_id,
                body.model_dump(exclude_unset=True),
            )
        )
    except DraftNotFoundError:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "DRAFT_NOT_FOUND",
                "message": f"Publish draft not found: {draft_id}",
                "details": {"draft_id": draft_id},
            },
        )
    except InvalidPlatformError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_PLATFORM",
                "message": str(exc),
                "details": {"platform": exc.platform},
            },
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_DRAFT_UPDATE",
                "message": str(exc),
                "details": {"draft_id": draft_id},
            },
        )


@draft_router.post(
    "/{draft_id}/export",
    response_model=ApiResponse[ExportPublishDraftResponse],
)
async def export_publish_draft(
    draft_id: str,
    body: ExportPublishDraftRequest,
) -> ApiResponse[dict[str, Any]]:
    """Export one OmniFlow-AI system draft for manual copy/save workflows."""
    try:
        return ok(_service.export_publish_draft(draft_id, body.format))
    except DraftNotFoundError:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "DRAFT_NOT_FOUND",
                "message": f"Publish draft not found: {draft_id}",
                "details": {"draft_id": draft_id},
            },
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_DRAFT_EXPORT",
                "message": str(exc),
                "details": {"draft_id": draft_id},
            },
        )


@draft_router.post(
    "/{draft_id}/handoff",
    response_model=ApiResponse[DraftHandoffResponse],
)
async def open_publish_draft_handoff(draft_id: str) -> ApiResponse[dict[str, Any]]:
    """Mark a system draft as ready for manual official publish page handoff."""
    try:
        return ok(_service.open_publish_draft_handoff(draft_id))
    except DraftNotFoundError:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "DRAFT_NOT_FOUND",
                "message": f"Publish draft not found: {draft_id}",
                "details": {"draft_id": draft_id},
            },
        )
    except InvalidPlatformError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_PLATFORM",
                "message": str(exc),
                "details": {"platform": exc.platform},
            },
        )
@router.post(
    "/{project_id}/llm-generate",
    response_model=ApiResponse[LLMProjectGenerateResponse],
)
async def generate_llm_content(
    project_id: str,
    body: LLMProjectGenerateRequest,
) -> ApiResponse[LLMProjectGenerateResponse]:
    """Generate optional provider-backed platform content for a project."""
    try:
        for platform in body.platforms:
            Platform(platform)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_PLATFORM",
                "message": str(exc),
                "details": {
                    "valid_platforms": [
                        platform.value for platform in _service.supported_platforms()
                    ],
                },
            },
        )

    try:
        project = _service.get_project(project_id)
        return ok(
            _llm_service.generate_for_project(
                project=project,
                target_platforms=body.platforms,
                tone=body.tone,
                requirements=body.requirements,
            )
        )
    except LLMProviderConfigurationError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "LLM_PROVIDER_NOT_CONFIGURED",
                "message": str(exc),
                "details": {"project_id": project_id},
            },
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
    except LLMProviderError as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "code": "LLM_PROVIDER_ERROR",
                "message": str(exc),
                "details": {"project_id": project_id},
            },
        )


@router.post(
    "/{project_id}/evaluation",
    response_model=ApiResponse[EvaluationReportResponse],
)
async def create_evaluation(project_id: str) -> ApiResponse[dict[str, Any]]:
    """Create a rule-based content quality evaluation report."""
    try:
        return ok(_service.evaluate_project(project_id))
    except ProjectNotFoundError:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "PROJECT_NOT_FOUND",
                "message": f"Project not found: {project_id}",
                "details": {"project_id": project_id},
            },
        )
    except EvaluationRequiresPreviewError as exc:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "EVALUATION_REQUIRES_PREVIEW",
                "message": str(exc),
                "details": {"project_id": exc.project_id},
            },
        )


@router.get("/{project_id}/evaluation", response_model=ApiResponse[EvaluationReportResponse])
async def get_evaluation(project_id: str) -> ApiResponse[dict[str, Any]]:
    """Return the latest rule-based content quality evaluation report."""
    try:
        return ok(_service.get_evaluation(project_id))
    except ProjectNotFoundError:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "PROJECT_NOT_FOUND",
                "message": f"Project not found: {project_id}",
                "details": {"project_id": project_id},
            },
        )
    except EvaluationNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "EVALUATION_NOT_FOUND",
                "message": str(exc),
                "details": {"project_id": exc.project_id},
            },
        )


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
