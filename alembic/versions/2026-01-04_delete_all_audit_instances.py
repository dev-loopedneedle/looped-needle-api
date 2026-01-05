"""delete_all_audit_instances

Revision ID: a99bc4884c06
Revises: e523f0e49913
Create Date: 2026-01-04 22:00:00.000000

"""
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a99bc4884c06"
down_revision: str | Sequence[str] | None = "e523f0e49913"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema - delete all audit instances and audit items."""
    # Delete all audit items first (due to foreign key constraint)
    op.execute("DELETE FROM audit_items")

    # Delete all audit instances
    op.execute("DELETE FROM audit_instances")


def downgrade() -> None:
    """Downgrade schema - cannot restore deleted data."""
    pass
