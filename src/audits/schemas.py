"""Audits domain Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from src.audits.constants import MAX_PAGE_LIMIT


class AuditRecordCreate(BaseModel):
    """Schema for creating an audit record."""

    name: str = Field(..., max_length=255, description="Name of the audit record")


class AuditRecordUpdate(BaseModel):
    """Schema for updating an audit record."""

    name: str | None = Field(None, max_length=255, description="Name of the audit record")


class AuditRecordResponse(BaseModel):
    """Schema for audit record response."""

    id: UUID
    name: str
    created_at: datetime
    updated_at: datetime | None


class AuditRecordListQuery(BaseModel):
    """Schema for audit record list query parameters."""

    name: str | None = None
    created_after: datetime | None = None
    created_before: datetime | None = None
    limit: int = Field(
        default=20, ge=1, le=MAX_PAGE_LIMIT, description="Maximum number of records to return"
    )
    offset: int = Field(default=0, ge=0, description="Number of records to skip")


class AuditRecordListResponse(BaseModel):
    """Schema for paginated audit record list response."""

    items: list[AuditRecordResponse]
    total: int
    limit: int
    offset: int
