"""Audit workflows domain Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class RuleSource(BaseModel):
    """Rule source information for traceability."""

    rule_id: UUID = Field(..., alias="ruleId", serialization_alias="ruleId")
    rule_code: str = Field(..., alias="ruleCode", serialization_alias="ruleCode")
    rule_name: str = Field(..., alias="ruleName", serialization_alias="ruleName")
    rule_version: int = Field(..., alias="ruleVersion", serialization_alias="ruleVersion")

    model_config = {"populate_by_name": True}


class ClaimResponse(BaseModel):
    """Evidence claim in a workflow."""

    id: UUID
    evidence_claim_id: UUID = Field(..., alias="evidenceClaimId", serialization_alias="evidenceClaimId")
    evidence_claim_name: str = Field(..., alias="evidenceClaimName", serialization_alias="evidenceClaimName")
    evidence_claim_description: str | None = Field(
        None, alias="evidenceClaimDescription", serialization_alias="evidenceClaimDescription"
    )
    evidence_claim_category: str = Field(
        ..., alias="evidenceClaimCategory", serialization_alias="evidenceClaimCategory"
    )
    evidence_claim_type: str = Field(..., alias="evidenceClaimType", serialization_alias="evidenceClaimType")
    evidence_claim_weight: float = Field(
        ..., alias="evidenceClaimWeight", serialization_alias="evidenceClaimWeight"
    )
    required: bool
    sources: list[RuleSource]
    created_at: datetime = Field(..., alias="createdAt", serialization_alias="createdAt")
    updated_at: datetime | None = Field(None, alias="updatedAt", serialization_alias="updatedAt")

    model_config = {"from_attributes": True, "populate_by_name": True}

    @classmethod
    def model_validate(cls, obj, **kwargs):
        """Map snake_case model fields to camelCase API fields."""
        if hasattr(obj, "__dict__"):
            data = dict(obj.__dict__)
            # Map fields to camelCase
            field_mappings = {
                "evidence_claim_id": "evidenceClaimId",
                "evidence_claim_name": "evidenceClaimName",
                "evidence_claim_description": "evidenceClaimDescription",
                "evidence_claim_category": "evidenceClaimCategory",
                "evidence_claim_type": "evidenceClaimType",
                "evidence_claim_weight": "evidenceClaimWeight",
                "created_at": "createdAt",
                "updated_at": "updatedAt",
            }
            for old_key, new_key in field_mappings.items():
                if old_key in data:
                    data[new_key] = data.pop(old_key)
            return super().model_validate(data, **kwargs)
        return super().model_validate(obj, **kwargs)


class RuleMatchResponse(BaseModel):
    """Rule match result for a workflow generation."""

    rule_id: UUID = Field(..., alias="ruleId", serialization_alias="ruleId")
    rule_code: str = Field(..., alias="ruleCode", serialization_alias="ruleCode")
    rule_version: int = Field(..., alias="ruleVersion", serialization_alias="ruleVersion")
    matched: bool
    error: str | None
    evaluated_at: datetime = Field(..., alias="evaluatedAt", serialization_alias="evaluatedAt")

    model_config = {"from_attributes": True, "populate_by_name": True}

    @classmethod
    def model_validate(cls, obj, **kwargs):
        """Map snake_case model fields to camelCase API fields."""
        if hasattr(obj, "__dict__"):
            data = dict(obj.__dict__)
            # Map fields to camelCase
            if "rule_id" in data:
                data["ruleId"] = data.pop("rule_id")
            if "rule_code" in data:
                data["ruleCode"] = data.pop("rule_code")
            if "rule_version" in data:
                data["ruleVersion"] = data.pop("rule_version")
            if "evaluated_at" in data:
                data["evaluatedAt"] = data.pop("evaluated_at")
            return super().model_validate(data, **kwargs)
        return super().model_validate(obj, **kwargs)


class WorkflowResponse(BaseModel):
    """Audit workflow response."""

    id: UUID
    audit_id: UUID = Field(..., alias="auditId", serialization_alias="auditId")
    generation: int
    status: str
    generated_at: datetime = Field(..., alias="generatedAt", serialization_alias="generatedAt")
    engine_version: str = Field(..., alias="engineVersion", serialization_alias="engineVersion")
    claims: list[ClaimResponse] = Field(
        ..., alias="claims", serialization_alias="claims"
    )
    rule_matches: list[RuleMatchResponse] | None = Field(
        None, alias="ruleMatches", serialization_alias="ruleMatches"
    )
    created_at: datetime = Field(..., alias="createdAt", serialization_alias="createdAt")
    updated_at: datetime | None = Field(None, alias="updatedAt", serialization_alias="updatedAt")

    model_config = {"from_attributes": True, "populate_by_name": True}

    @classmethod
    def model_validate(cls, obj, **kwargs):
        """Map snake_case model fields to camelCase API fields."""
        if hasattr(obj, "__dict__"):
            data = dict(obj.__dict__)
            # Map fields to camelCase
            field_mappings = {
                "audit_id": "auditId",
                "generated_at": "generatedAt",
                "engine_version": "engineVersion",
                "claims": "claims",
                "rule_matches": "ruleMatches",
                "created_at": "createdAt",
                "updated_at": "updatedAt",
            }
            for old_key, new_key in field_mappings.items():
                if old_key in data:
                    data[new_key] = data.pop(old_key)
            return super().model_validate(data, **kwargs)
        return super().model_validate(obj, **kwargs)


class WorkflowSummary(BaseModel):
    """Lightweight workflow summary for list endpoints."""

    id: UUID
    audit_id: UUID = Field(..., alias="auditId", serialization_alias="auditId")
    generation: int
    status: str
    generated_at: datetime = Field(..., alias="generatedAt", serialization_alias="generatedAt")
    engine_version: str = Field(..., alias="engineVersion", serialization_alias="engineVersion")
    created_at: datetime = Field(..., alias="createdAt", serialization_alias="createdAt")
    updated_at: datetime | None = Field(None, alias="updatedAt", serialization_alias="updatedAt")

    model_config = {"from_attributes": True, "populate_by_name": True}

    @classmethod
    def model_validate(cls, obj, **kwargs):
        """Map snake_case model fields to camelCase API fields."""
        if hasattr(obj, "__dict__"):
            data = dict(obj.__dict__)
            field_mappings = {
                "audit_id": "auditId",
                "generated_at": "generatedAt",
                "engine_version": "engineVersion",
                "created_at": "createdAt",
                "updated_at": "updatedAt",
            }
            for old_key, new_key in field_mappings.items():
                if old_key in data:
                    data[new_key] = data.pop(old_key)
            return super().model_validate(data, **kwargs)
        return super().model_validate(obj, **kwargs)


class WorkflowListResponse(BaseModel):
    """Paginated list of workflows."""

    items: list[WorkflowSummary]
    total: int
    limit: int
    offset: int


class WorkflowGenerateResponse(BaseModel):
    """Response for workflow generation."""

    workflow_id: UUID = Field(..., alias="workflowId", serialization_alias="workflowId")
    audit_id: UUID = Field(..., alias="auditId", serialization_alias="auditId")
    generation: int
    generated_at: datetime = Field(..., alias="generatedAt", serialization_alias="generatedAt")
    required_claims_count: int = Field(
        ..., alias="requiredClaimsCount", serialization_alias="requiredClaimsCount"
    )
    matched_rules_count: int = Field(
        ..., alias="matchedRulesCount", serialization_alias="matchedRulesCount"
    )

    model_config = {"populate_by_name": True}

