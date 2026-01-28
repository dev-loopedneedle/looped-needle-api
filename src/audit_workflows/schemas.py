"""Audit workflows domain Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from src.evidence_submissions.schemas import EvidenceEvaluationSummary


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
    evidence_claim_id: UUID = Field(
        ..., alias="evidenceClaimId", serialization_alias="evidenceClaimId"
    )
    evidence_claim_name: str = Field(
        ..., alias="evidenceClaimName", serialization_alias="evidenceClaimName"
    )
    evidence_claim_description: str | None = Field(
        None, alias="evidenceClaimDescription", serialization_alias="evidenceClaimDescription"
    )
    evidence_claim_category: str = Field(
        ..., alias="evidenceClaimCategory", serialization_alias="evidenceClaimCategory"
    )
    evidence_claim_type: str = Field(
        ..., alias="evidenceClaimType", serialization_alias="evidenceClaimType"
    )
    evidence_claim_weight: float = Field(
        ..., alias="evidenceClaimWeight", serialization_alias="evidenceClaimWeight"
    )
    sources: list[RuleSource]
    created_at: datetime = Field(..., alias="createdAt", serialization_alias="createdAt")
    updated_at: datetime | None = Field(None, alias="updatedAt", serialization_alias="updatedAt")

    model_config = {"from_attributes": True, "populate_by_name": True}


class RuleMatchResponse(BaseModel):
    """Rule match result for a workflow generation."""

    rule_id: UUID = Field(..., alias="ruleId", serialization_alias="ruleId")
    rule_code: str = Field(..., alias="ruleCode", serialization_alias="ruleCode")
    rule_version: int = Field(..., alias="ruleVersion", serialization_alias="ruleVersion")
    matched: bool
    error: str | None
    evaluated_at: datetime = Field(..., alias="evaluatedAt", serialization_alias="evaluatedAt")

    model_config = {"from_attributes": True, "populate_by_name": True}


class WorkflowResponse(BaseModel):
    """Audit workflow response."""

    id: UUID
    audit_id: UUID = Field(..., alias="auditId", serialization_alias="auditId")
    status: str
    engine_version: str = Field(..., alias="engineVersion", serialization_alias="engineVersion")
    data_completeness: int | None = Field(
        None, alias="dataCompleteness", serialization_alias="dataCompleteness"
    )
    category_scores: dict | None = Field(
        None, alias="categoryScores", serialization_alias="categoryScores"
    )
    overall_score: int | None = Field(
        None,
        ge=0,
        alias="overallScore",
        serialization_alias="overallScore",
        description="Average percent of all category scores (0-100)",
    )
    certification: str | None = Field(
        None,
        alias="certification",
        serialization_alias="certification",
        description="Certification level: Bronze (>60%), Silver (>75%), Gold (>90%). Only awarded when data_completeness > 90",
    )

    @field_validator("overall_score", mode="before")
    @classmethod
    def validate_overall_score(cls, v: int | None) -> int | None:
        """Validate and clamp overall_score to 0-100 range.

        Handles legacy workflows with incorrect scores (e.g., 10000 from old buggy calculation).
        Values > 100 are set to None to trigger recalculation.
        """
        if v is None:
            return None
        if v > 100:
            # Legacy buggy calculation - set to None to trigger recalculation
            return None
        if v < 0:
            return 0
        return v

    claims: list[ClaimResponse] = Field(..., alias="claims", serialization_alias="claims")
    rule_matches: list[RuleMatchResponse] | None = Field(
        None, alias="ruleMatches", serialization_alias="ruleMatches"
    )
    evidence_evaluations: list[EvidenceEvaluationSummary] | None = Field(
        None, alias="evidenceEvaluations", serialization_alias="evidenceEvaluations"
    )
    created_at: datetime = Field(..., alias="createdAt", serialization_alias="createdAt")
    updated_at: datetime | None = Field(None, alias="updatedAt", serialization_alias="updatedAt")

    model_config = {"from_attributes": True, "populate_by_name": True}


class WorkflowSummary(BaseModel):
    """Lightweight workflow summary for list endpoints."""

    id: UUID
    audit_id: UUID = Field(..., alias="auditId", serialization_alias="auditId")
    status: str
    engine_version: str = Field(..., alias="engineVersion", serialization_alias="engineVersion")
    data_completeness: int | None = Field(
        None, alias="dataCompleteness", serialization_alias="dataCompleteness"
    )
    category_scores: dict | None = Field(
        None, alias="categoryScores", serialization_alias="categoryScores"
    )
    overall_score: int | None = Field(
        None,
        ge=0,
        alias="overallScore",
        serialization_alias="overallScore",
        description="Average percent of all category scores (0-100)",
    )

    @field_validator("overall_score", mode="before")
    @classmethod
    def validate_overall_score(cls, v: int | None) -> int | None:
        """Validate and clamp overall_score to 0-100 range.

        Handles legacy workflows with incorrect scores (e.g., 10000 from old buggy calculation).
        Values > 100 are set to None to trigger recalculation.
        """
        if v is None:
            return None
        if v > 100:
            # Legacy buggy calculation - set to None to trigger recalculation
            return None
        if v < 0:
            return 0
        return v

    certification: str | None = Field(
        None,
        alias="certification",
        serialization_alias="certification",
        description="Certification level: Bronze (>60%), Silver (>75%), Gold (>90%). Only awarded when data_completeness > 90",
    )
    created_at: datetime = Field(..., alias="createdAt", serialization_alias="createdAt")
    updated_at: datetime | None = Field(None, alias="updatedAt", serialization_alias="updatedAt")

    model_config = {"from_attributes": True, "populate_by_name": True}


class WorkflowListResponse(BaseModel):
    """Paginated list of workflows."""

    items: list[WorkflowSummary]
    total: int
    limit: int
    offset: int


class SubmissionFileInfo(BaseModel):
    """File information for workflow submission."""

    claim_id: UUID = Field(..., alias="claimId")
    file_path: str = Field(..., alias="filePath")
    file_name: str = Field(..., alias="fileName")
    file_size: int | None = Field(None, alias="fileSize")
    mime_type: str | None = Field(None, alias="mimeType")

    model_config = {"populate_by_name": True}


class WorkflowSubmissionRequest(BaseModel):
    """Request to submit workflow with evidence files."""

    submissions: list[SubmissionFileInfo]

    model_config = {"populate_by_name": True}


class WorkflowSubmissionResponse(BaseModel):
    """Response for workflow submission."""

    workflow_id: UUID = Field(..., alias="workflowId", serialization_alias="workflowId")
    status: str
    submission_ids: list[UUID] = Field(
        ..., alias="submissionIds", serialization_alias="submissionIds"
    )
    message: str

    model_config = {"populate_by_name": True}
