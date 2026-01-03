"""Schemas for audit runs (instances and items)."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from src.audit_engine.constants import MAX_PAGE_LIMIT, AuditInstanceStatus, AuditItemStatus


class AuditInstanceCreate(BaseModel):
    """Schema for creating an audit instance."""

    brand_id: UUID = Field(..., description="Brand ID")
    questionnaire_definition_id: UUID | None = Field(
        None, description="Questionnaire definition ID (optional)"
    )
    scoping_responses: dict[str, Any] = Field(..., description="Questionnaire answers")


class AuditInstanceUpdate(BaseModel):
    """Schema for updating an audit instance."""

    status: AuditInstanceStatus | None = Field(None, description="Audit status")
    overall_score: float | None = Field(None, ge=0, le=100, description="Overall audit score")


class AuditInstanceResponse(BaseModel):
    """Schema for audit instance response."""

    id: UUID
    brand_id: UUID
    questionnaire_definition_id: UUID | None = Field(
        None, description="Questionnaire definition ID"
    )
    status: AuditInstanceStatus
    scoping_responses: dict[str, Any]
    brand_context_snapshot: dict[str, Any]
    overall_score: float | None = Field(None, description="Overall audit score (0-100)")
    created_at: datetime
    updated_at: datetime | None = Field(None, description="Last update timestamp")

    model_config = {"from_attributes": True}


class AuditInstanceListQuery(BaseModel):
    """Schema for audit instance list query parameters."""

    brand_id: UUID | None = Field(None, description="Filter by brand ID")
    status: AuditInstanceStatus | None = Field(None, description="Filter by status")
    limit: int = Field(
        default=20, ge=1, le=MAX_PAGE_LIMIT, description="Maximum number of records to return"
    )
    offset: int = Field(default=0, ge=0, description="Number of records to skip")


class AuditInstanceListResponse(BaseModel):
    """Schema for paginated audit instance list response."""

    items: list[AuditInstanceResponse]
    total: int
    limit: int
    offset: int


class AuditItemResponse(BaseModel):
    """Schema for audit item response."""

    id: UUID
    audit_instance_id: UUID
    criteria_id: UUID
    triggered_by_rule_id: UUID
    status: AuditItemStatus
    auditor_comments: str | None = Field(None, description="Auditor comments")
    created_at: datetime
    updated_at: datetime | None = Field(None, description="Last update timestamp")

    model_config = {"from_attributes": True}


class AuditItemUpdate(BaseModel):
    """Schema for updating an audit item."""

    status: AuditItemStatus | None = Field(None, description="Audit item status")
    auditor_comments: str | None = Field(None, description="Auditor comments")


class AuditItemListResponse(BaseModel):
    """Schema for audit item list response."""

    items: list[AuditItemResponse]
    total: int


class AuditItemGenerationResponse(BaseModel):
    """Schema for audit item generation response."""

    items_created: int
    items_preserved: int
    rules_evaluated: int
    rules_failed: int
    message: str


__all__ = [
    "AuditInstanceCreate",
    "AuditInstanceUpdate",
    "AuditInstanceResponse",
    "AuditInstanceListQuery",
    "AuditInstanceListResponse",
    "AuditItemResponse",
    "AuditItemUpdate",
    "AuditItemListResponse",
    "AuditItemGenerationResponse",
]

