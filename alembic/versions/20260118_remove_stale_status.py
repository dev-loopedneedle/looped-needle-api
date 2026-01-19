"""Remove unused STALE status from audit workflows.

Revision ID: ba5e31880a38
Revises: 1f33d2a93db2
Create Date: 2026-01-18
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "ba5e31880a38"
down_revision = "1f33d2a93db2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop the old constraint
    op.drop_constraint("audit_workflows_status_check", "audit_workflows", type_="check")
    
    # Add new constraint without STALE
    op.create_check_constraint(
        "audit_workflows_status_check",
        "audit_workflows",
        "status IN ('GENERATED', 'PROCESSING', 'PROCESSING_COMPLETE', 'PROCESSING_FAILED')",
    )
    
    # Update any existing workflows with STALE status to GENERATED
    op.execute(
        """
        UPDATE audit_workflows
        SET status = 'GENERATED'
        WHERE status = 'STALE'
        """
    )


def downgrade() -> None:
    # Update any GENERATED workflows back to STALE (if they were originally STALE)
    # Note: We can't know which ones were STALE, so we'll leave them as GENERATED
    
    # Drop the constraint
    op.drop_constraint("audit_workflows_status_check", "audit_workflows", type_="check")
    
    # Add back the old constraint with STALE
    op.create_check_constraint(
        "audit_workflows_status_check",
        "audit_workflows",
        "status IN ('GENERATED', 'STALE', 'PROCESSING', 'PROCESSING_COMPLETE', 'PROCESSING_FAILED')",
    )

