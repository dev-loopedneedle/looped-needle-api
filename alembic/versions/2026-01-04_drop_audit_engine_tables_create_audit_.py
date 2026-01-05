"""drop_audit_engine_tables_create_audit_workflows_update_audits_brand_id

Revision ID: 6e3a1fcd41ff
Revises: a17ba7f8c984
Create Date: 2026-01-04 23:14:41.172061

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6e3a1fcd41ff"
down_revision: str | Sequence[str] | None = "a17ba7f8c984"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema - drop audit_engine tables, create audit_workflows, update audits.brand_id."""
    # Step 1: Drop audit_engine tables (in reverse dependency order)
    # Drop tables that have foreign keys first

    # Drop audit_items (references audits and sustainability_criteria)
    op.execute("DROP TABLE IF EXISTS audit_items CASCADE")

    # Drop evidence_files (references brands)
    op.execute("DROP TABLE IF EXISTS evidence_files CASCADE")

    # Drop audit_item_evidence_links (references audit_items and evidence_files)
    op.execute("DROP TABLE IF EXISTS audit_item_evidence_links CASCADE")

    # Drop criteria_rules (references sustainability_criteria)
    op.execute("DROP TABLE IF EXISTS criteria_rules CASCADE")

    # Drop questionnaire_definitions
    op.execute("DROP TABLE IF EXISTS questionnaire_definitions CASCADE")

    # Drop sustainability_criteria
    op.execute("DROP TABLE IF EXISTS sustainability_criteria CASCADE")

    # Drop products (references brands)
    op.execute("DROP TABLE IF EXISTS products CASCADE")

    # Drop supply_chain_nodes (references brands)
    op.execute("DROP TABLE IF EXISTS supply_chain_nodes CASCADE")

    # Step 2: Update audits.brand_id from VARCHAR to UUID with FK constraint
    # Drop the existing index on brand_id if it exists
    op.execute("DROP INDEX IF EXISTS idx_audits_brand_id")

    # Drop any existing foreign key constraints on brand_id (old constraint from audit_instances)
    op.execute("""
        DO $$
        BEGIN
            -- Drop old constraint if it exists (from audit_instances table)
            IF EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'audit_instances_brand_id_fkey'
                AND conrelid = 'audits'::regclass
            ) THEN
                ALTER TABLE audits DROP CONSTRAINT audit_instances_brand_id_fkey;
            END IF;

            -- Drop new constraint if it already exists (in case migration was partially run)
            IF EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'audits_brand_id_fkey'
                AND conrelid = 'audits'::regclass
            ) THEN
                ALTER TABLE audits DROP CONSTRAINT audits_brand_id_fkey;
            END IF;
        END $$;
    """)

    # Delete any audits with invalid brand_id values (non-UUID strings)
    # Use text() function to explicitly cast to text for regex matching
    op.execute("""
        DELETE FROM audits
        WHERE text(brand_id) !~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    """)

    # Convert brand_id from VARCHAR to UUID
    # This will fail if there are any remaining invalid UUIDs
    op.execute("""
        ALTER TABLE audits
        ALTER COLUMN brand_id TYPE UUID USING brand_id::UUID
    """)

    # Add foreign key constraint (only one should exist)
    op.create_foreign_key(
        "audits_brand_id_fkey",
        "audits",
        "brands",
        ["brand_id"],
        ["id"],
        ondelete="RESTRICT",
    )

    # Recreate the index on brand_id
    op.create_index("idx_audits_brand_id", "audits", ["brand_id"])

    # Step 3: Create audit_workflows table
    op.create_table(
        "audit_workflows",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("audit_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), index=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Add foreign key constraint for audit_id
    op.create_foreign_key(
        "audit_workflows_audit_id_fkey",
        "audit_workflows",
        "audits",
        ["audit_id"],
        ["id"],
        ondelete="RESTRICT",
    )

    # Create index on audit_id
    op.create_index("idx_audit_workflows_audit_id", "audit_workflows", ["audit_id"])


def downgrade() -> None:
    """Downgrade schema - restore audit_engine tables, drop audit_workflows, revert audits.brand_id."""
    # Step 1: Drop audit_workflows table
    op.drop_index("idx_audit_workflows_audit_id", table_name="audit_workflows")
    op.drop_constraint("audit_workflows_audit_id_fkey", "audit_workflows", type_="foreignkey")
    op.drop_table("audit_workflows")

    # Step 2: Revert audits.brand_id from UUID to VARCHAR
    # Drop foreign key constraint
    op.drop_constraint("audits_brand_id_fkey", "audits", type_="foreignkey")

    # Drop index
    op.drop_index("idx_audits_brand_id", table_name="audits")

    # Convert brand_id from UUID back to VARCHAR
    op.execute("""
        ALTER TABLE audits
        ALTER COLUMN brand_id TYPE VARCHAR(255) USING brand_id::TEXT
    """)

    # Recreate index
    op.create_index("idx_audits_brand_id", "audits", ["brand_id"])

    # Step 3: Note: We don't recreate the dropped audit_engine tables in downgrade
    # as that would require the full schema definition. If needed, those tables
    # should be recreated from the original migration that created them.
    pass
