"""Brands domain database models."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlmodel import Field, SQLModel

from src.brands.constants import CompanySize


class Brand(SQLModel, table=True):
    """Brand model."""

    __tablename__ = "brands"

    id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(PostgresUUID(as_uuid=True), primary_key=True),
    )
    name: str = Field(max_length=255, index=True)
    registration_country: str
    company_size: CompanySize = Field(sa_column=Column(String, nullable=False))
    target_markets: list[str] = Field(default_factory=list, sa_column=Column(ARRAY(String)))
    user_id: UUID | None = Field(
        default=None,
        sa_column=Column(
            PostgresUUID(as_uuid=True),
            ForeignKey("user_profiles.id", ondelete="RESTRICT"),
            nullable=True,
            unique=True,
            index=True,
        ),
    )
    deleted_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), index=True)
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), index=True),
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )

    __table_args__ = (
        CheckConstraint(
            "company_size IN ('Micro', 'SME', 'Large')", name="brands_company_size_check"
        ),
    )

