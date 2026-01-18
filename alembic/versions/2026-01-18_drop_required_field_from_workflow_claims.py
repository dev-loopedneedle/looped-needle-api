"""drop_required_field_from_workflow_claims

Revision ID: 43df249771c1
Revises: b2bbee4b9474
Create Date: 2026-01-18 12:38:56.310437

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '43df249771c1'
down_revision: Union[str, Sequence[str], None] = 'b2bbee4b9474'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Drop required column from audit_workflow_required_claims."""
    op.drop_column("audit_workflow_required_claims", "required")


def downgrade() -> None:
    """Restore required column."""
    op.add_column(
        "audit_workflow_required_claims",
        sa.Column("required", sa.Boolean(), nullable=False, server_default="true"),
    )
