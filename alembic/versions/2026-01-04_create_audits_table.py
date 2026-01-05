"""create_audits_table

Revision ID: ec5a1872c0d9
Revises: 6b9e85ea4cd3
Create Date: 2026-01-04 20:15:26.065923

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ec5a1872c0d9"
down_revision: str | Sequence[str] | None = "6b9e85ea4cd3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema - create audits table."""
    op.create_table(
        "audits",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("brand_id", sa.String(length=255), nullable=False, index=True),
        sa.Column("status", sa.String(), nullable=False, server_default="DRAFT", index=True),
        sa.Column("audit_data", postgresql.JSONB(), nullable=False),
        sa.Column("certification_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), index=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("certified_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('DRAFT', 'PUBLISHED')",
            name="audits_status_check",
        ),
        sa.CheckConstraint(
            "certification_score IS NULL OR (certification_score >= 0 AND certification_score <= 100)",
            name="audits_certification_score_check",
        ),
    )
    # Create GIN index for JSONB audit_data column
    op.create_index(
        "idx_audits_audit_data_gin",
        "audits",
        ["audit_data"],
        postgresql_using="gin",
    )


def downgrade() -> None:
    """Downgrade schema - drop audits table."""
    op.drop_index("idx_audits_audit_data_gin", table_name="audits")
    op.drop_table("audits")
