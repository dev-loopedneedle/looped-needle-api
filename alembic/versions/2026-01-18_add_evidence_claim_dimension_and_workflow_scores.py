"""Add evidence claim dimension and workflow scoring fields.

Revision ID: 2026-01-18_add_evidence_claim_dimension_and_workflow_scores
Revises: 2026-01-18_rename_workflow_claims_tables_and_
Create Date: 2026-01-18
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "2026-01-18_add_evidence_claim_dimension_and_workflow_scores"
down_revision = "2026-01-18_rename_workflow_claims_tables_and_"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add dimension to evidence_claims
    op.add_column("evidence_claims", sa.Column("dimension", sa.String(), nullable=True))

    # Backfill dimension based on existing category
    op.execute(
        """
        UPDATE evidence_claims
        SET dimension = CASE
            WHEN category IN ('ENVIRONMENT', 'SUSTAINABILITY') THEN 'ENVIRONMENTAL'
            WHEN category = 'SOCIAL' THEN 'SOCIAL'
            WHEN category IN ('TRACEABILITY', 'GOVERNANCE') THEN 'TRANSPARENCY'
            ELSE 'TRANSPARENCY'
        END
        """
    )

    op.alter_column("evidence_claims", "dimension", nullable=False)

    # Add workflow scoring fields
    op.add_column("audit_workflows", sa.Column("data_completeness", sa.Integer(), nullable=True))
    op.add_column(
        "audit_workflows",
        sa.Column("dimension_scores", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("audit_workflows", "dimension_scores")
    op.drop_column("audit_workflows", "data_completeness")
    op.drop_column("evidence_claims", "dimension")

