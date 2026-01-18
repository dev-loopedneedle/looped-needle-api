"""remove_audit_data_snapshot_from_workflows

Revision ID: 447251e925ce
Revises: 94b08b71e699
Create Date: 2026-01-18 12:03:07.669006

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '447251e925ce'
down_revision: Union[str, Sequence[str], None] = '94b08b71e699'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove audit_data_snapshot column from audit_workflows table."""
    op.drop_column("audit_workflows", "audit_data_snapshot")


def downgrade() -> None:
    """Restore audit_data_snapshot column to audit_workflows table."""
    op.add_column(
        "audit_workflows",
        sa.Column(
            "audit_data_snapshot",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
    )
