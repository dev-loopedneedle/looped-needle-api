"""Inference engine domain database models."""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlmodel import Field, SQLModel

from src.inference.constants import (
    AuditInstanceStatus,
    AuditItemStatus,
    CompanySize,
    SustainabilityDomain,
)


class Brand(SQLModel, table=True):
    """Brand model."""

    __tablename__ = "brands"

    id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(PostgresUUID(as_uuid=True), primary_key=True),
    )
    name: str = Field(max_length=255, index=True)
    registration_country: str
    company_size: CompanySize
    target_markets: list[str] = Field(default_factory=list, sa_column=Column(ARRAY(String)))
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

    # Relationships (forward references for tables not yet defined)
    # products: list["Product"] = Relationship(back_populates="brand")
    # supply_chain_nodes: list["SupplyChainNode"] = Relationship(back_populates="brand")
    # audit_instances: list["AuditInstance"] = Relationship(back_populates="brand")
    # evidence_files: list["EvidenceFile"] = Relationship(back_populates="brand")

    __table_args__ = (
        CheckConstraint(
            "company_size IN ('Micro', 'SME', 'Large')", name="brands_company_size_check"
        ),
    )


class Product(SQLModel, table=True):
    """Product model."""

    __tablename__ = "products"

    id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(PostgresUUID(as_uuid=True), primary_key=True),
    )
    brand_id: UUID = Field(
        sa_column=Column(
            PostgresUUID(as_uuid=True), ForeignKey("brands.id", ondelete="RESTRICT"), nullable=False
        )
    )
    name: str
    category: str
    materials_composition: list[dict[str, Any]] = Field(
        default_factory=list, sa_column=Column(JSONB, nullable=False)
    )
    manufacturing_processes: list[str] = Field(
        default_factory=list, sa_column=Column(ARRAY(String), nullable=False)
    )
    deleted_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), index=True)
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True)),
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )

    # Relationships
    # brand: Brand = Relationship(back_populates="products")

    __table_args__ = (
        Index(
            "idx_products_materials_composition_gin",
            "materials_composition",
            postgresql_using="gin",
        ),
    )


class SupplyChainNode(SQLModel, table=True):
    """Supply chain node model."""

    __tablename__ = "supply_chain_nodes"

    id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(PostgresUUID(as_uuid=True), primary_key=True),
    )
    brand_id: UUID = Field(
        sa_column=Column(
            PostgresUUID(as_uuid=True), ForeignKey("brands.id", ondelete="RESTRICT"), nullable=False
        )
    )
    role: str
    country: str
    tier_level: int
    deleted_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), index=True)
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True)),
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )

    # Relationships
    # brand: Brand = Relationship(back_populates="supply_chain_nodes")

    __table_args__ = (
        CheckConstraint("tier_level > 0", name="supply_chain_nodes_tier_level_check"),
    )


class SustainabilityCriterion(SQLModel, table=True):
    """Sustainability criterion model."""

    __tablename__ = "sustainability_criteria"

    id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(PostgresUUID(as_uuid=True), primary_key=True),
    )
    code: str = Field(unique=True, index=True)
    name: str
    description: str
    domain: SustainabilityDomain
    deleted_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), index=True)
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True)),
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )

    # Relationships
    # rules: list["CriteriaRule"] = Relationship(back_populates="criterion")

    __table_args__ = (
        CheckConstraint(
            "domain IN ('Social', 'Environmental', 'Governance')",
            name="sustainability_criteria_domain_check",
        ),
    )


class CriteriaRule(SQLModel, table=True):
    """Criteria rule model."""

    __tablename__ = "criteria_rules"

    id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(PostgresUUID(as_uuid=True), primary_key=True),
    )
    criteria_id: UUID = Field(
        sa_column=Column(
            PostgresUUID(as_uuid=True),
            ForeignKey("sustainability_criteria.id", ondelete="RESTRICT"),
            nullable=False,
        )
    )
    rule_name: str
    condition_expression: str = Field(sa_column=Column(Text, nullable=False))
    priority: int = Field(default=0, index=True)
    deleted_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), index=True)
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True)),
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )

    # Relationships
    # criterion: SustainabilityCriterion = Relationship(back_populates="rules")

    __table_args__ = (Index("idx_criteria_rules_criteria_priority", "criteria_id", "priority"),)


