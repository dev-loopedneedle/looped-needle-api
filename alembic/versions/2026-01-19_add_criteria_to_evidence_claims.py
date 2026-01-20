"""Add criteria field to evidence claims and remove category claim mapping.

Revision ID: 2026-01-19_add_criteria_to_evidence_claims
Revises: 2026-01-18_add_evidence_claim_dimension_and_workflow_scores
Create Date: 2026-01-19
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "68ec1279dbc2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add criteria array column to evidence_claims
    op.add_column(
        "evidence_claims",
        sa.Column("criteria", postgresql.ARRAY(sa.String()), nullable=False, server_default="{}"),
    )


def downgrade() -> None:
    op.drop_column("evidence_claims", "criteria")

