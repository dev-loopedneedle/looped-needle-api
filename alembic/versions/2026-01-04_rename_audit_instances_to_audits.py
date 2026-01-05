"""rename_audit_instances_to_audits

Revision ID: a17ba7f8c984
Revises: 1255d90917de
Create Date: 2026-01-04 22:30:00.000000

"""
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a17ba7f8c984"
down_revision: str | Sequence[str] | None = "1255d90917de"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema - drop old audits table, rename audit_instances to audits, update foreign keys."""
    # Drop the old simple audits table if it exists
    op.execute("DROP TABLE IF EXISTS audits CASCADE")

    # Rename audit_instances table to audits
    op.rename_table("audit_instances", "audits")

    # Rename indexes
    op.execute("ALTER INDEX IF EXISTS idx_audit_instances_scoping_responses_gin RENAME TO idx_audits_scoping_responses_gin")
    op.execute("ALTER INDEX IF EXISTS idx_audit_instances_brand_context_snapshot_gin RENAME TO idx_audits_brand_context_snapshot_gin")
    op.execute("ALTER INDEX IF EXISTS idx_audit_instances_brand_id RENAME TO idx_audits_brand_id")
    op.execute("ALTER INDEX IF EXISTS idx_audit_instances_status RENAME TO idx_audits_status")
    op.execute("ALTER INDEX IF EXISTS idx_audit_instances_created_at RENAME TO idx_audits_created_at")
    op.execute("ALTER INDEX IF EXISTS idx_audit_instances_deleted_at RENAME TO idx_audits_deleted_at")

    # Rename constraint (handle both possible names)
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'audit_instances_status_check'
                AND conrelid = 'audits'::regclass
            ) THEN
                ALTER TABLE audits RENAME CONSTRAINT audit_instances_status_check TO audits_status_check;
            END IF;
        END $$;
    """)

    # Update audit_items foreign key: rename column and update constraint
    op.alter_column("audit_items", "audit_instance_id", new_column_name="audit_id")

    # Drop old foreign key if it exists
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'audit_items_audit_instance_id_fkey'
            ) THEN
                ALTER TABLE audit_items DROP CONSTRAINT audit_items_audit_instance_id_fkey;
            END IF;
        END $$;
    """)

    # Create new foreign key
    op.create_foreign_key(
        "audit_items_audit_id_fkey",
        "audit_items",
        "audits",
        ["audit_id"],
        ["id"],
        ondelete="RESTRICT",
    )

    # Update audit_items index - drop if exists, then recreate
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE indexname = 'idx_audit_items_audit_criteria'
            ) THEN
                DROP INDEX idx_audit_items_audit_criteria;
            END IF;
        END $$;
    """)
    op.create_index(
        "idx_audit_items_audit_criteria",
        "audit_items",
        ["audit_id", "criteria_id"],
        unique=True,
    )


def downgrade() -> None:
    """Downgrade schema - rename audits back to audit_instances."""
    # Rename audits table back to audit_instances
    op.rename_table("audits", "audit_instances")

    # Rename indexes back
    op.execute("ALTER INDEX IF EXISTS idx_audits_scoping_responses_gin RENAME TO idx_audit_instances_scoping_responses_gin")
    op.execute("ALTER INDEX IF EXISTS idx_audits_brand_context_snapshot_gin RENAME TO idx_audit_instances_brand_context_snapshot_gin")
    op.execute("ALTER INDEX IF EXISTS idx_audits_brand_id RENAME TO idx_audit_instances_brand_id")
    op.execute("ALTER INDEX IF EXISTS idx_audits_status RENAME TO idx_audit_instances_status")
    op.execute("ALTER INDEX IF EXISTS idx_audits_created_at RENAME TO idx_audit_instances_created_at")
    op.execute("ALTER INDEX IF EXISTS idx_audits_deleted_at RENAME TO idx_audit_instances_deleted_at")

    # Rename constraint back
    op.execute("ALTER TABLE audit_instances RENAME CONSTRAINT audits_status_check TO audit_instances_status_check")

    # Update audit_items foreign key back
    op.alter_column("audit_items", "audit_id", new_column_name="audit_instance_id")
    op.drop_constraint("audit_items_audit_id_fkey", "audit_items", type_="foreignkey")
    op.create_foreign_key(
        "audit_items_audit_instance_id_fkey",
        "audit_items",
        "audit_instances",
        ["audit_instance_id"],
        ["id"],
        ondelete="RESTRICT",
    )

    # Update audit_items index back
    op.drop_index("idx_audit_items_audit_criteria", table_name="audit_items")
    op.create_index(
        "idx_audit_items_audit_criteria",
        "audit_items",
        ["audit_instance_id", "criteria_id"],
        unique=True,
    )
