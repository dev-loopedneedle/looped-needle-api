"""create waitlist table

Revision ID: create_waitlist_table
Revises: 001_create_audit_table
Create Date: 2026-01-05

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "create_waitlist_table"
down_revision: str | None = "b486d5c74821"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema - create waitlist_entries table."""
    op.create_table(
        "waitlist_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True, index=True),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            index=True,
        ),
    )
    # Create unique constraint explicitly
    op.create_unique_constraint("waitlist_entries_email_key", "waitlist_entries", ["email"])


def downgrade() -> None:
    """Downgrade schema - drop waitlist_entries table."""
    op.drop_constraint("waitlist_entries_email_key", "waitlist_entries", type_="unique")
    op.drop_index("waitlist_entries_email_idx", table_name="waitlist_entries")
    op.drop_index("waitlist_entries_created_at_idx", table_name="waitlist_entries")
    op.drop_table("waitlist_entries")

