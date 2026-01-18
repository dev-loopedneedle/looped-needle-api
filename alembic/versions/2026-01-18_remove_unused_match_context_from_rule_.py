"""remove_unused_match_context_from_rule_matches

Revision ID: b2bbee4b9474
Revises: 23828b5d519b
Create Date: 2026-01-18 12:30:05.818132

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'b2bbee4b9474'
down_revision: Union[str, Sequence[str], None] = '23828b5d519b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove unused match_context column from audit_workflow_rule_matches."""
    op.drop_column("audit_workflow_rule_matches", "match_context")


def downgrade() -> None:
    """Restore match_context column."""
    op.add_column(
        "audit_workflow_rule_matches",
        sa.Column("match_context", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
