"""Evidence submissions domain Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class EvaluationResult(BaseModel):
    """Evaluation result for evidence submission."""

    match_decision: str | None = Field(None, alias="matchDecision", serialization_alias="matchDecision")
    confidence_score: int | None = Field(None, alias="confidenceScore", serialization_alias="confidenceScore")
    evaluation_reasons: dict | None = Field(None, alias="evaluationReasons", serialization_alias="evaluationReasons")
    document_type_detected: str | None = Field(
        None, alias="documentTypeDetected", serialization_alias="documentTypeDetected"
    )
    category_detected: str | None = Field(None, alias="categoryDetected", serialization_alias="categoryDetected")

    model_config = {"populate_by_name": True}


class EvidenceSubmissionResponse(BaseModel):
    """Evidence submission response for listing."""

    id: UUID
    audit_workflow_id: UUID = Field(..., alias="auditWorkflowId", serialization_alias="auditWorkflowId")
    audit_workflow_claim_id: UUID = Field(
        ..., alias="auditWorkflowClaimId", serialization_alias="auditWorkflowClaimId"
    )
    file_name: str = Field(..., alias="fileName", serialization_alias="fileName")
    file_size: int | None = Field(None, alias="fileSize", serialization_alias="fileSize")
    mime_type: str | None = Field(None, alias="mimeType", serialization_alias="mimeType")
    status: str
    match_decision: str | None = Field(None, alias="matchDecision", serialization_alias="matchDecision")
    confidence_score: int | None = Field(None, alias="confidenceScore", serialization_alias="confidenceScore")
    created_at: datetime = Field(..., alias="createdAt", serialization_alias="createdAt")
    processing_completed_at: datetime | None = Field(
        None, alias="processingCompletedAt", serialization_alias="processingCompletedAt"
    )

    model_config = {"from_attributes": True, "populate_by_name": True}


class EvidenceEvaluationSummary(BaseModel):
    """Summary of evidence evaluation for workflow response."""

    submission_id: UUID = Field(..., alias="submissionId", serialization_alias="submissionId")
    status: str
    overall_verdict: str | None = Field(None, alias="overallVerdict", serialization_alias="overallVerdict")
    confidence_score: int | None = Field(None, alias="confidenceScore", serialization_alias="confidenceScore")
    file_name: str = Field(..., alias="fileName", serialization_alias="fileName")

    model_config = {"populate_by_name": True}


class EvidenceSubmissionDetailResponse(BaseModel):
    """Detailed evidence submission response."""

    id: UUID
    audit_workflow_id: UUID = Field(..., alias="auditWorkflowId", serialization_alias="auditWorkflowId")
    audit_workflow_claim_id: UUID = Field(
        ..., alias="auditWorkflowClaimId", serialization_alias="auditWorkflowClaimId"
    )
    file_path: str = Field(..., alias="filePath", serialization_alias="filePath")
    file_name: str = Field(..., alias="fileName", serialization_alias="fileName")
    file_size: int | None = Field(None, alias="fileSize", serialization_alias="fileSize")
    mime_type: str | None = Field(None, alias="mimeType", serialization_alias="mimeType")
    status: str
    extracted_text: str | None = Field(None, alias="extractedText", serialization_alias="extractedText")
    extracted_fields: dict | None = Field(None, alias="extractedFields", serialization_alias="extractedFields")
    match_decision: str | None = Field(None, alias="matchDecision", serialization_alias="matchDecision")
    confidence_score: int | None = Field(None, alias="confidenceScore", serialization_alias="confidenceScore")
    overall_verdict_reason: str | None = Field(
        None, alias="overallVerdictReason", serialization_alias="overallVerdictReason"
    )
    evaluation_reasons: dict | None = Field(None, alias="evaluationReasons", serialization_alias="evaluationReasons")
    document_type_detected: str | None = Field(
        None, alias="documentTypeDetected", serialization_alias="documentTypeDetected"
    )
    category_detected: str | None = Field(None, alias="categoryDetected", serialization_alias="categoryDetected")
    error_message: str | None = Field(None, alias="errorMessage", serialization_alias="errorMessage")
    review_decision: str | None = Field(None, alias="reviewDecision", serialization_alias="reviewDecision")
    review_notes: str | None = Field(None, alias="reviewNotes", serialization_alias="reviewNotes")
    reviewed_at: datetime | None = Field(None, alias="reviewedAt", serialization_alias="reviewedAt")
    created_at: datetime = Field(..., alias="createdAt", serialization_alias="createdAt")
    processing_started_at: datetime | None = Field(
        None, alias="processingStartedAt", serialization_alias="processingStartedAt"
    )
    processing_completed_at: datetime | None = Field(
        None, alias="processingCompletedAt", serialization_alias="processingCompletedAt"
    )

    model_config = {"from_attributes": True, "populate_by_name": True}


class EvidenceEvaluationReportResponse(BaseModel):
    """Full Gemini evaluation report for admin (includes full gemini_evaluation_response)."""

    submission_id: UUID = Field(..., alias="submissionId", serialization_alias="submissionId")
    file_name: str = Field(..., alias="fileName", serialization_alias="fileName")
    status: str
    gemini_evaluation_response: dict | None = Field(
        None, alias="geminiEvaluationResponse", serialization_alias="geminiEvaluationResponse"
    )
    match_decision: str | None = Field(None, alias="matchDecision", serialization_alias="matchDecision")
    confidence_score: int | None = Field(None, alias="confidenceScore", serialization_alias="confidenceScore")
    overall_verdict_reason: str | None = Field(
        None, alias="overallVerdictReason", serialization_alias="overallVerdictReason"
    )
    processing_started_at: datetime | None = Field(
        None, alias="processingStartedAt", serialization_alias="processingStartedAt"
    )
    processing_completed_at: datetime | None = Field(
        None, alias="processingCompletedAt", serialization_alias="processingCompletedAt"
    )

    model_config = {"populate_by_name": True}


class UploadUrlRequest(BaseModel):
    """Request to generate upload URL."""

    claim_id: UUID = Field(..., alias="claimId")
    file_name: str = Field(..., alias="fileName")
    file_size: int = Field(..., alias="fileSize")
    mime_type: str = Field(..., alias="mimeType")
    previous_file_path: str | None = Field(None, alias="previousFilePath")

    model_config = {"populate_by_name": True}


class UploadUrlResponse(BaseModel):
    """Response with signed upload URL."""

    upload_url: str = Field(..., alias="uploadUrl", serialization_alias="uploadUrl")
    file_path: str = Field(..., alias="filePath", serialization_alias="filePath")
    expires_at: str = Field(..., alias="expiresAt", serialization_alias="expiresAt")

    model_config = {"populate_by_name": True}


class ResubmissionRequest(BaseModel):
    """Request to resubmit evidence."""

    file_path: str = Field(..., alias="filePath", serialization_alias="filePath")
    file_name: str = Field(..., alias="fileName", serialization_alias="fileName")
    file_size: int | None = Field(None, alias="fileSize", serialization_alias="fileSize")
    mime_type: str | None = Field(None, alias="mimeType", serialization_alias="mimeType")

    model_config = {"populate_by_name": True}


class ReviewRequest(BaseModel):
    """Request for admin review of submission."""

    decision: str = Field(..., description="Review decision: ACCEPTED or REJECTED")
    notes: str | None = Field(None, description="Optional review notes")

    model_config = {"populate_by_name": True}
