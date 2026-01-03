"""Schemas for sustainability standards (criteria and rules)."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from src.audit_engine.constants import MAX_PAGE_LIMIT, SustainabilityDomain


class CriterionCreate(BaseModel):
    """Schema for creating a sustainability criterion."""

    code: str = Field(..., description="Unique criterion code (e.g., ENV-001)")
    name: str = Field(..., description="Criterion name")
    description: str = Field(..., description="Criterion description")
    domain: SustainabilityDomain = Field(..., description="Sustainability domain")


class CriterionResponse(BaseModel):
    """Schema for criterion response."""

    id: UUID
    code: str
    name: str
    description: str
    domain: SustainabilityDomain
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}


class CriterionListQuery(BaseModel):
    """Schema for criterion list query parameters."""

    domain: SustainabilityDomain | None = Field(None, description="Filter by domain")
    limit: int = Field(
        default=20, ge=1, le=MAX_PAGE_LIMIT, description="Maximum number of records to return"
    )
    offset: int = Field(default=0, ge=0, description="Number of records to skip")


class CriterionListResponse(BaseModel):
    """Schema for paginated criterion list response."""

    items: list[CriterionResponse]
    total: int
    limit: int
    offset: int


class RuleCreate(BaseModel):
    """Schema for creating a criteria rule."""

    rule_name: str = Field(..., description="Admin reference name")
    condition_expression: str = Field(..., description="Python-like expression string")
    priority: int = Field(default=0, description="Priority (higher = more important)")


class RuleUpdate(BaseModel):
    """Schema for updating a criteria rule."""

    rule_name: str | None = Field(None, description="Admin reference name")
    condition_expression: str | None = Field(None, description="Python-like expression string")
    priority: int | None = Field(None, description="Priority (higher = more important)")


class RuleResponse(BaseModel):
    """Schema for rule response."""

    id: UUID
    criteria_id: UUID
    rule_name: str
    condition_expression: str
    priority: int
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}


class RuleListResponse(BaseModel):
    """Schema for rule list response."""

    items: list[RuleResponse]
    total: int


__all__ = [
    "CriterionCreate",
    "CriterionResponse",
    "CriterionListQuery",
    "CriterionListResponse",
    "RuleCreate",
    "RuleUpdate",
    "RuleResponse",
    "RuleListResponse",
]
