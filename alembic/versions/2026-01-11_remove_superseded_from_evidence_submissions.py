"""remove_superseded_from_evidence_submissions

Revision ID: remove_superseded_from_evidence_submissions
Revises: 2026-01-11_create_evidence_submissions_table
Create Date: 2026-01-11 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "remove_superseded"
down_revision: Union[str, Sequence[str], None] = "create_evidence_submissions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove SUPERSEDED status and superseded_by_submission_id column."""
    # Use raw SQL with IF EXISTS to handle cases where constraints/columns might not exist
    # This prevents transaction errors if the migration was partially run or the original migration
    # created the table without these elements
    
    # Drop foreign key constraint if it exists (using raw SQL to handle IF EXISTS)
    op.execute("""
        DO $$ 
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.table_constraints 
                WHERE constraint_name = 'evidence_submissions_superseded_by_submission_id_fkey'
                AND table_name = 'evidence_submissions'
            ) THEN
                ALTER TABLE evidence_submissions 
                DROP CONSTRAINT evidence_submissions_superseded_by_submission_id_fkey;
            END IF;
        END $$;
    """)
    
    # Drop the column if it exists
    op.execute("""
        DO $$ 
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'evidence_submissions' 
                AND column_name = 'superseded_by_submission_id'
            ) THEN
                ALTER TABLE evidence_submissions 
                DROP COLUMN superseded_by_submission_id;
            END IF;
        END $$;
    """)
    
    # Update the status constraint to remove SUPERSEDED
    op.drop_constraint("evidence_submissions_status_check", "evidence_submissions", type_="check")
    op.create_check_constraint(
        "evidence_submissions_status_check",
        "evidence_submissions",
        "status IN ('PENDING_PROCESSING', 'PROCESSING', 'PROCESSING_COMPLETE', 'PROCESSING_FAILED', 'NEEDS_REVIEW', 'ACCEPTED', 'REJECTED')",
    )


def downgrade() -> None:
    """Revert changes - add back SUPERSEDED status and column."""
    # Add back the column
    op.add_column(
        "evidence_submissions",
        sa.Column(
            "superseded_by_submission_id",
            sa.UUID(),
            nullable=True,
        ),
    )
    
    # Add back the foreign key constraint
    op.create_foreign_key(
        "evidence_submissions_superseded_by_submission_id_fkey",
        "evidence_submissions",
        "evidence_submissions",
        ["superseded_by_submission_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    
    # Update the status constraint to include SUPERSEDED
    op.drop_constraint("evidence_submissions_status_check", "evidence_submissions", type_="check")
    op.create_check_constraint(
        "evidence_submissions_status_check",
        "evidence_submissions",
        "status IN ('PENDING_PROCESSING', 'PROCESSING', 'PROCESSING_COMPLETE', 'PROCESSING_FAILED', 'NEEDS_REVIEW', 'ACCEPTED', 'REJECTED', 'SUPERSEDED')",
    )

