"""extend_audit_workflows_status

Revision ID: extend_workflow_status
Revises: add_required_workflow_claims
Create Date: 2026-01-11 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "extend_workflow_status"
down_revision: Union[str, Sequence[str], None] = "add_required_workflow_claims"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Extend audit_workflows.status constraint to include PROCESSING statuses."""
    # Drop existing constraint
    op.drop_constraint("audit_workflows_status_check", "audit_workflows", type_="check")
    
    # Add new constraint with extended statuses
    op.create_check_constraint(
        "audit_workflows_status_check",
        "audit_workflows",
        "status IN ('GENERATED', 'STALE', 'PROCESSING', 'PROCESSING_COMPLETE', 'PROCESSING_FAILED')",
    )


def downgrade() -> None:
    """Revert audit_workflows.status constraint to original values."""
    # Drop extended constraint
    op.drop_constraint("audit_workflows_status_check", "audit_workflows", type_="check")
    
    # Restore original constraint
    op.create_check_constraint(
        "audit_workflows_status_check",
        "audit_workflows",
        "status IN ('GENERATED', 'STALE')",
    )



