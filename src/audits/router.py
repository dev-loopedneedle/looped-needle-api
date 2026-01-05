"""Audits domain router."""

import logging

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.audits.schemas import (
    AuditData,
    AuditListQuery,
    AuditListResponse,
    AuditResponse,
    CreateAuditRequest,
    UpdateAuditRequest,
)
from src.audits.service import AuditService
from src.auth.dependencies import UserContext, get_current_user
from src.core.dependencies import get_request_id
from src.database import get_db

router = APIRouter(prefix="/api/v1", tags=["audits"])
logger = logging.getLogger(__name__)


@router.post(
    "/audits",
    response_model=AuditResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create audit",
    description="Create a new audit with product, materials, supply chain, and sustainability data",
)
async def create_audit(
    audit_request: CreateAuditRequest,
    request_id: str | None = Depends(get_request_id),
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AuditResponse:
    """Create a new audit."""
    logger.info(
        f"Creating audit: brand_id={audit_request.brand_id}",
        extra={"request_id": request_id},
    )

    audit = await AuditService.create_audit(db, audit_request, current_user)
    # Parse audit_data from dict to AuditData model (handle empty dict)
    audit_data = None
    if audit.audit_data is not None and len(audit.audit_data) > 0:
        audit_data = AuditData.model_validate(audit.audit_data)
    audit_dict = {
        "id": audit.id,
        "brand_id": audit.brand_id,
        "status": audit.status,
        "audit_data": audit_data,
        "created_at": audit.created_at,
        "updated_at": audit.updated_at,
    }
    return AuditResponse.model_validate(audit_dict)


@router.get(
    "/audits",
    response_model=AuditListResponse,
    summary="List audits",
    description="Retrieve a paginated list of audits, optionally filtered by brand_id, status, scope, and category",
)
async def list_audits(
    brand_id: str | None = Query(None, description="Filter by brand ID (UUID)"),
    status: str | None = Query(None, description="Filter by audit status: DRAFT or PUBLISHED"),
    scope: str | None = Query(
        None, description="Filter by audit scope: Single Product, Collection, or Brand-wide"
    ),
    category: str | None = Query(None, description="Filter by product category"),
    limit: int = Query(default=20, ge=1, le=50, description="Maximum number of records to return"),
    offset: int = Query(default=0, ge=0, description="Number of records to skip"),
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AuditListResponse:
    """List audits with pagination and optional filtering."""

    from typing import cast
    from uuid import UUID

    from fastapi import HTTPException

    # Validate status if provided
    if status is not None and status not in ("DRAFT", "PUBLISHED"):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status: {status}. Must be 'DRAFT' or 'PUBLISHED'",
        )

    # Validate scope if provided
    if scope is not None and scope not in ("Single Product", "Collection", "Brand-wide"):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid scope: {scope}. Must be 'Single Product', 'Collection', or 'Brand-wide'",
        )

    # Type narrowing for Literal types
    from typing import Literal

    status_literal: Literal["DRAFT", "PUBLISHED"] | None = (
        cast(Literal["DRAFT", "PUBLISHED"], status) if status in ("DRAFT", "PUBLISHED") else None
    )
    scope_literal: Literal["Single Product", "Collection", "Brand-wide"] | None = (
        cast(Literal["Single Product", "Collection", "Brand-wide"], scope)
        if scope in ("Single Product", "Collection", "Brand-wide")
        else None
    )

    query = AuditListQuery(
        brand_id=UUID(brand_id) if brand_id else None,
        status=status_literal,
        scope=scope_literal,
        category=category,
        limit=limit,
        offset=offset,
    )
    audits, total = await AuditService.list_audits(db, query, current_user)

    # Convert audits to response format
    audit_responses = []
    for audit in audits:
        audit_data = None
        if audit.audit_data is not None and len(audit.audit_data) > 0:
            audit_data = AuditData.model_validate(audit.audit_data)
        audit_dict = {
            "id": audit.id,
            "brand_id": audit.brand_id,
            "status": audit.status,
            "audit_data": audit_data,
            "created_at": audit.created_at,
            "updated_at": audit.updated_at,
        }
        audit_responses.append(AuditResponse.model_validate(audit_dict))

    return AuditListResponse(
        items=audit_responses,
        total=total,
        limit=query.limit,
        offset=query.offset,
    )


@router.get(
    "/audits/{audit_id}",
    response_model=AuditResponse,
    summary="Get audit",
    description="Retrieve a specific audit by ID",
)
async def get_audit(
    audit_id: str,
    db: AsyncSession = Depends(get_db),
) -> AuditResponse:
    """Get audit by ID."""

    audit = await AuditService.get_audit(db, audit_id)
    # Parse audit_data from dict to AuditData model (handle empty dict)
    audit_data = None
    if audit.audit_data is not None and len(audit.audit_data) > 0:
        audit_data = AuditData.model_validate(audit.audit_data)
    audit_dict = {
        "id": audit.id,
        "brand_id": audit.brand_id,
        "status": audit.status,
        "audit_data": audit_data,
        "created_at": audit.created_at,
        "updated_at": audit.updated_at,
    }
    return AuditResponse.model_validate(audit_dict)


@router.put(
    "/audits/{audit_id}",
    response_model=AuditResponse,
    summary="Update audit",
    description="Update an audit (status cannot be set directly, always resets to DRAFT). Published audits cannot be updated.",
)
async def update_audit(
    audit_id: str,
    update_request: UpdateAuditRequest,
    request_id: str | None = Depends(get_request_id),
    db: AsyncSession = Depends(get_db),
) -> AuditResponse:
    """Update an audit."""
    logger.info(
        f"Updating audit: id={audit_id}",
        extra={"request_id": request_id},
    )

    audit = await AuditService.update_audit(db, audit_id, update_request)
    # Parse audit_data from dict to AuditData model (handle empty dict)
    audit_data = None
    if audit.audit_data is not None and len(audit.audit_data) > 0:
        audit_data = AuditData.model_validate(audit.audit_data)
    audit_dict = {
        "id": audit.id,
        "brand_id": audit.brand_id,
        "status": audit.status,
        "audit_data": audit_data,
        "created_at": audit.created_at,
        "updated_at": audit.updated_at,
    }
    return AuditResponse.model_validate(audit_dict)


@router.post(
    "/audits/{audit_id}/publish",
    response_model=AuditResponse,
    summary="Publish audit",
    description="Publish an audit (set status to PUBLISHED). Once published, audit cannot be updated.",
)
async def publish_audit(
    audit_id: str,
    request_id: str | None = Depends(get_request_id),
    db: AsyncSession = Depends(get_db),
) -> AuditResponse:
    """Publish an audit."""
    logger.info(
        f"Publishing audit: id={audit_id}",
        extra={"request_id": request_id},
    )

    audit = await AuditService.publish_audit(db, audit_id)
    # Parse audit_data from dict to AuditData model (handle empty dict)
    audit_data = None
    if audit.audit_data is not None and len(audit.audit_data) > 0:
        audit_data = AuditData.model_validate(audit.audit_data)
    audit_dict = {
        "id": audit.id,
        "brand_id": audit.brand_id,
        "status": audit.status,
        "audit_data": audit_data,
        "created_at": audit.created_at,
        "updated_at": audit.updated_at,
    }
    return AuditResponse.model_validate(audit_dict)
