"""Authentication domain database models."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Column, DateTime, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlmodel import Field, SQLModel


class UserProfile(SQLModel, table=True):
    """User profile model."""

    __tablename__ = "user_profiles"

    id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(PostgresUUID(as_uuid=True), primary_key=True),
    )
    clerk_user_id: str = Field(sa_column=Column(String, nullable=False, unique=True, index=True))
    is_active: bool = Field(
        default=True, sa_column=Column(Boolean, nullable=False, server_default="true", index=True)
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True),
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    last_access_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), index=True)
    )

    __table_args__ = (UniqueConstraint("clerk_user_id", name="user_profiles_clerk_user_id_key"),)
