"""Remove dimension field from evidence_claims.

Revision ID: b1c2d3e4f5g6
Revises: a1b2c3d4e5f6
Create Date: 2026-01-19
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b1c2d3e4f5g6"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop dimension column from evidence_claims
    op.drop_column("evidence_claims", "dimension")


def downgrade() -> None:
    # Add back dimension column (nullable first, then backfill and make not null)
    op.add_column("evidence_claims", sa.Column("dimension", sa.String(), nullable=True))
    
    # Backfill dimension based on category
    op.execute(
        """
        UPDATE evidence_claims
        SET dimension = CASE
            WHEN category = 'ENVIRONMENTAL' THEN 'ENVIRONMENTAL'
            WHEN category = 'SOCIAL' THEN 'SOCIAL'
            ELSE 'TRANSPARENCY'
        END
        """
    )
    
    op.alter_column("evidence_claims", "dimension", nullable=False)

