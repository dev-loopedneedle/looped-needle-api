"""merge_user_profiles_and_audits_heads

Revision ID: e523f0e49913
Revises: add_user_profiles, 5723a4bbd420
Create Date: 2026-01-04 21:52:27.641672

"""
from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = 'e523f0e49913'
down_revision: str | Sequence[str] | None = ('add_user_profiles', '5723a4bbd420')
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
