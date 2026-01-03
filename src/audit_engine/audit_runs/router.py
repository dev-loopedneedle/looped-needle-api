"""Audit runs domain router."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.audit_engine.audit_runs.schemas import (
    AuditInstanceCreate,
    AuditInstanceListQuery,
    AuditInstanceListResponse,
    AuditInstanceResponse,
    AuditInstanceUpdate,
    AuditItemGenerationResponse,
    AuditItemListResponse,
    AuditItemResponse,
    AuditItemUpdate,
)
from src.audit_engine.audit_runs.service import AuditInstanceService, AuditItemService
from src.audit_engine.constants import AuditInstanceStatus
from src.audit_engine.dependencies import get_audit_engine_db
from src.auth.dependencies import UserContext, get_current_user

router = APIRouter(prefix="/api/v1", tags=["audit-runs"])
logger = logging.getLogger(__name__)


def _get_request_id(request: Request) -> str | None:
    """Get request ID from request state."""
    return getattr(request.state, "request_id", None)


# Audit Instance endpoints
@router.post(
    "/audit-instances",
    response_model=AuditInstanceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create audit instance",
    description="Create a new audit instance with brand context snapshot",
)
async def create_audit_instance(
    request: Request,
    audit_data: AuditInstanceCreate,
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_audit_engine_db),
) -> AuditInstanceResponse:
    """Create a new audit instance."""
    request_id = _get_request_id(request)
    logger.info(
        f"Creating audit instance: brand_id={audit_data.brand_id}, questionnaire_id={audit_data.questionnaire_definition_id}",
        extra={"request_id": request_id},
    )
    audit_instance = await AuditInstanceService.create_audit_instance(db, audit_data, current_user)
    return AuditInstanceResponse.model_validate(audit_instance)


@router.get(
    "/audit-instances",
    response_model=AuditInstanceListResponse,
    summary="List audit instances",
    description="Retrieve a paginated list of audit instances",
)
async def list_audit_instances(
    request: Request,
    brand_id: UUID | None = Query(None, description="Filter by brand ID"),
    status: str | None = Query(None, description="Filter by status"),
    limit: int = Query(default=20, ge=1, le=50, description="Maximum number of records to return"),
    offset: int = Query(default=0, ge=0, description="Number of records to skip"),
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_audit_engine_db),
) -> AuditInstanceListResponse:
    """List audit instances with pagination."""
    request_id = _get_request_id(request)
    logger.info(
        f"Listing audit instances: brand_id={brand_id}, status={status}, limit={limit}, offset={offset}",
        extra={"request_id": request_id},
    )

    query = AuditInstanceListQuery(
        brand_id=brand_id,
        status=AuditInstanceStatus(status) if status else None,
        limit=limit,
        offset=offset,
    )
    audit_instances, total = await AuditInstanceService.list_audit_instances(
        db, query, current_user
    )
    return AuditInstanceListResponse(
        items=[AuditInstanceResponse.model_validate(ai) for ai in audit_instances],
        total=total,
        limit=query.limit,
        offset=query.offset,
    )


@router.get(
    "/audit-instances/{audit_instance_id}",
    response_model=AuditInstanceResponse,
    summary="Get audit instance",
    description="Retrieve a specific audit instance by ID",
)
async def get_audit_instance(
    request: Request,
    audit_instance_id: UUID,
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_audit_engine_db),
) -> AuditInstanceResponse:
    """Get audit instance by ID."""
    request_id = _get_request_id(request)
    logger.info(f"Getting audit instance: id={audit_instance_id}", extra={"request_id": request_id})
    audit_instance = await AuditInstanceService.get_audit_instance_with_access(
        db, audit_instance_id, current_user
    )
    return AuditInstanceResponse.model_validate(audit_instance)


@router.put(
    "/audit-instances/{audit_instance_id}",
    response_model=AuditInstanceResponse,
    summary="Update audit instance",
    description="Update an existing audit instance (status, score)",
)
async def update_audit_instance(
    request: Request,
    audit_instance_id: UUID,
    audit_data: AuditInstanceUpdate,
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_audit_engine_db),
) -> AuditInstanceResponse:
    """Update audit instance."""
    request_id = _get_request_id(request)
    logger.info(
        f"Updating audit instance: id={audit_instance_id}", extra={"request_id": request_id}
    )
    audit_instance = await AuditInstanceService.update_audit_instance_status(
        db, audit_instance_id, audit_data, current_user
    )
    return AuditInstanceResponse.model_validate(audit_instance)


# Audit Item endpoints
@router.post(
    "/audit-instances/{audit_instance_id}/generate-items",
    response_model=AuditItemGenerationResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate audit items",
    description="Generate audit items by evaluating rules against brand context and questionnaire responses",
)
async def generate_audit_items(
    request: Request,
    audit_instance_id: UUID,
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_audit_engine_db),
) -> AuditItemGenerationResponse:
    """Generate audit items for an audit instance."""
    request_id = _get_request_id(request)
    logger.info(
        f"Generating audit items for audit instance: id={audit_instance_id}",
        extra={"request_id": request_id},
    )
    service = AuditItemService()
    stats = await service.generate_audit_items(db, audit_instance_id, current_user)
    return AuditItemGenerationResponse(
        items_created=stats["items_created"],
        items_preserved=stats["items_preserved"],
        rules_evaluated=stats["rules_evaluated"],
        rules_failed=stats["rules_failed"],
        message=f"Generated {stats['items_created']} new items, preserved {stats['items_preserved']} existing items",
    )


@router.get(
    "/audit-instances/{audit_instance_id}/items",
    response_model=AuditItemListResponse,
    summary="List audit items",
    description="Retrieve all audit items for an audit instance",
)
async def list_audit_items(
    request: Request,
    audit_instance_id: UUID,
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_audit_engine_db),
) -> AuditItemListResponse:
    """List audit items for an audit instance."""
    request_id = _get_request_id(request)
    logger.info(
        f"Listing audit items for audit instance: id={audit_instance_id}",
        extra={"request_id": request_id},
    )
    service = AuditItemService()
    items = await service.get_audit_items_by_instance(db, audit_instance_id, current_user)
    return AuditItemListResponse(
        items=[AuditItemResponse.model_validate(item) for item in items],
        total=len(items),
    )


@router.get(
    "/audit-items/{audit_item_id}",
    response_model=AuditItemResponse,
    summary="Get audit item",
    description="Retrieve a specific audit item by ID",
)
async def get_audit_item(
    request: Request,
    audit_item_id: UUID,
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_audit_engine_db),
) -> AuditItemResponse:
    """Get audit item by ID."""
    request_id = _get_request_id(request)
    logger.info(f"Getting audit item: id={audit_item_id}", extra={"request_id": request_id})
    service = AuditItemService()
    audit_item = await service.get_audit_item(db, audit_item_id, current_user)
    return AuditItemResponse.model_validate(audit_item)


@router.put(
    "/audit-items/{audit_item_id}",
    response_model=AuditItemResponse,
    summary="Update audit item",
    description="Update an existing audit item (status, comments)",
)
async def update_audit_item(
    request: Request,
    audit_item_id: UUID,
    audit_item_data: AuditItemUpdate,
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_audit_engine_db),
) -> AuditItemResponse:
    """Update audit item."""
    request_id = _get_request_id(request)
    logger.info(f"Updating audit item: id={audit_item_id}", extra={"request_id": request_id})
    service = AuditItemService()
    audit_item = await service.update_audit_item(
        db, audit_item_id, audit_item_data, current_user
    )
    return AuditItemResponse.model_validate(audit_item)

