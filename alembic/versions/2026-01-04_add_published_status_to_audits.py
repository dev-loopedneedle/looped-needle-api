"""add_published_status_to_audits

Revision ID: a1b2c3d4e5f6
Revises: ec5a1872c0d9
Create Date: 2026-01-04 21:00:00.000000

"""
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f90dc1934ab8"
down_revision: str | Sequence[str] | None = "ec5a1872c0d9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema - add PUBLISHED status to audits table constraint."""
    # Drop the existing constraint
    op.drop_constraint("audits_status_check", "audits", type_="check")
    # Add the new constraint with PUBLISHED status
    op.create_check_constraint(
        "audits_status_check",
        "audits",
        "status IN ('DRAFT', 'PUBLISHED')",
    )


def downgrade() -> None:
    """Downgrade schema - remove PUBLISHED status from constraint."""
    # Drop the constraint with PUBLISHED
    op.drop_constraint("audits_status_check", "audits", type_="check")
    # Recreate the original constraint without PUBLISHED
    op.create_check_constraint(
        "audits_status_check",
        "audits",
        "status IN ('DRAFT', 'REVIEWING', 'CERTIFIED', 'REJECTED')",
    )
