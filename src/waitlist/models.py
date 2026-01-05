"""Waitlist domain database models."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlmodel import Field, SQLModel


class WaitlistEntry(SQLModel, table=True):
    """Waitlist entry model."""

    __tablename__ = "waitlist_entries"

    id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(PostgresUUID(as_uuid=True), primary_key=True),
    )
    email: str = Field(max_length=255, index=True, unique=True)
    name: str | None = Field(default=None, max_length=255)
    message: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), index=True),
    )

    __table_args__ = (UniqueConstraint("email", name="waitlist_entries_email_key"),)

