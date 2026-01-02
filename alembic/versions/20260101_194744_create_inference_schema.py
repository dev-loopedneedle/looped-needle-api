"""create inference schema

Revision ID: 002_create_inference_schema
Revises: 001_create_audit_table
Create Date: 2026-01-01 19:47:44.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "002_create_inference_schema"
down_revision: Union[str, None] = "001_create_audit_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - create inference engine tables."""
    # Enable UUID extension
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # Create brands table
    op.create_table(
        "brands",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("registration_country", sa.String(), nullable=False),
        sa.Column("company_size", sa.String(), nullable=False),
        sa.Column("target_markets", postgresql.ARRAY(sa.String()), nullable=False, server_default="{}"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_brands_name", "brands", ["name"])
    op.create_index("idx_brands_deleted_at", "brands", ["deleted_at"])
    op.create_index("idx_brands_created_at", "brands", ["created_at"])
    op.create_check_constraint(
        "brands_company_size_check",
        "brands",
        "company_size IN ('Micro', 'SME', 'Large')",
    )

    # Create products table
    op.create_table(
        "products",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("brand_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("materials_composition", postgresql.JSONB(), nullable=False),
        sa.Column("manufacturing_processes", postgresql.ARRAY(sa.String()), nullable=False, server_default="{}"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["brand_id"], ["brands.id"], ondelete="RESTRICT"),
    )
    op.create_index("idx_products_brand_id", "products", ["brand_id"])
    op.create_index("idx_products_deleted_at", "products", ["deleted_at"])
    op.create_index("idx_products_materials_composition_gin", "products", ["materials_composition"], postgresql_using="gin")

    # Create supply_chain_nodes table
    op.create_table(
        "supply_chain_nodes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("brand_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("country", sa.String(), nullable=False),
        sa.Column("tier_level", sa.Integer(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["brand_id"], ["brands.id"], ondelete="RESTRICT"),
    )
    op.create_index("idx_supply_chain_nodes_brand_id", "supply_chain_nodes", ["brand_id"])
    op.create_index("idx_supply_chain_nodes_deleted_at", "supply_chain_nodes", ["deleted_at"])
    op.create_index("idx_supply_chain_nodes_tier_level", "supply_chain_nodes", ["tier_level"])
    op.create_check_constraint(
        "supply_chain_nodes_tier_level_check",
        "supply_chain_nodes",
        "tier_level > 0",
    )

    # Create sustainability_criteria table
    op.create_table(
        "sustainability_criteria",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("domain", sa.String(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_sustainability_criteria_code", "sustainability_criteria", ["code"], unique=True)
    op.create_index("idx_sustainability_criteria_domain", "sustainability_criteria", ["domain"])
    op.create_index("idx_sustainability_criteria_deleted_at", "sustainability_criteria", ["deleted_at"])
    op.create_check_constraint(
        "sustainability_criteria_domain_check",
        "sustainability_criteria",
        "domain IN ('Social', 'Environmental', 'Governance')",
    )

    # Create criteria_rules table
    op.create_table(
        "criteria_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("criteria_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rule_name", sa.String(), nullable=False),
        sa.Column("condition_expression", sa.String(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["criteria_id"], ["sustainability_criteria.id"], ondelete="RESTRICT"),
    )
    op.create_index("idx_criteria_rules_criteria_id", "criteria_rules", ["criteria_id"])
    op.create_index("idx_criteria_rules_priority", "criteria_rules", ["priority"])
    op.create_index("idx_criteria_rules_deleted_at", "criteria_rules", ["deleted_at"])
    op.create_index("idx_criteria_rules_criteria_priority", "criteria_rules", ["criteria_id", "priority"])

    # Create questionnaire_definitions table
    op.create_table(
        "questionnaire_definitions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("form_schema", postgresql.JSONB(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_questionnaire_definitions_is_active", "questionnaire_definitions", ["is_active"])
    op.create_index("idx_questionnaire_definitions_deleted_at", "questionnaire_definitions", ["deleted_at"])
    op.create_index("idx_questionnaire_definitions_form_schema_gin", "questionnaire_definitions", ["form_schema"], postgresql_using="gin")

    # Create audit_instances table
    op.create_table(
        "audit_instances",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("brand_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("questionnaire_definition_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="IN_PROGRESS"),
        sa.Column("scoping_responses", postgresql.JSONB(), nullable=False),
        sa.Column("brand_context_snapshot", postgresql.JSONB(), nullable=False),
        sa.Column("overall_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["brand_id"], ["brands.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["questionnaire_definition_id"], ["questionnaire_definitions.id"], ondelete="RESTRICT"),
    )
    op.create_index("idx_audit_instances_brand_id", "audit_instances", ["brand_id"])
    op.create_index("idx_audit_instances_status", "audit_instances", ["status"])
    op.create_index("idx_audit_instances_created_at", "audit_instances", ["created_at"])
    op.create_index("idx_audit_instances_deleted_at", "audit_instances", ["deleted_at"])
    op.create_index("idx_audit_instances_scoping_responses_gin", "audit_instances", ["scoping_responses"], postgresql_using="gin")
    op.create_index("idx_audit_instances_brand_context_snapshot_gin", "audit_instances", ["brand_context_snapshot"], postgresql_using="gin")
    op.create_check_constraint(
        "audit_instances_status_check",
        "audit_instances",
        "status IN ('IN_PROGRESS', 'REVIEWING', 'CERTIFIED')",
    )

    # Create audit_items table
    op.create_table(
        "audit_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("audit_instance_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("criteria_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("triggered_by_rule_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="MISSING_EVIDENCE"),
        sa.Column("auditor_comments", sa.String(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["audit_instance_id"], ["audit_instances.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["criteria_id"], ["sustainability_criteria.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["triggered_by_rule_id"], ["criteria_rules.id"], ondelete="RESTRICT"),
    )
    op.create_index("idx_audit_items_audit_instance_id", "audit_items", ["audit_instance_id"])
    op.create_index("idx_audit_items_criteria_id", "audit_items", ["criteria_id"])
    op.create_index("idx_audit_items_status", "audit_items", ["status"])
    op.create_index("idx_audit_items_deleted_at", "audit_items", ["deleted_at"])
    op.create_index("idx_audit_items_instance_criteria_unique", "audit_items", ["audit_instance_id", "criteria_id"], unique=True)
    op.create_check_constraint(
        "audit_items_status_check",
        "audit_items",
        "status IN ('MISSING_EVIDENCE', 'EVIDENCE_PROVIDED', 'UNDER_REVIEW', 'ACCEPTED', 'REJECTED')",
    )

    # Create evidence_files table
    op.create_table(
        "evidence_files",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("brand_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("file_path", sa.String(), nullable=False),
        sa.Column("file_name", sa.String(), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=True),
        sa.Column("mime_type", sa.String(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["brand_id"], ["brands.id"], ondelete="RESTRICT"),
    )
    op.create_index("idx_evidence_files_brand_id", "evidence_files", ["brand_id"])
    op.create_index("idx_evidence_files_uploaded_at", "evidence_files", ["uploaded_at"])
    op.create_index("idx_evidence_files_deleted_at", "evidence_files", ["deleted_at"])

    # Create audit_item_evidence_links table
    op.create_table(
        "audit_item_evidence_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("audit_item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("evidence_file_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="PENDING"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["audit_item_id"], ["audit_items.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["evidence_file_id"], ["evidence_files.id"], ondelete="RESTRICT"),
    )
    op.create_index("idx_audit_item_evidence_links_audit_item_id", "audit_item_evidence_links", ["audit_item_id"])
    op.create_index("idx_audit_item_evidence_links_evidence_file_id", "audit_item_evidence_links", ["evidence_file_id"])
    op.create_index("idx_audit_item_evidence_links_status", "audit_item_evidence_links", ["status"])
    op.create_index("idx_audit_item_evidence_links_deleted_at", "audit_item_evidence_links", ["deleted_at"])
    op.create_index("idx_audit_item_evidence_links_item_file_unique", "audit_item_evidence_links", ["audit_item_id", "evidence_file_id"], unique=True)
    op.create_check_constraint(
        "audit_item_evidence_links_status_check",
        "audit_item_evidence_links",
        "status IN ('PENDING', 'ACCEPTED', 'REJECTED')",
    )


def downgrade() -> None:
    """Downgrade schema - drop inference engine tables."""
    op.drop_table("audit_item_evidence_links")
    op.drop_table("evidence_files")
    op.drop_table("audit_items")
    op.drop_table("audit_instances")
    op.drop_table("questionnaire_definitions")
    op.drop_table("criteria_rules")
    op.drop_table("sustainability_criteria")
    op.drop_table("supply_chain_nodes")
    op.drop_table("products")
    op.drop_table("brands")