class QuestionnaireDefinition(SQLModel, table=True):
    """Questionnaire definition model."""

    __tablename__ = "questionnaire_definitions"

    id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(PostgresUUID(as_uuid=True), primary_key=True),
    )
    name: str
    form_schema: dict[str, Any] = Field(
        default_factory=dict, sa_column=Column(JSONB, nullable=False)
    )
    is_active: bool = Field(default=True, index=True)
    deleted_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), index=True)
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True)),
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )

    # Relationships
    # audit_instances: list["AuditInstance"] = Relationship(back_populates="questionnaire")

    __table_args__ = (
        Index(
            "idx_questionnaire_definitions_form_schema_gin",
            "form_schema",
            postgresql_using="gin",
        ),
    )


class AuditInstance(SQLModel, table=True):
    """Audit instance model."""

    __tablename__ = "audit_instances"

    id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(PostgresUUID(as_uuid=True), primary_key=True),
    )
    brand_id: UUID = Field(
        sa_column=Column(
            PostgresUUID(as_uuid=True), ForeignKey("brands.id", ondelete="RESTRICT"), nullable=False
        )
    )
    questionnaire_definition_id: UUID = Field(
        sa_column=Column(
            PostgresUUID(as_uuid=True),
            ForeignKey("questionnaire_definitions.id", ondelete="RESTRICT"),
            nullable=False,
        )
    )
    status: AuditInstanceStatus = Field(default=AuditInstanceStatus.IN_PROGRESS, index=True)
    scoping_responses: dict[str, Any] = Field(
        default_factory=dict, sa_column=Column(JSONB, nullable=False)
    )
    brand_context_snapshot: dict[str, Any] = Field(
        default_factory=dict, sa_column=Column(JSONB, nullable=False)
    )
    overall_score: float | None = Field(
        default=None, sa_column=Column(Numeric(5, 2), nullable=True)
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

    # Relationships
    # brand: Brand = Relationship(back_populates="audit_instances")
    # questionnaire: QuestionnaireDefinition = Relationship(back_populates="audit_instances")
    # audit_items: list["AuditItem"] = Relationship(back_populates="audit_instance")

    __table_args__ = (
        Index(
            "idx_audit_instances_scoping_responses_gin",
            "scoping_responses",
            postgresql_using="gin",
        ),
        Index(
            "idx_audit_instances_brand_context_snapshot_gin",
            "brand_context_snapshot",
            postgresql_using="gin",
        ),
        CheckConstraint(
            "status IN ('IN_PROGRESS', 'REVIEWING', 'CERTIFIED')",
            name="audit_instances_status_check",
        ),
    )


class AuditItem(SQLModel, table=True):
    """Audit item model."""

    __tablename__ = "audit_items"

    id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(PostgresUUID(as_uuid=True), primary_key=True),
    )
    audit_instance_id: UUID = Field(
        sa_column=Column(
            PostgresUUID(as_uuid=True),
            ForeignKey("audit_instances.id", ondelete="RESTRICT"),
            nullable=False,
        )
    )
    criteria_id: UUID = Field(
        sa_column=Column(
            PostgresUUID(as_uuid=True),
            ForeignKey("sustainability_criteria.id", ondelete="RESTRICT"),
            nullable=False,
        )
    )
    triggered_by_rule_id: UUID = Field(
        sa_column=Column(
            PostgresUUID(as_uuid=True),
            ForeignKey("criteria_rules.id", ondelete="RESTRICT"),
            nullable=False,
        )
    )
    status: AuditItemStatus = Field(default=AuditItemStatus.MISSING_EVIDENCE, index=True)
    auditor_comments: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    deleted_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), index=True)
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True)),
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )

    # Relationships
    # audit_instance: AuditInstance = Relationship(back_populates="audit_items")
    # criterion: SustainabilityCriterion = Relationship()
    # triggered_by_rule: CriteriaRule = Relationship()

    __table_args__ = (
        Index("idx_audit_items_audit_criteria", "audit_instance_id", "criteria_id", unique=True),
        CheckConstraint(
            "status IN ('MISSING_EVIDENCE', 'EVIDENCE_PROVIDED', 'UNDER_REVIEW', 'ACCEPTED', 'REJECTED')",
            name="audit_items_status_check",
        ),
    )
