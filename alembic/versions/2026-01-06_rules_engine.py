"""Add rules engine tables and workflow extensions

Revision ID: 20260106_rules_engine
Revises: create_waitlist_table
Create Date: 2026-01-06
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260106_rules_engine"
down_revision = "create_waitlist_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("state", sa.String(), nullable=False, server_default="DRAFT"),
        sa.Column("expression", sa.String(), nullable=False),
        sa.Column("expression_ast", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_by_user_profile_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user_profiles.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("disabled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "replaces_rule_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("rules.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.UniqueConstraint("code", "version", name="uq_rules_code_version"),
        sa.CheckConstraint("state IN ('DRAFT','PUBLISHED','DISABLED')", name="rules_state_check"),
        sa.Index("idx_rules_code", "code"),
    )

    op.create_table(
        "evidence_claims",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("weight", sa.Numeric(precision=5, scale=4), nullable=False, server_default="0"),
        sa.Column(
            "created_by_user_profile_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user_profiles.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("weight >= 0 AND weight <= 1", name="evidence_claims_weight_check"),
    )

    op.create_table(
        "rule_evidence_claims",
        sa.Column(
            "rule_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("rules.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "evidence_claim_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("evidence_claims.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("sort_order", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.PrimaryKeyConstraint("rule_id", "evidence_claim_id", name="pk_rule_claim"),
    )

    # Extend audit_workflows
    op.add_column(
        "audit_workflows", sa.Column("generation", sa.Integer(), nullable=False, server_default="1")
    )
    op.add_column(
        "audit_workflows",
        sa.Column("status", sa.String(), nullable=False, server_default="GENERATED"),
    )
    op.add_column(
        "audit_workflows",
        sa.Column(
            "generated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.add_column(
        "audit_workflows",
        sa.Column("engine_version", sa.String(), nullable=False, server_default="v1"),
    )
    op.add_column(
        "audit_workflows",
        sa.Column(
            "audit_data_snapshot",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )
    op.create_check_constraint(
        "audit_workflows_status_check",
        "audit_workflows",
        "status IN ('GENERATED','STALE')",
    )
    op.create_index(
        "idx_audit_workflows_audit_generation",
        "audit_workflows",
        ["audit_id", "generation"],
        unique=True,
    )

    op.create_table(
        "audit_workflow_rule_matches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "audit_workflow_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("audit_workflows.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "rule_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("rules.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("rule_code", sa.String(), nullable=False),
        sa.Column("rule_version", sa.Integer(), nullable=False),
        sa.Column("matched", sa.Boolean(), nullable=False),
        sa.Column("error", sa.String(), nullable=True),
        sa.Column(
            "evaluated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("match_context", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Index("idx_audit_workflow_rule_matches_workflow", "audit_workflow_id"),
    )

    op.create_table(
        "audit_workflow_required_claims",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "audit_workflow_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("audit_workflows.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "evidence_claim_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("evidence_claims.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("status", sa.String(), nullable=False, server_default="REQUIRED"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('REQUIRED','SATISFIED')", name="audit_workflow_required_claims_status_check"
        ),
        sa.Index(
            "uq_audit_workflow_required_claim",
            "audit_workflow_id",
            "evidence_claim_id",
            unique=True,
        ),
    )

    op.create_table(
        "audit_workflow_required_claim_sources",
        sa.Column(
            "audit_workflow_required_claim_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("audit_workflow_required_claims.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "rule_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("rules.id", ondelete="RESTRICT"),
            primary_key=True,
        ),
        sa.Column("rule_code", sa.String(), nullable=False),
        sa.Column("rule_version", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Index(
            "pk_required_claim_source", "audit_workflow_required_claim_id", "rule_id", unique=True
        ),
    )


def downgrade() -> None:
    op.drop_table("audit_workflow_required_claim_sources")
    op.drop_table("audit_workflow_required_claims")
    op.drop_table("audit_workflow_rule_matches")
    op.drop_index("idx_audit_workflows_audit_generation", table_name="audit_workflows")
    op.drop_constraint("audit_workflows_status_check", "audit_workflows", type_="check")
    op.drop_column("audit_workflows", "audit_data_snapshot")
    op.drop_column("audit_workflows", "engine_version")
    op.drop_column("audit_workflows", "generated_at")
    op.drop_column("audit_workflows", "status")
    op.drop_column("audit_workflows", "generation")
    op.drop_table("rule_evidence_claims")
    op.drop_table("evidence_claims")
    op.drop_table("rules")
