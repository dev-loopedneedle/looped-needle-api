"""Add overall_score and certification to audit workflows.

Revision ID: add_overall_score_certification
Revises: a1b2c3d4e5f6
Create Date: 2026-01-27
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "add_overall_score_certification"
down_revision = "b1c2d3e4f5g6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add overall_score column (integer, 0-100)
    op.add_column(
        "audit_workflows",
        sa.Column("overall_score", sa.Integer(), nullable=True),
    )

    # Add certification column (string: Bronze, Silver, Gold, or None)
    op.add_column(
        "audit_workflows",
        sa.Column("certification", sa.String(), nullable=True),
    )

    # Add check constraint for certification values
    op.create_check_constraint(
        "audit_workflows_certification_check",
        "audit_workflows",
        "certification IS NULL OR certification IN ('Bronze', 'Silver', 'Gold')",
    )

    # Calculate overall_score and certification for existing completed workflows
    op.execute(
        """
        UPDATE audit_workflows
        SET overall_score = (
            SELECT ROUND(AVG(score_value))
            FROM (
                SELECT value::int as score_value
                FROM jsonb_each_text(category_scores)
                WHERE value ~ '^[0-9]+$'
            ) scores
        ),
        certification = CASE
            WHEN (
                SELECT ROUND(AVG(value::int))
                FROM jsonb_each_text(category_scores)
                WHERE value ~ '^[0-9]+$'
            ) >= 90 THEN 'Gold'
            WHEN (
                SELECT ROUND(AVG(value::int))
                FROM jsonb_each_text(category_scores)
                WHERE value ~ '^[0-9]+$'
            ) >= 75 THEN 'Silver'
            WHEN (
                SELECT ROUND(AVG(value::int))
                FROM jsonb_each_text(category_scores)
                WHERE value ~ '^[0-9]+$'
            ) > 60 THEN 'Bronze'
            ELSE NULL
        END
        WHERE status = 'PROCESSING_COMPLETE'
          AND category_scores IS NOT NULL
          AND jsonb_typeof(category_scores) = 'object'
        """
    )


def downgrade() -> None:
    op.drop_constraint("audit_workflows_certification_check", "audit_workflows", type_="check")
    op.drop_column("audit_workflows", "certification")
    op.drop_column("audit_workflows", "overall_score")
