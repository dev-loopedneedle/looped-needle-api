"""restrict_audit_statuses_and_delete_all_audits

Revision ID: 5723a4bbd420
Revises: f90dc1934ab8
Create Date: 2026-01-04 22:00:00.000000

"""
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5723a4bbd420"
down_revision: str | Sequence[str] | None = "f90dc1934ab8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema - delete all audits and restrict status to DRAFT and PUBLISHED only."""
    # Delete all audits from the database
    op.execute("DELETE FROM audits")

    # Drop the existing constraint
    op.drop_constraint("audits_status_check", "audits", type_="check")
    # Add the new constraint with only DRAFT and PUBLISHED
    op.create_check_constraint(
        "audits_status_check",
        "audits",
        "status IN ('DRAFT', 'PUBLISHED')",
    )


def downgrade() -> None:
    """Downgrade schema - restore previous constraint (cannot restore deleted audits)."""
    # Drop the restricted constraint
    op.drop_constraint("audits_status_check", "audits", type_="check")
    # Recreate the previous constraint with all statuses
    op.create_check_constraint(
        "audits_status_check",
        "audits",
        "status IN ('DRAFT', 'REVIEWING', 'CERTIFIED', 'REJECTED', 'PUBLISHED')",
    )
