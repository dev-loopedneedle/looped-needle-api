"""Audits domain database models."""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlmodel import Field, SQLModel


class AuditStatus:
    """Audit status constants."""

    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"


class Audit(SQLModel, table=True):
    """Audit model."""

    __tablename__ = "audits"

    id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(PostgresUUID(as_uuid=True), primary_key=True),
    )
    brand_id: UUID = Field(
        sa_column=Column(
            PostgresUUID(as_uuid=True),
            ForeignKey("brands.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        )
    )
    status: str = Field(
        default=AuditStatus.DRAFT,
        sa_column=Column(String, nullable=False, server_default="DRAFT", index=True),
    )
    audit_data: dict[str, Any] = Field(
        default_factory=dict, sa_column=Column(JSONB, nullable=False)
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), index=True),
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )

    __table_args__ = (
        Index(
            "idx_audits_audit_data_gin",
            "audit_data",
            postgresql_using="gin",
        ),
        CheckConstraint(
            "status IN ('DRAFT', 'PUBLISHED')",
            name="audits_status_check",
        ),
    )
