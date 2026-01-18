"""Evidence submissions domain database models."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlmodel import Field, SQLModel

from src.evidence_submissions.constants import SubmissionStatus


class EvidenceSubmission(SQLModel, table=True):
    """Evidence submission model - represents a user's evidence file submission."""

    __tablename__ = "evidence_submissions"
    __table_args__ = (
        CheckConstraint(
            "status IN ('PENDING_PROCESSING', 'PROCESSING', 'PROCESSING_COMPLETE', 'PROCESSING_FAILED', 'NEEDS_REVIEW', 'ACCEPTED', 'REJECTED')",
            name="evidence_submissions_status_check",
        ),
        CheckConstraint(
            "match_decision IN ('MATCH', 'NO_MATCH', 'NEEDS_REVIEW') OR match_decision IS NULL",
            name="evidence_submissions_match_decision_check",
        ),
        CheckConstraint(
            "confidence_score >= 0 AND confidence_score <= 100 OR confidence_score IS NULL",
            name="evidence_submissions_confidence_score_check",
        ),
        CheckConstraint(
            "review_decision IN ('ACCEPTED', 'REJECTED') OR review_decision IS NULL",
            name="evidence_submissions_review_decision_check",
        ),
        Index("idx_evidence_submissions_workflow_id", "audit_workflow_id"),
        Index("idx_evidence_submissions_claim_id", "audit_workflow_claim_id"),
        Index("idx_evidence_submissions_status", "status"),
        Index("idx_evidence_submissions_created_at", "created_at"),
        Index("idx_evidence_submissions_processing_started_at", "processing_started_at"),
        Index("idx_evidence_submissions_processing_completed_at", "processing_completed_at"),
    )

    id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(PostgresUUID(as_uuid=True), primary_key=True),
    )
    audit_workflow_id: UUID = Field(
        sa_column=Column(
            PostgresUUID(as_uuid=True),
            ForeignKey("audit_workflows.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    audit_workflow_claim_id: UUID = Field(
        sa_column=Column(
            PostgresUUID(as_uuid=True),
            ForeignKey("audit_workflow_claims.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        )
    )
    file_path: str = Field(sa_column=Column(Text, nullable=False))
    file_name: str = Field(sa_column=Column(Text, nullable=False))
    file_size: int | None = Field(default=None, sa_column=Column(BigInteger, nullable=True))
    mime_type: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    status: str = Field(
        default=SubmissionStatus.PENDING_PROCESSING,
        sa_column=Column(String, nullable=False, server_default=SubmissionStatus.PENDING_PROCESSING),
    )
    # Gemini evaluation results (replaces Document AI OCR)
    gemini_evaluation_response: dict | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True), description="Full Gemini evaluation response"
    )
    # Legacy fields (kept for backward compatibility, will be populated from gemini_evaluation_response)
    extracted_text: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    extracted_fields: dict | None = Field(default=None, sa_column=Column(JSONB, nullable=True))
    match_decision: str | None = Field(default=None, sa_column=Column(String, nullable=True))
    confidence_score: int | None = Field(default=None, sa_column=Column(Integer, nullable=True))
    overall_verdict_reason: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    evaluation_reasons: dict | None = Field(default=None, sa_column=Column(JSONB, nullable=True))
    document_type_detected: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    category_detected: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    error_message: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    review_decision: str | None = Field(default=None, sa_column=Column(String, nullable=True))
    review_notes: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    reviewed_by_user_profile_id: UUID | None = Field(
        default=None,
        sa_column=Column(
            PostgresUUID(as_uuid=True),
            ForeignKey("user_profiles.id", ondelete="RESTRICT"),
            nullable=True,
        ),
    )
    reviewed_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    processing_started_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True, index=True)
    )
    processing_completed_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True, index=True)
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True),
    )
    updated_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )

