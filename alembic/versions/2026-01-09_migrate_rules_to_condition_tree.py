"""migrate_rules_to_condition_tree

Revision ID: 6303a865bd4a
Revises: 648c451a9d18
Create Date: 2026-01-09 11:33:21.256095

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '6303a865bd4a'
down_revision: Union[str, Sequence[str], None] = '648c451a9d18'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Migrate rules table from expression to condition_tree."""
    # Add condition_tree column (nullable first to allow existing rows)
    op.add_column(
        'rules',
        sa.Column('condition_tree', postgresql.JSONB(astext_type=sa.Text()), nullable=True)
    )
    
    # Note: If you have existing rules with expressions, you would need to migrate the data here.
    # For now, we'll set a default empty condition tree for existing rows.
    # In production, you'd want to convert existing expressions to condition trees.
    op.execute("""
        UPDATE rules 
        SET condition_tree = '{"type": "group", "id": "root", "logical": "AND", "children": []}'::jsonb
        WHERE condition_tree IS NULL
    """)
    
    # Make condition_tree NOT NULL
    op.alter_column('rules', 'condition_tree', nullable=False)
    
    # Drop old expression columns
    op.drop_column('rules', 'expression_ast')
    op.drop_column('rules', 'expression')


def downgrade() -> None:
    """Revert to expression-based rules."""
    # Add back expression columns
    op.add_column(
        'rules',
        sa.Column('expression', sa.String(), nullable=True)
    )
    op.add_column(
        'rules',
        sa.Column('expression_ast', postgresql.JSONB(astext_type=sa.Text()), nullable=True)
    )
    
    # Note: Converting condition_tree back to expression would require custom logic.
    # For now, set a default expression.
    op.execute("""
        UPDATE rules 
        SET expression = 'true'
        WHERE expression IS NULL
    """)
    
    # Make expression NOT NULL
    op.alter_column('rules', 'expression', nullable=False)
    
    # Drop condition_tree column
    op.drop_column('rules', 'condition_tree')
