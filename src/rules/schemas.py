"""Pydantic schemas for the rules domain."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from src.rules.constants import (
    EvidenceClaimCategory,
    EvidenceClaimType,
    RuleState,
)


def _convert_snake_to_camel(data: dict[str, Any]) -> dict[str, Any]:
    """Convert snake_case keys to camelCase for API responses."""
    field_mappings = {
        "created_at": "createdAt",
        "updated_at": "updatedAt",
        "published_at": "publishedAt",
        "disabled_at": "disabledAt",
        "condition_tree": "conditionTree",
        "evidence_claims": "evidenceClaims",
    }
    result = {}
    for key, value in data.items():
        # Map snake_case to camelCase if mapping exists
        mapped_key = field_mappings.get(key, key)
        # Handle nested lists (e.g., evidence_claims)
        if isinstance(value, list) and value and isinstance(value[0], dict):
            result[mapped_key] = [_convert_snake_to_camel(item) for item in value]
        else:
            result[mapped_key] = value
    return result


class EvidenceClaimCreate(BaseModel):
    name: str
    description: str | None = None
    category: EvidenceClaimCategory
    type: EvidenceClaimType
    weight: float = Field(ge=0, le=1)


class EvidenceClaimResponse(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    category: EvidenceClaimCategory
    type: EvidenceClaimType
    weight: float
    required: bool = Field(default=True, alias="required", serialization_alias="required")
    created_at: datetime = Field(..., alias="createdAt", serialization_alias="createdAt")
    updated_at: datetime | None = Field(None, alias="updatedAt", serialization_alias="updatedAt")

    model_config = {"from_attributes": True, "populate_by_name": True}

    @classmethod
    def model_validate(cls, obj: Any, **kwargs: Any) -> "EvidenceClaimResponse":
        """Map snake_case model fields to camelCase API fields."""
        if hasattr(obj, "__dict__"):
            data = dict(obj.__dict__)
            converted_data = _convert_snake_to_camel(data)
            return super().model_validate(converted_data, **kwargs)
        return super().model_validate(obj, **kwargs)


class RuleCreate(BaseModel):
    name: str
    code: str
    description: str | None = None
    conditionTree: dict = Field(..., alias="conditionTree")
    evidence_claims: list[EvidenceClaimCreate] = Field(
        default_factory=list, alias="evidenceClaims", serialization_alias="evidenceClaims"
    )
    evidence_claim_ids: list[UUID] = Field(
        default_factory=list, alias="evidenceClaimIds", serialization_alias="evidenceClaimIds"
    )

    @field_validator("code")
    @classmethod
    def strip_code(cls, v: str) -> str:
        return v.strip()

    model_config = {"populate_by_name": True}


class RuleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    conditionTree: dict | None = Field(None, alias="conditionTree")
    evidence_claims: list[EvidenceClaimCreate] | None = Field(
        None, alias="evidenceClaims", serialization_alias="evidenceClaims"
    )
    evidence_claim_ids: list[UUID] | None = Field(
        None, alias="evidenceClaimIds", serialization_alias="evidenceClaimIds"
    )

    model_config = {"populate_by_name": True}


class RuleResponse(BaseModel):
    id: UUID
    code: str
    version: int
    name: str
    description: str | None = None
    state: RuleState
    conditionTree: dict = Field(..., alias="conditionTree", serialization_alias="conditionTree")
    created_at: datetime = Field(..., alias="createdAt", serialization_alias="createdAt")
    updated_at: datetime | None = Field(None, alias="updatedAt", serialization_alias="updatedAt")
    published_at: datetime | None = Field(
        None, alias="publishedAt", serialization_alias="publishedAt"
    )
    disabled_at: datetime | None = Field(None, alias="disabledAt", serialization_alias="disabledAt")
    evidence_claims: list[EvidenceClaimResponse] = Field(
        default_factory=list, alias="evidenceClaims", serialization_alias="evidenceClaims"
    )

    model_config = {"from_attributes": True, "populate_by_name": True}

    @classmethod
    def model_validate(cls, obj: Any, **kwargs: Any) -> "RuleResponse":
        """Map snake_case model fields to camelCase API fields."""
        if hasattr(obj, "__dict__"):
            data = dict(obj.__dict__)
            converted_data = _convert_snake_to_camel(data)
            return super().model_validate(converted_data, **kwargs)
        return super().model_validate(obj, **kwargs)


class RuleListResponse(BaseModel):
    items: list[RuleResponse]
    total: int
    limit: int
    offset: int


class EvidenceClaimListResponse(BaseModel):
    items: list[EvidenceClaimResponse]
    total: int
    limit: int
    offset: int


class RulePreviewRequest(BaseModel):
    conditionTree: dict = Field(..., alias="conditionTree")
    audit_data: dict = Field(..., alias="auditData", serialization_alias="auditData")
    evidence_claim_ids: list[UUID] | None = Field(
        None, alias="evidenceClaimIds", serialization_alias="evidenceClaimIds"
    )

    model_config = {"populate_by_name": True}


class RulePreviewResponse(BaseModel):
    valid: bool
    matched: bool | None = None
    errors: list[str] = Field(default_factory=list)
