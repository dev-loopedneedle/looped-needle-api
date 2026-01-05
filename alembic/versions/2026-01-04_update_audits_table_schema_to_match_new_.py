"""update_audits_table_schema_to_match_new_model

Revision ID: b486d5c74821
Revises: 6e3a1fcd41ff
Create Date: 2026-01-04 23:42:16.357614

"""
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b486d5c74821"
down_revision: str | Sequence[str] | None = "6e3a1fcd41ff"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema - update audits table to match new model schema."""
    # Drop old columns that are no longer needed
    op.execute("ALTER TABLE audits DROP COLUMN IF EXISTS questionnaire_definition_id CASCADE")
    op.execute("ALTER TABLE audits DROP COLUMN IF EXISTS scoping_responses CASCADE")
    op.execute("ALTER TABLE audits DROP COLUMN IF EXISTS brand_context_snapshot CASCADE")
    op.execute("ALTER TABLE audits DROP COLUMN IF EXISTS overall_score CASCADE")
    op.execute("ALTER TABLE audits DROP COLUMN IF EXISTS deleted_at CASCADE")

    # Drop old indexes
    op.execute("DROP INDEX IF EXISTS idx_audits_scoping_responses_gin")
    op.execute("DROP INDEX IF EXISTS idx_audits_brand_context_snapshot_gin")
    op.execute("DROP INDEX IF EXISTS idx_audits_deleted_at")

    # Drop old foreign key constraint for questionnaire_definition_id if it exists
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'audits_questionnaire_definition_id_fkey'
            ) THEN
                ALTER TABLE audits DROP CONSTRAINT audits_questionnaire_definition_id_fkey;
            END IF;
        END $$;
    """)

    # Add new columns
    # Check if audit_data exists, if not add it
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'audits' AND column_name = 'audit_data'
            ) THEN
                ALTER TABLE audits ADD COLUMN audit_data JSONB NOT NULL DEFAULT '{}';
            END IF;
        END $$;
    """)

    # Drop certification_score and certified_at if they exist (no longer needed)
    op.execute("ALTER TABLE audits DROP COLUMN IF EXISTS certification_score CASCADE")
    op.execute("ALTER TABLE audits DROP COLUMN IF EXISTS certified_at CASCADE")

    # Create GIN index for audit_data if it doesn't exist
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE indexname = 'idx_audits_audit_data_gin'
            ) THEN
                CREATE INDEX idx_audits_audit_data_gin ON audits USING gin (audit_data);
            END IF;
        END $$;
    """)

    # Update status constraint to only allow DRAFT and PUBLISHED
    # Drop ALL possible status check constraints and recreate with correct values
    op.execute("""
        DO $$
        DECLARE
            constraint_name TEXT;
        BEGIN
            -- Find and drop all status check constraints on audits table
            FOR constraint_name IN
                SELECT conname
                FROM pg_constraint
                WHERE conrelid = 'audits'::regclass
                AND contype = 'c'
                AND (conname LIKE '%status%check%' OR conname LIKE '%status_check%')
            LOOP
                EXECUTE format('ALTER TABLE audits DROP CONSTRAINT IF EXISTS %I', constraint_name);
            END LOOP;

            -- Add new constraint with correct allowed values
            ALTER TABLE audits ADD CONSTRAINT audits_status_check
                CHECK (status IN ('DRAFT', 'PUBLISHED'));
        END $$;
    """)

    # Drop certification_score constraint if it exists
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'audits_certification_score_check'
            ) THEN
                ALTER TABLE audits DROP CONSTRAINT audits_certification_score_check;
            END IF;
        END $$;
    """)

    # Update status default to DRAFT if not already set
    op.execute("ALTER TABLE audits ALTER COLUMN status SET DEFAULT 'DRAFT'")


def downgrade() -> None:
    """Downgrade schema - restore old audit_instances schema."""
    # Note: This is a destructive operation - we can't fully restore the old schema
    # as we don't have the original data. This is mainly for migration rollback testing.

    # Remove new columns
    op.execute("ALTER TABLE audits DROP COLUMN IF EXISTS audit_data CASCADE")

    # Drop new indexes
    op.execute("DROP INDEX IF EXISTS idx_audits_audit_data_gin")

    # Drop new constraints
    op.execute("ALTER TABLE audits DROP CONSTRAINT IF EXISTS audits_status_check")

    # Add back old columns (with NULL defaults since we don't have original data)
    op.execute("ALTER TABLE audits ADD COLUMN questionnaire_definition_id UUID")
    op.execute("ALTER TABLE audits ADD COLUMN scoping_responses JSONB NOT NULL DEFAULT '{}'")
    op.execute("ALTER TABLE audits ADD COLUMN brand_context_snapshot JSONB NOT NULL DEFAULT '{}'")
    op.execute("ALTER TABLE audits ADD COLUMN overall_score NUMERIC(5, 2) NULL")
    op.execute("ALTER TABLE audits ADD COLUMN deleted_at TIMESTAMP WITH TIME ZONE NULL")

    # Recreate old indexes
    op.create_index("idx_audits_scoping_responses_gin", "audits", ["scoping_responses"], postgresql_using="gin")
    op.create_index("idx_audits_brand_context_snapshot_gin", "audits", ["brand_context_snapshot"], postgresql_using="gin")
    op.create_index("idx_audits_deleted_at", "audits", ["deleted_at"])

    # Restore old status constraint
    op.execute("""
        ALTER TABLE audits ADD CONSTRAINT audits_status_check
            CHECK (status IN ('DRAFT', 'IN_PROGRESS', 'REVIEWING', 'CERTIFIED'))
    """)
