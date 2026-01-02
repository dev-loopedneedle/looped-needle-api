"""drop_audit_table

Revision ID: 794aba133a29
Revises: 002_create_inference_schema
Create Date: 2026-01-02 12:36:17.738928

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = '794aba133a29'
down_revision: Union[str, Sequence[str], None] = '002_create_inference_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - drop audit table."""
    # Check if audit table exists before dropping
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()
    
    if 'audit' in tables:
        # Drop indexes first (if they exist)
        try:
            op.drop_index('created_at_idx', table_name='audit')
        except Exception:
            pass
        try:
            op.drop_index('user_id_idx', table_name='audit')
        except Exception:
            pass
        try:
            op.drop_index('entity_id_idx', table_name='audit')
        except Exception:
            pass
        try:
            op.drop_index('entity_type_idx', table_name='audit')
        except Exception:
            pass
        try:
            op.drop_index('action_type_idx', table_name='audit')
        except Exception:
            pass
        
        # Drop the table
        op.drop_table('audit')


def downgrade() -> None:
    """Downgrade schema - recreate audit table."""
    from sqlalchemy.dialects import postgresql
    
    # Recreate audit table (matching the original migration schema)
    op.create_table(
        'audit',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('action_type', sa.String(length=50), nullable=False, index=True),
        sa.Column('entity_type', sa.String(length=100), nullable=False, index=True),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('details', postgresql.JSONB(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='success'),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), index=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    # Recreate indexes
    op.create_index('action_type_idx', 'audit', ['action_type'])
    op.create_index('entity_type_idx', 'audit', ['entity_type'])
    op.create_index('entity_id_idx', 'audit', ['entity_id'])
    op.create_index('user_id_idx', 'audit', ['user_id'])
    op.create_index('created_at_idx', 'audit', ['created_at'])
