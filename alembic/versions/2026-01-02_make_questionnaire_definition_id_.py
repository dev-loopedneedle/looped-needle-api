"""make_questionnaire_definition_id_nullable

Revision ID: 6b9e85ea4cd3
Revises: 794aba133a29
Create Date: 2026-01-02 15:51:30.203152

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '6b9e85ea4cd3'
down_revision: Union[str, Sequence[str], None] = '794aba133a29'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - make questionnaire_definition_id nullable."""
    # Make questionnaire_definition_id nullable
    op.alter_column(
        "audit_instances",
        "questionnaire_definition_id",
        nullable=True,
        existing_type=postgresql.UUID(as_uuid=True),
    )


def downgrade() -> None:
    """Downgrade schema - make questionnaire_definition_id non-nullable."""
    # Note: This will fail if there are any NULL values in the column
    # Set a default value for any NULL entries before making it non-nullable
    op.execute(
        """
        UPDATE audit_instances 
        SET questionnaire_definition_id = '00000000-0000-0000-0000-000000000000'::uuid
        WHERE questionnaire_definition_id IS NULL
        """
    )
    # Make questionnaire_definition_id non-nullable
    op.alter_column(
        "audit_instances",
        "questionnaire_definition_id",
        nullable=False,
        existing_type=postgresql.UUID(as_uuid=True),
    )
