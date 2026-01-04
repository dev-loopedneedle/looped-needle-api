"""create audit table

Revision ID: 001_create_audit_table
Revises: 
Create Date: 2025-01-27

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001_create_audit_table"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - create audit table."""
    op.create_table(
        "audit",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("action_type", sa.String(length=50), nullable=False, index=True),
        sa.Column("entity_type", sa.String(length=100), nullable=False, index=True),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("details", postgresql.JSONB(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="success"),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), index=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    # Create indexes with naming convention
    op.create_index("action_type_idx", "audit", ["action_type"])
    op.create_index("entity_type_idx", "audit", ["entity_type"])
    op.create_index("entity_id_idx", "audit", ["entity_id"])
    op.create_index("user_id_idx", "audit", ["user_id"])
    op.create_index("created_at_idx", "audit", ["created_at"])


def downgrade() -> None:
    """Downgrade schema - drop audit table."""
    op.drop_index("created_at_idx", table_name="audit")
    op.drop_index("user_id_idx", table_name="audit")
    op.drop_index("entity_id_idx", table_name="audit")
    op.drop_index("entity_type_idx", table_name="audit")
    op.drop_index("action_type_idx", table_name="audit")
    op.drop_table("audit")
