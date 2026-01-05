"""change_audit_instance_default_status_to_draft

Revision ID: 1255d90917de
Revises: a99bc4884c06
Create Date: 2026-01-04 22:00:00.000000

"""
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1255d90917de"
down_revision: str | Sequence[str] | None = "a99bc4884c06"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema - change audit_instance default status to DRAFT and update constraint."""
    # Use raw SQL to find and drop all check constraints on status column
    # This is more robust than trying specific constraint names
    op.execute("""
        DO $$
        DECLARE
            r RECORD;
        BEGIN
            FOR r IN (
                SELECT constraint_name
                FROM information_schema.table_constraints
                WHERE table_name = 'audit_instances'
                AND constraint_type = 'CHECK'
                AND constraint_name LIKE '%status%'
            ) LOOP
                EXECUTE 'ALTER TABLE audit_instances DROP CONSTRAINT IF EXISTS ' || quote_ident(r.constraint_name);
            END LOOP;
        END $$;
    """)

    # Add the new constraint with DRAFT status
    op.create_check_constraint(
        "audit_instances_status_check",
        "audit_instances",
        "status IN ('DRAFT', 'IN_PROGRESS', 'REVIEWING', 'CERTIFIED')",
    )

    # Update existing IN_PROGRESS records to DRAFT
    op.execute("UPDATE audit_instances SET status = 'DRAFT' WHERE status = 'IN_PROGRESS'")

    # Change the default value
    op.alter_column(
        "audit_instances",
        "status",
        server_default="DRAFT",
    )


def downgrade() -> None:
    """Downgrade schema - restore IN_PROGRESS as default."""
    # Update DRAFT records back to IN_PROGRESS
    op.execute("UPDATE audit_instances SET status = 'IN_PROGRESS' WHERE status = 'DRAFT'")

    # Drop the constraint
    op.drop_constraint("audit_instances_status_check", "audit_instances", type_="check")
    # Recreate the original constraint without DRAFT
    op.create_check_constraint(
        "audit_instances_status_check",
        "audit_instances",
        "status IN ('IN_PROGRESS', 'REVIEWING', 'CERTIFIED')",
    )

    # Change the default value back
    op.alter_column(
        "audit_instances",
        "status",
        server_default="IN_PROGRESS",
    )
