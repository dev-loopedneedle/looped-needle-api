"""add_required_field_to_rule_evidence_claims

Revision ID: 648c451a9d18
Revises: 20260106_rules_engine
Create Date: 2026-01-08 19:08:23.562485

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '648c451a9d18'
down_revision: Union[str, Sequence[str], None] = '20260106_rules_engine'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add required column to rule_evidence_claims table
    op.add_column(
        "rule_evidence_claims",
        sa.Column("required", sa.Boolean(), nullable=False, server_default="true"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Remove required column from rule_evidence_claims table
    op.drop_column("rule_evidence_claims", "required")
