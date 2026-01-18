"""create_evidence_submissions_table

Revision ID: create_evidence_submissions
Revises: extend_workflow_status
Create Date: 2026-01-11 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "create_evidence_submissions"
down_revision: Union[str, Sequence[str], None] = "extend_workflow_status"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create evidence_submissions table with all columns, indexes, and constraints."""
    op.create_table(
        "evidence_submissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("audit_workflow_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("audit_workflow_required_claim_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("file_name", sa.Text(), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=True),
        sa.Column("mime_type", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False, server_default="PENDING_PROCESSING"),
        sa.Column("ocr_response", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("extracted_text", sa.Text(), nullable=True),
        sa.Column("extracted_fields", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("match_decision", sa.Text(), nullable=True),
        sa.Column("confidence_score", sa.Integer(), nullable=True),
        sa.Column("evaluation_reasons", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("document_type_detected", sa.Text(), nullable=True),
        sa.Column("category_detected", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("review_decision", sa.Text(), nullable=True),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("reviewed_by_user_profile_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("processing_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("processing_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["audit_workflow_id"],
            ["audit_workflows.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["audit_workflow_required_claim_id"],
            ["audit_workflow_required_claims.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["reviewed_by_user_profile_id"],
            ["user_profiles.id"],
            ondelete="RESTRICT",
        ),
    )
    
    # Create indexes
    op.create_index("idx_evidence_submissions_workflow_id", "evidence_submissions", ["audit_workflow_id"])
    op.create_index("idx_evidence_submissions_required_claim_id", "evidence_submissions", ["audit_workflow_required_claim_id"])
    op.create_index("idx_evidence_submissions_status", "evidence_submissions", ["status"])
    op.create_index("idx_evidence_submissions_created_at", "evidence_submissions", ["created_at"])
    op.create_index("idx_evidence_submissions_processing_started_at", "evidence_submissions", ["processing_started_at"])
    op.create_index("idx_evidence_submissions_processing_completed_at", "evidence_submissions", ["processing_completed_at"])
    
    # Create GIN indexes for JSONB
    op.create_index(
        "idx_evidence_submissions_ocr_response_gin",
        "evidence_submissions",
        ["ocr_response"],
        postgresql_using="gin",
    )
    op.create_index(
        "idx_evidence_submissions_extracted_fields_gin",
        "evidence_submissions",
        ["extracted_fields"],
        postgresql_using="gin",
    )
    
    # Create check constraints
    op.create_check_constraint(
        "evidence_submissions_status_check",
        "evidence_submissions",
        "status IN ('PENDING_PROCESSING', 'PROCESSING', 'PROCESSING_COMPLETE', 'PROCESSING_FAILED', 'NEEDS_REVIEW', 'ACCEPTED', 'REJECTED')",
    )
    op.create_check_constraint(
        "evidence_submissions_match_decision_check",
        "evidence_submissions",
        "match_decision IN ('MATCH', 'NO_MATCH', 'NEEDS_REVIEW') OR match_decision IS NULL",
    )
    op.create_check_constraint(
        "evidence_submissions_confidence_score_check",
        "evidence_submissions",
        "confidence_score >= 0 AND confidence_score <= 100 OR confidence_score IS NULL",
    )
    op.create_check_constraint(
        "evidence_submissions_review_decision_check",
        "evidence_submissions",
        "review_decision IN ('ACCEPTED', 'REJECTED') OR review_decision IS NULL",
    )


def downgrade() -> None:
    """Drop evidence_submissions table."""
    op.drop_table("evidence_submissions")

