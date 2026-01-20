"""Rules domain database models."""

from __future__ import annotations

from datetime import UTC, datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    PrimaryKeyConstraint,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, NUMERIC
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlmodel import Field, SQLModel

from src.rules.constants import (
    EvidenceClaimCategory,
    EvidenceClaimType,
    RuleState,
)


class Rule(SQLModel, table=True):
    """Rule definition with versioning."""

    __tablename__ = "rules"
    __table_args__ = (
        UniqueConstraint("code", "version", name="uq_rules_code_version"),
        Index("idx_rules_code", "code"),
        CheckConstraint(
            "state IN ('DRAFT', 'PUBLISHED', 'DISABLED')",
            name="rules_state_check",
        ),
    )

    id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(PostgresUUID(as_uuid=True), primary_key=True),
    )
    code: str = Field(
        sa_column=Column(String, nullable=False, index=True)
    )  # stable identifier across versions
    version: int = Field(sa_column=Column(Integer, nullable=False, default=1))
    name: str = Field(sa_column=Column(String, nullable=False))
    description: str | None = Field(default=None, sa_column=Column(String, nullable=True))
    state: RuleState = Field(
        default=RuleState.DRAFT,
        sa_column=Column(String, nullable=False, server_default=RuleState.DRAFT.value),
    )
    condition_tree: dict = Field(sa_column=Column(JSONB, nullable=False))
    created_by_user_profile_id: UUID | None = Field(
        default=None,
        sa_column=Column(
            PostgresUUID(as_uuid=True),
            ForeignKey("user_profiles.id", ondelete="RESTRICT"),
            nullable=True,
        ),
    )
    published_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    disabled_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True),
    )
    updated_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    replaces_rule_id: UUID | None = Field(
        default=None,
        sa_column=Column(
            PostgresUUID(as_uuid=True),
            ForeignKey("rules.id", ondelete="RESTRICT"),
            nullable=True,
        ),
    )

    # Relationship to evidence claims through join table


class EvidenceClaim(SQLModel, table=True):
    """Evidence requirement definition."""

    __tablename__ = "evidence_claims"
    __table_args__ = (
        CheckConstraint("weight >= 0 AND weight <= 1", name="evidence_claims_weight_check"),
    )

    id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(PostgresUUID(as_uuid=True), primary_key=True),
    )
    name: str = Field(sa_column=Column(String, nullable=False))
    description: str | None = Field(default=None, sa_column=Column(String, nullable=True))
    category: EvidenceClaimCategory = Field(sa_column=Column(String, nullable=False))
    type: EvidenceClaimType = Field(sa_column=Column(String, nullable=False))
    weight: float = Field(
        sa_column=Column(NUMERIC(precision=5, scale=4), nullable=False, default=0)
    )
    criteria: list[str] = Field(
        default_factory=list,
        sa_column=Column(ARRAY(String), nullable=False, server_default="{}"),
    )
    created_by_user_profile_id: UUID | None = Field(
        default=None,
        sa_column=Column(
            PostgresUUID(as_uuid=True),
            ForeignKey("user_profiles.id", ondelete="RESTRICT"),
            nullable=True,
        ),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True),
    )
    updated_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )


class RuleEvidenceClaim(SQLModel, table=True):
    """Join between rules and evidence claims."""

    __tablename__ = "rule_evidence_claims"
    __table_args__ = (PrimaryKeyConstraint("rule_id", "evidence_claim_id", name="pk_rule_claim"),)

    rule_id: UUID = Field(
        sa_column=Column(
            PostgresUUID(as_uuid=True),
            ForeignKey("rules.id", ondelete="CASCADE"),
            nullable=False,
        )
    )
    evidence_claim_id: UUID = Field(
        sa_column=Column(
            PostgresUUID(as_uuid=True),
            ForeignKey("evidence_claims.id", ondelete="RESTRICT"),
            nullable=False,
        )
    )
    sort_order: int | None = Field(default=None, sa_column=Column(Integer, nullable=True))
    required: bool = Field(
        default=True, sa_column=Column(Boolean, nullable=False, server_default="true")
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True),
    )
