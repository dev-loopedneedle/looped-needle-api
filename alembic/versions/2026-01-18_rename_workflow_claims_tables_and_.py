"""rename_workflow_claims_tables_and_columns

Revision ID: 3dbf4dae8bae
Revises: 43df249771c1
Create Date: 2026-01-18 12:39:08.150535

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3dbf4dae8bae'
down_revision: Union[str, Sequence[str], None] = '43df249771c1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Rename workflow claims tables and columns."""
    # Step 1: Drop foreign key constraints (must be done before renaming)
    # Drop FK from evidence_submissions
    op.execute("""
        DO $$ 
        DECLARE
            r RECORD;
        BEGIN
            FOR r IN (
                SELECT constraint_name 
                FROM information_schema.table_constraints 
                WHERE table_name = 'evidence_submissions' 
                AND constraint_type = 'FOREIGN KEY'
                AND constraint_name LIKE '%audit_workflow_required_claim%'
            ) LOOP
                EXECUTE 'ALTER TABLE evidence_submissions DROP CONSTRAINT ' || quote_ident(r.constraint_name);
            END LOOP;
        END $$;
    """)
    
    # Drop FK from audit_workflow_required_claim_sources
    op.execute("""
        DO $$ 
        DECLARE
            r RECORD;
        BEGIN
            FOR r IN (
                SELECT constraint_name 
                FROM information_schema.table_constraints 
                WHERE table_name = 'audit_workflow_required_claim_sources' 
                AND constraint_type = 'FOREIGN KEY'
                AND constraint_name LIKE '%audit_workflow_required_claim_id%'
            ) LOOP
                EXECUTE 'ALTER TABLE audit_workflow_required_claim_sources DROP CONSTRAINT ' || quote_ident(r.constraint_name);
            END LOOP;
        END $$;
    """)
    
    # Step 2: Rename foreign key columns
    op.alter_column(
        "audit_workflow_required_claim_sources",
        "audit_workflow_required_claim_id",
        new_column_name="audit_workflow_claim_id",
    )
    
    op.alter_column(
        "evidence_submissions",
        "audit_workflow_required_claim_id",
        new_column_name="audit_workflow_claim_id",
    )
    
    # Step 3: Rename tables
    op.rename_table("audit_workflow_required_claims", "audit_workflow_claims")
    op.rename_table("audit_workflow_required_claim_sources", "audit_workflow_claim_sources")
    
    # Step 4: Recreate foreign key constraints with new names
    op.create_foreign_key(
        "evidence_submissions_audit_workflow_claim_id_fkey",
        "evidence_submissions",
        "audit_workflow_claims",
        ["audit_workflow_claim_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    
    op.create_foreign_key(
        "audit_workflow_claim_sources_audit_workflow_claim_id_fkey",
        "audit_workflow_claim_sources",
        "audit_workflow_claims",
        ["audit_workflow_claim_id"],
        ["id"],
        ondelete="CASCADE",
    )
    
    # Rename constraints (check if exists first, create if missing)
    op.execute("""
        DO $$ 
        DECLARE
            old_constraint_exists BOOLEAN;
            new_constraint_exists BOOLEAN;
        BEGIN
            -- Check if old constraint exists
            SELECT EXISTS (
                SELECT 1 
                FROM information_schema.table_constraints 
                WHERE table_name = 'audit_workflow_claims' 
                AND constraint_name = 'audit_workflow_required_claims_status_check'
            ) INTO old_constraint_exists;
            
            -- Check if new constraint already exists
            SELECT EXISTS (
                SELECT 1 
                FROM information_schema.table_constraints 
                WHERE table_name = 'audit_workflow_claims' 
                AND constraint_name = 'audit_workflow_claims_status_check'
            ) INTO new_constraint_exists;
            
            IF old_constraint_exists AND NOT new_constraint_exists THEN
                -- Rename the constraint
                EXECUTE 'ALTER TABLE audit_workflow_claims '
                    'RENAME CONSTRAINT audit_workflow_required_claims_status_check '
                    'TO audit_workflow_claims_status_check';
            ELSIF NOT old_constraint_exists AND NOT new_constraint_exists THEN
                -- Create the constraint if it doesn't exist
                EXECUTE 'ALTER TABLE audit_workflow_claims '
                    'ADD CONSTRAINT audit_workflow_claims_status_check '
                    'CHECK (status IN (''REQUIRED'', ''SATISFIED''))';
            END IF;
        END $$;
    """)
    
    # Rename indexes
    op.drop_index("uq_audit_workflow_required_claim", table_name="audit_workflow_claims")
    op.create_index(
        "uq_audit_workflow_claim",
        "audit_workflow_claims",
        ["audit_workflow_id", "evidence_claim_id"],
        unique=True,
    )
    
    op.drop_index("pk_required_claim_source", table_name="audit_workflow_claim_sources")
    op.create_index(
        "pk_claim_source",
        "audit_workflow_claim_sources",
        ["audit_workflow_claim_id", "rule_id"],
        unique=True,
    )
    
    # Rename index in evidence_submissions
    op.drop_index("idx_evidence_submissions_required_claim_id", table_name="evidence_submissions")
    op.create_index(
        "idx_evidence_submissions_claim_id",
        "evidence_submissions",
        ["audit_workflow_claim_id"],
    )


def downgrade() -> None:
    """Revert table and column renames."""
    # Step 1: Drop foreign key constraints
    op.drop_constraint(
        "audit_workflow_claim_sources_audit_workflow_claim_id_fkey",
        "audit_workflow_claim_sources",
        type_="foreignkey",
    )
    
    op.drop_constraint(
        "evidence_submissions_audit_workflow_claim_id_fkey",
        "evidence_submissions",
        type_="foreignkey",
    )
    
    # Step 2: Rename tables back
    op.rename_table("audit_workflow_claim_sources", "audit_workflow_required_claim_sources")
    op.rename_table("audit_workflow_claims", "audit_workflow_required_claims")
    
    # Step 3: Rename columns back
    op.alter_column(
        "audit_workflow_required_claim_sources",
        "audit_workflow_claim_id",
        new_column_name="audit_workflow_required_claim_id",
    )
    
    op.alter_column(
        "evidence_submissions",
        "audit_workflow_claim_id",
        new_column_name="audit_workflow_required_claim_id",
    )
    
    # Step 4: Recreate foreign keys with old names
    op.execute("""
        ALTER TABLE evidence_submissions
        ADD CONSTRAINT evidence_submissions_audit_workflow_required_claim_id_fkey
        FOREIGN KEY (audit_workflow_required_claim_id)
        REFERENCES audit_workflow_required_claims(id)
        ON DELETE RESTRICT;
    """)
    
    op.execute("""
        ALTER TABLE audit_workflow_required_claim_sources
        ADD CONSTRAINT audit_workflow_required_claim_sources_audit_workflow_required_claim_id_fkey
        FOREIGN KEY (audit_workflow_required_claim_id)
        REFERENCES audit_workflow_required_claims(id)
        ON DELETE CASCADE;
    """)
    
    # Rename indexes back
    op.drop_index("idx_evidence_submissions_claim_id", table_name="evidence_submissions")
    op.create_index(
        "idx_evidence_submissions_required_claim_id",
        "evidence_submissions",
        ["audit_workflow_required_claim_id"],
    )
    
    op.drop_index("pk_claim_source", table_name="audit_workflow_required_claim_sources")
    op.create_index(
        "pk_required_claim_source",
        "audit_workflow_required_claim_sources",
        ["audit_workflow_required_claim_id", "rule_id"],
        unique=True,
    )
    
    op.drop_index("uq_audit_workflow_claim", table_name="audit_workflow_required_claims")
    op.create_index(
        "uq_audit_workflow_required_claim",
        "audit_workflow_required_claims",
        ["audit_workflow_id", "evidence_claim_id"],
        unique=True,
    )
    
    # Rename constraint back
    op.execute(
        "ALTER TABLE audit_workflow_required_claims "
        "RENAME CONSTRAINT audit_workflow_claims_status_check "
        "TO audit_workflow_required_claims_status_check"
    )
