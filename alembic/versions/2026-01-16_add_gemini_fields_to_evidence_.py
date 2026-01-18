"""add_gemini_fields_to_evidence_submissions

Revision ID: 94b08b71e699
Revises: remove_superseded
Create Date: 2026-01-16 12:53:10.871222

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '94b08b71e699'
down_revision: Union[str, Sequence[str], None] = 'remove_superseded'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add gemini fields to evidence_submissions table."""
    # Add gemini_evaluation_response column (JSONB)
    op.add_column(
        "evidence_submissions",
        sa.Column(
            "gemini_evaluation_response",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )

    # Add overall_verdict_reason column (Text)
    op.add_column(
        "evidence_submissions",
        sa.Column(
            "overall_verdict_reason",
            sa.Text(),
            nullable=True,
        ),
    )

    # Create GIN index for gemini_evaluation_response JSONB column
    op.create_index(
        "idx_evidence_submissions_gemini_evaluation_response_gin",
        "evidence_submissions",
        ["gemini_evaluation_response"],
        postgresql_using="gin",
    )


def downgrade() -> None:
    """Remove gemini fields from evidence_submissions table."""
    # Drop GIN index
    op.drop_index(
        "idx_evidence_submissions_gemini_evaluation_response_gin",
        table_name="evidence_submissions",
        postgresql_using="gin",
    )

    # Drop columns
    op.drop_column("evidence_submissions", "overall_verdict_reason")
    op.drop_column("evidence_submissions", "gemini_evaluation_response")
