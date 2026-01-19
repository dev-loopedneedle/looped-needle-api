"""Remove dimension column from evidence_claims.

Revision ID: 54f139dfc375
Revises: ba5e31880a38
Create Date: 2026-01-18
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "54f139dfc375"
down_revision = "ba5e31880a38"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop the dimension column from evidence_claims
    op.drop_column("evidence_claims", "dimension")


def downgrade() -> None:
    # Add back the dimension column
    op.add_column(
        "evidence_claims",
        sa.Column("dimension", sa.String(), nullable=False, server_default="TRANSPARENCY"),
    )

