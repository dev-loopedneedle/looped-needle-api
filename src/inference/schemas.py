"""Inference engine domain Pydantic schemas."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from src.inference.constants import (
    MAX_PAGE_LIMIT,
    AuditInstanceStatus,
    AuditItemStatus,
    CompanySize,
    SustainabilityDomain,
)


# Brand Schemas
class BrandCreate(BaseModel):
    """Schema for creating a brand."""

    name: str = Field(..., max_length=255, description="Brand name")
    registration_country: str = Field(..., description="ISO country code")
    company_size: CompanySize = Field(..., description="Company size")
    target_markets: list[str] = Field(..., description="Array of ISO country codes")


class BrandUpdate(BaseModel):
    """Schema for updating a brand."""

    name: str | None = Field(None, max_length=255, description="Brand name")
    registration_country: str | None = Field(None, description="ISO country code")
    company_size: CompanySize | None = Field(None, description="Company size")
    target_markets: list[str] | None = Field(None, description="Array of ISO country codes")


class BrandResponse(BaseModel):
    """Schema for brand response."""

    id: UUID
    name: str
    registration_country: str
    company_size: CompanySize
    target_markets: list[str]
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}


class BrandListQuery(BaseModel):
    """Schema for brand list query parameters."""

    limit: int = Field(
        default=20, ge=1, le=MAX_PAGE_LIMIT, description="Maximum number of records to return"
    )
    offset: int = Field(default=0, ge=0, description="Number of records to skip")


class BrandListResponse(BaseModel):
    """Schema for paginated brand list response."""

    items: list[BrandResponse]
    total: int
    limit: int
    offset: int


# Product Schemas
class ProductCreate(BaseModel):
    """Schema for creating a product."""

    name: str = Field(..., description="Product name")
    category: str = Field(..., description="Product category")
    materials_composition: list[dict[str, Any]] = Field(
        ..., description="Materials composition with percentages"
    )
    manufacturing_processes: list[str] = Field(
        default_factory=list, description="Manufacturing processes"
    )


class ProductResponse(BaseModel):
    """Schema for product response."""

    id: UUID
    brand_id: UUID
    name: str
    category: str
    materials_composition: list[dict[str, Any]]
    manufacturing_processes: list[str]
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}


# Supply Chain Node Schemas
class SupplyChainNodeCreate(BaseModel):
    """Schema for creating a supply chain node."""

    role: str = Field(..., description="Node role (e.g., CutAndSew, FabricMill)")
    country: str = Field(..., description="ISO country code")
    tier_level: int = Field(..., gt=0, description="Tier level (1, 2, 3, etc.)")


class SupplyChainNodeResponse(BaseModel):
    """Schema for supply chain node response."""

    id: UUID
    brand_id: UUID
    role: str
    country: str
    tier_level: int
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}


# Criterion Schemas
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


# Rule Schemas
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


# Questionnaire Schemas
class QuestionnaireDefinitionCreate(BaseModel):
    """Schema for creating a questionnaire definition."""

    name: str = Field(..., description="Questionnaire name")
    form_schema: dict[str, Any] = Field(..., description="Form structure (JSON schema)")
    is_active: bool = Field(default=True, description="Active status")

    @field_validator("form_schema")
    @classmethod
    def validate_form_schema(cls, v: dict[str, Any]) -> dict[str, Any]:
        """Validate form schema structure."""
        if not isinstance(v, dict):
            raise ValueError("form_schema must be a dictionary")
        # Basic validation - ensure it has expected structure
        if "questions" not in v and not isinstance(v, list):
            # Allow both object and array formats
            if not isinstance(v, list):
                raise ValueError(
                    "form_schema must be a dictionary with 'questions' key or a list of questions"
                )
        return v


class QuestionnaireDefinitionResponse(BaseModel):
    """Schema for questionnaire definition response."""

    id: UUID
    name: str
    form_schema: dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}


class QuestionnaireListQuery(BaseModel):
    """Schema for questionnaire list query parameters."""

    is_active: bool | None = Field(None, description="Filter by active status")
    limit: int = Field(
        default=20, ge=1, le=MAX_PAGE_LIMIT, description="Maximum number of records to return"
    )
    offset: int = Field(default=0, ge=0, description="Number of records to skip")


class QuestionnaireListResponse(BaseModel):
    """Schema for paginated questionnaire list response."""

    items: list[QuestionnaireDefinitionResponse]
    total: int
    limit: int
    offset: int


# Audit Instance Schemas
class AuditInstanceCreate(BaseModel):
    """Schema for creating an audit instance."""

    brand_id: UUID = Field(..., description="Brand ID")
    questionnaire_definition_id: UUID = Field(..., description="Questionnaire definition ID")
    scoping_responses: dict[str, Any] = Field(..., description="Questionnaire answers")


class AuditInstanceUpdate(BaseModel):
    """Schema for updating an audit instance."""

    status: AuditInstanceStatus | None = Field(None, description="Audit status")
    overall_score: float | None = Field(
        None, ge=0, le=100, description="Overall audit score (0-100)"
    )


class AuditInstanceResponse(BaseModel):
    """Schema for audit instance response."""

    id: UUID
    brand_id: UUID
    questionnaire_definition_id: UUID
    status: AuditInstanceStatus
    scoping_responses: dict[str, Any]
    brand_context_snapshot: dict[str, Any]
    overall_score: float | None
    created_at: datetime
    updated_at: datetime | None

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


# Audit Item Schemas
class AuditItemResponse(BaseModel):
    """Schema for audit item response."""

    id: UUID
    audit_instance_id: UUID
    criteria_id: UUID
    triggered_by_rule_id: UUID
    status: AuditItemStatus
    auditor_comments: str | None
    created_at: datetime
    updated_at: datetime | None

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
