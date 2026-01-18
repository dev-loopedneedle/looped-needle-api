"""remove_workflow_generation_and_generated_at_columns

Revision ID: 23828b5d519b
Revises: 447251e925ce
Create Date: 2026-01-18 12:08:10.027609

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '23828b5d519b'
down_revision: Union[str, Sequence[str], None] = '447251e925ce'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove generation and generated_at columns from audit_workflows."""
    # Drop the unique index that uses generation
    op.drop_index("idx_audit_workflows_audit_generation", table_name="audit_workflows")
    
    # Drop the columns (using original names since rename migration hasn't run)
    op.drop_column("audit_workflows", "generated_at")
    op.drop_column("audit_workflows", "generation")


def downgrade() -> None:
    """Restore generation and generated_at columns."""
    # Add columns back
    op.add_column(
        "audit_workflows",
        sa.Column(
            "generation",
            sa.Integer(),
            nullable=False,
            server_default="1",
        ),
    )
    op.add_column(
        "audit_workflows",
        sa.Column(
            "generated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    
    # Recreate the unique index
    op.create_index(
        "idx_audit_workflows_audit_generation",
        "audit_workflows",
        ["audit_id", "generation"],
        unique=True,
    )
