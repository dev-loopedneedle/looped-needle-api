"""Audits domain router."""

import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.audits.dependencies import get_audit_db
from src.audits.exceptions import AuditValidationError
from src.audits.schemas import (
    AuditRecordCreate,
    AuditRecordListQuery,
    AuditRecordListResponse,
    AuditRecordResponse,
    AuditRecordUpdate,
)
from src.audits.service import AuditService

router = APIRouter(prefix="/api/v1/audits", tags=["audits"])
logger = logging.getLogger(__name__)


def _get_request_id(request: Request) -> str | None:
    """Get request ID from request state."""
    return getattr(request.state, "request_id", None)


@router.post(
    "",
    response_model=AuditRecordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create audit record",
    description="Create a new audit record with a name.",
    response_description="The created audit record with all fields including generated ID and timestamps.",
)
async def create_audit(
    request: Request,
    audit_data: AuditRecordCreate,
    db: AsyncSession = Depends(get_audit_db),
) -> AuditRecordResponse:
    """
    Create a new audit record.

    This endpoint creates a new audit record with the provided name.
    """
    request_id = _get_request_id(request)
    logger.info(
        f"Creating audit record: name={audit_data.name}",
        extra={"request_id": request_id},
    )
    try:
        audit = await AuditService.create(db, audit_data)
        logger.info(f"Created audit record: id={audit.id}", extra={"request_id": request_id})
        return AuditRecordResponse.model_validate(audit)
    except ValueError as e:
        logger.error(
            f"Validation error creating audit record: {e}",
            extra={"request_id": request_id, "name": audit_data.name},
        )
        raise AuditValidationError(str(e)) from e


@router.get(
    "",
    response_model=AuditRecordListResponse,
    status_code=status.HTTP_200_OK,
    summary="List audit records",
    description="Retrieve a paginated list of audit records with optional filtering. Supports filtering by name and date range. Results are paginated with a default limit of 20 and maximum of 50 records per page.",
    response_description="Paginated list of audit records matching the filter criteria.",
)
async def list_audits(
    request: Request,
    name: str | None = Query(None, description="Filter by name (partial match)"),
    created_after: datetime | None = Query(
        None, description="Filter by creation date (ISO 8601 format, after this date)"
    ),
    created_before: datetime | None = Query(
        None, description="Filter by creation date (ISO 8601 format, before this date)"
    ),
    limit: int = Query(
        20, ge=1, le=50, description="Maximum number of records to return (default: 20, max: 50)"
    ),
    offset: int = Query(
        0, ge=0, description="Number of records to skip for pagination (default: 0)"
    ),
    db: AsyncSession = Depends(get_audit_db),
) -> AuditRecordListResponse:
    """
    List audit records with filtering and pagination.

    Returns a paginated list of audit records. Multiple filters can be combined.
    Results are ordered by creation date (newest first).
    """
    request_id = _get_request_id(request)
    logger.info(
        f"Listing audit records: limit={limit}, offset={offset}, filters={{name={name}}}",
        extra={"request_id": request_id},
    )
    query = AuditRecordListQuery(
        name=name,
        created_after=created_after,
        created_before=created_before,
        limit=limit,
        offset=offset,
    )
    audits, total = await AuditService.list(db, query)
    logger.info(
        f"Retrieved {len(audits)} audit records (total: {total})",
        extra={"request_id": request_id, "total": total, "returned": len(audits)},
    )
    return AuditRecordListResponse(
        items=[AuditRecordResponse.model_validate(audit) for audit in audits],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{audit_id}",
    response_model=AuditRecordResponse,
    status_code=status.HTTP_200_OK,
    summary="Get audit record",
    description="Retrieve a specific audit record by its unique identifier (UUID). Returns 404 if the audit record does not exist.",
    response_description="The audit record with the specified ID.",
)
async def get_audit(
    request: Request,
    audit_id: UUID,
    db: AsyncSession = Depends(get_audit_db),
) -> AuditRecordResponse:
    """
    Get audit record by ID.

    Retrieves a single audit record by its UUID. Raises 404 error if not found.
    """
    request_id = _get_request_id(request)
    logger.info(
        f"Getting audit record: id={audit_id}",
        extra={"request_id": request_id, "audit_id": str(audit_id)},
    )
    audit = await AuditService.get_by_id(db, audit_id)
    logger.info(f"Retrieved audit record: id={audit_id}", extra={"request_id": request_id})
    return AuditRecordResponse.model_validate(audit)


@router.put(
    "/{audit_id}",
    response_model=AuditRecordResponse,
    status_code=status.HTTP_200_OK,
    summary="Update audit record",
    description="Update an existing audit record. Only the name field can be updated. Returns 404 if the audit record does not exist.",
    response_description="The updated audit record.",
)
async def update_audit(
    request: Request,
    audit_id: UUID,
    update_data: AuditRecordUpdate,
    db: AsyncSession = Depends(get_audit_db),
) -> AuditRecordResponse:
    """
    Update an audit record.

    Updates the name of an existing audit record.
    Only this field can be modified; other fields are immutable.
    """
    request_id = _get_request_id(request)
    logger.info(
        f"Updating audit record: id={audit_id}",
        extra={"request_id": request_id, "audit_id": str(audit_id)},
    )
    try:
        audit = await AuditService.update(db, audit_id, update_data)
        logger.info(f"Updated audit record: id={audit.id}", extra={"request_id": request_id})
        return AuditRecordResponse.model_validate(audit)
    except ValueError as e:
        logger.error(
            f"Validation error updating audit record: {e}",
            extra={"request_id": request_id, "audit_id": str(audit_id)},
        )
        raise AuditValidationError(str(e)) from e


@router.delete(
    "/{audit_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete audit record",
    description="Permanently delete an audit record by its ID. Returns 204 No Content on success, or 404 if the audit record does not exist.",
    response_description="No content (204) on successful deletion.",
)
async def delete_audit(
    request: Request,
    audit_id: UUID,
    db: AsyncSession = Depends(get_audit_db),
) -> None:
    """
    Delete an audit record.

    Permanently removes an audit record from the database.
    This operation cannot be undone.
    """
    request_id = _get_request_id(request)
    logger.info(
        f"Deleting audit record: id={audit_id}",
        extra={"request_id": request_id, "audit_id": str(audit_id)},
    )
    await AuditService.delete(db, audit_id)
    logger.info(f"Deleted audit record: id={audit_id}", extra={"request_id": request_id})
    return None
