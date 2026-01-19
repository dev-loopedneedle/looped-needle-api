"""Rename dimension_scores to category_scores.

Revision ID: 68ec1279dbc2
Revises: 54f139dfc375
Create Date: 2026-01-18
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "68ec1279dbc2"
down_revision = "54f139dfc375"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Rename dimension_scores column to category_scores
    op.alter_column(
        "audit_workflows",
        "dimension_scores",
        new_column_name="category_scores",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        existing_nullable=True,
    )


def downgrade() -> None:
    # Rename category_scores column back to dimension_scores
    op.alter_column(
        "audit_workflows",
        "category_scores",
        new_column_name="dimension_scores",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        existing_nullable=True,
    )

