"""add_required_to_workflow_claims

Revision ID: add_required_workflow_claims
Revises: 6303a865bd4a
Create Date: 2026-01-09 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "add_required_workflow_claims"
down_revision: Union[str, Sequence[str], None] = "6303a865bd4a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add required boolean column to audit_workflow_required_claims."""
    # Add required column (nullable first, default to True for existing rows)
    op.add_column(
        "audit_workflow_required_claims",
        sa.Column("required", sa.Boolean(), nullable=True, server_default="true"),
    )
    
    # Set all existing rows to required=True (they were all required before)
    op.execute("UPDATE audit_workflow_required_claims SET required = true WHERE required IS NULL")
    
    # Make required NOT NULL
    op.alter_column("audit_workflow_required_claims", "required", nullable=False, server_default="true")


def downgrade() -> None:
    """Remove required column from audit_workflow_required_claims."""
    op.drop_column("audit_workflow_required_claims", "required")

