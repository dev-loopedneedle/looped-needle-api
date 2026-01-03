"""add_user_profiles_and_brand_ownership

Revision ID: add_user_profiles
Revises: 6b9e85ea4cd3
Create Date: 2026-01-02 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "add_user_profiles"
down_revision: Union[str, Sequence[str], None] = "6b9e85ea4cd3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - add user_profiles table and user_id to brands."""
    # Create user_profiles table
    op.create_table(
        "user_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("clerk_user_id", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_access_at", sa.DateTime(timezone=True), nullable=True),
    )
    # Create indexes
    op.create_index("idx_user_profiles_clerk_user_id", "user_profiles", ["clerk_user_id"], unique=True)
    op.create_index("idx_user_profiles_is_active", "user_profiles", ["is_active"])
    op.create_index("idx_user_profiles_last_access_at", "user_profiles", ["last_access_at"])
    op.create_index("idx_user_profiles_created_at", "user_profiles", ["created_at"])

    # Add user_id column to brands table
    op.add_column(
        "brands",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    # Create foreign key constraint
    op.create_foreign_key(
        "brands_user_id_fkey",
        "brands",
        "user_profiles",
        ["user_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    # Create unique constraint on user_id (one brand per user)
    op.create_unique_constraint("brands_user_id_key", "brands", ["user_id"])
    # Create index on user_id
    op.create_index("idx_brands_user_id", "brands", ["user_id"])


def downgrade() -> None:
    """Downgrade schema - remove user_id from brands and drop user_profiles table."""
    # Remove user_id column from brands
    op.drop_index("idx_brands_user_id", "brands")
    op.drop_constraint("brands_user_id_key", "brands", type_="unique")
    op.drop_constraint("brands_user_id_fkey", "brands", type_="foreignkey")
    op.drop_column("brands", "user_id")

    # Drop user_profiles table
    op.drop_index("idx_user_profiles_created_at", "user_profiles")
    op.drop_index("idx_user_profiles_last_access_at", "user_profiles")
    op.drop_index("idx_user_profiles_is_active", "user_profiles")
    op.drop_index("idx_user_profiles_clerk_user_id", "user_profiles")
    op.drop_table("user_profiles")

