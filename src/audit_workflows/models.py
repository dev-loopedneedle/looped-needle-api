"""Audit workflows domain database models."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlmodel import Field, SQLModel


class AuditWorkflowStatus:
    GENERATED = "GENERATED"
    PROCESSING = "PROCESSING"
    PROCESSING_COMPLETE = "PROCESSING_COMPLETE"
    PROCESSING_FAILED = "PROCESSING_FAILED"


class AuditWorkflow(SQLModel, table=True):
    """Audit workflow model - represents an instance/workflow of an audit."""

    __tablename__ = "audit_workflows"
    __table_args__ = (
        CheckConstraint(
            "status IN ('GENERATED', 'PROCESSING', 'PROCESSING_COMPLETE', 'PROCESSING_FAILED')",
            name="audit_workflows_status_check",
        ),
        CheckConstraint(
            "certification IS NULL OR certification IN ('Bronze', 'Silver', 'Gold')",
            name="audit_workflows_certification_check",
        ),
    )

    id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(PostgresUUID(as_uuid=True), primary_key=True),
    )
    audit_id: UUID = Field(
        sa_column=Column(
            PostgresUUID(as_uuid=True),
            ForeignKey("audits.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        )
    )
    status: str = Field(
        default=AuditWorkflowStatus.GENERATED,
        sa_column=Column(String, nullable=False, server_default=AuditWorkflowStatus.GENERATED),
    )
    engine_version: str = Field(
        default="v1",
        sa_column=Column(String, nullable=False, server_default="v1"),
    )
    data_completeness: int | None = Field(default=None, sa_column=Column(Integer, nullable=True))
    category_scores: dict | None = Field(default=None, sa_column=Column(JSONB, nullable=True))
    overall_score: int | None = Field(
        default=None,
        sa_column=Column(Integer, nullable=True),
        description="Average percent of all category scores (0-100)",
    )
    certification: str | None = Field(
        default=None,
        sa_column=Column(String, nullable=True),
        description="Certification level: Bronze (>60%), Silver (>75%), Gold (>90%). Only awarded when data_completeness > 90",
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), index=True),
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )


class AuditWorkflowRuleMatch(SQLModel, table=True):
    """Rule evaluation result for a workflow."""

    __tablename__ = "audit_workflow_rule_matches"

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
    rule_id: UUID = Field(
        sa_column=Column(
            PostgresUUID(as_uuid=True),
            ForeignKey("rules.id", ondelete="RESTRICT"),
            nullable=False,
        )
    )
    rule_code: str = Field(sa_column=Column(String, nullable=False))
    rule_version: int = Field(sa_column=Column(Integer, nullable=False))
    matched: bool = Field(sa_column=Column(Boolean, nullable=False))
    error: str | None = Field(default=None, sa_column=Column(String, nullable=True))
    evaluated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class AuditWorkflowClaim(SQLModel, table=True):
    """Evidence claim for a workflow."""

    __tablename__ = "audit_workflow_claims"
    __table_args__ = (
        CheckConstraint(
            "status IN ('REQUIRED', 'SATISFIED')",
            name="audit_workflow_claims_status_check",
        ),
        Index(
            "uq_audit_workflow_claim",
            "audit_workflow_id",
            "evidence_claim_id",
            unique=True,
        ),
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
    evidence_claim_id: UUID = Field(
        sa_column=Column(
            PostgresUUID(as_uuid=True),
            ForeignKey("evidence_claims.id", ondelete="RESTRICT"),
            nullable=False,
        )
    )
    status: str = Field(
        default="REQUIRED",
        sa_column=Column(String, nullable=False, server_default="REQUIRED"),
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True),
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )


class AuditWorkflowClaimSource(SQLModel, table=True):
    """Sources (rules) that require a claim."""

    __tablename__ = "audit_workflow_claim_sources"
    __table_args__ = (
        Index(
            "pk_claim_source",
            "audit_workflow_claim_id",
            "rule_id",
            unique=True,
        ),
    )

    audit_workflow_claim_id: UUID = Field(
        sa_column=Column(
            PostgresUUID(as_uuid=True),
            ForeignKey("audit_workflow_claims.id", ondelete="CASCADE"),
            primary_key=True,
        )
    )
    rule_id: UUID = Field(
        sa_column=Column(
            PostgresUUID(as_uuid=True),
            ForeignKey("rules.id", ondelete="RESTRICT"),
            primary_key=True,
        )
    )
    rule_code: str = Field(sa_column=Column(String, nullable=False))
    rule_version: int = Field(sa_column=Column(Integer, nullable=False))
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True),
    )
