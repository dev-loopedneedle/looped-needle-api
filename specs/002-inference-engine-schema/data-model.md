# Data Model: Dynamic Audit Inference Engine

**Date**: 2025-01-27  
**Feature**: 002-inference-engine-schema

## Overview

This document defines the database schema for the inference engine module. All tables use UUID primary keys, PostgreSQL-specific types (JSONB, arrays), and follow the existing naming conventions (lower_case_snake, singular table names).

## Entity Relationships

```
Brand
├── has_many Products
├── has_many SupplyChainNodes
├── has_many AuditInstances
└── has_many EvidenceFiles

SustainabilityCriterion
└── has_many CriteriaRules

QuestionnaireDefinition
└── referenced_by AuditInstances

AuditInstance
├── belongs_to Brand
├── references QuestionnaireDefinition
└── has_many AuditItems

AuditItem
├── belongs_to AuditInstance
├── references SustainabilityCriterion
├── references CriteriaRule (triggered_by_rule_id)
└── has_many AuditItemEvidenceLinks

EvidenceFile
├── belongs_to Brand
└── has_many AuditItemEvidenceLinks

AuditItemEvidenceLink
├── belongs_to AuditItem
└── belongs_to EvidenceFile
```

## Tables

### brands

Represents an organization seeking certification.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY, DEFAULT uuid_generate_v4() | Unique identifier |
| name | TEXT | NOT NULL, INDEX | Brand name |
| registration_country | TEXT | NOT NULL | ISO country code |
| company_size | TEXT | NOT NULL, CHECK | Enum: 'Micro', 'SME', 'Large' |
| target_markets | TEXT[] | NOT NULL, DEFAULT '{}' | Array of ISO country codes |
| deleted_at | TIMESTAMP WITH TIME ZONE | NULLABLE, INDEX | Soft delete timestamp |
| created_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW(), INDEX | Creation timestamp |
| updated_at | TIMESTAMP WITH TIME ZONE | NULLABLE | Last update timestamp |

**Indexes**:
- `idx_brands_name` on `name`
- `idx_brands_deleted_at` on `deleted_at` (for soft delete filtering)
- `idx_brands_created_at` on `created_at`

**Constraints**:
- `company_size` CHECK constraint: `company_size IN ('Micro', 'SME', 'Large')`

**Relationships**:
- One-to-many with `products` (brand_id)
- One-to-many with `supply_chain_nodes` (brand_id)
- One-to-many with `audit_instances` (brand_id)
- One-to-many with `evidence_files` (brand_id)

---

### products

Represents a product manufactured or sold by a brand.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY, DEFAULT uuid_generate_v4() | Unique identifier |
| brand_id | UUID | NOT NULL, FOREIGN KEY -> brands.id | Brand reference |
| name | TEXT | NOT NULL | Product name |
| category | TEXT | NOT NULL | Product category (e.g., 'Apparel', 'Footwear') |
| materials_composition | JSONB | NOT NULL | Array of material objects with material and percent |
| manufacturing_processes | TEXT[] | NOT NULL, DEFAULT '{}' | Array of process names |
| deleted_at | TIMESTAMP WITH TIME ZONE | NULLABLE, INDEX | Soft delete timestamp |
| created_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | Creation timestamp |
| updated_at | TIMESTAMP WITH TIME ZONE | NULLABLE | Last update timestamp |

**Indexes**:
- `idx_products_brand_id` on `brand_id`
- `idx_products_deleted_at` on `deleted_at`
- GIN index on `materials_composition` for JSONB queries

**Constraints**:
- Foreign key: `brand_id` REFERENCES `brands(id)` ON DELETE RESTRICT

**Relationships**:
- Many-to-one with `brands` (brand_id)

**JSONB Structure** (materials_composition):
```json
[
  {"material": "Cotton", "percent": 80},
  {"material": "Polyester", "percent": 20}
]
```

---

### supply_chain_nodes

Represents a node in the brand's supply chain.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY, DEFAULT uuid_generate_v4() | Unique identifier |
| brand_id | UUID | NOT NULL, FOREIGN KEY -> brands.id | Brand reference |
| role | TEXT | NOT NULL | Node role (e.g., 'CutAndSew', 'FabricMill') |
| country | TEXT | NOT NULL | ISO country code |
| tier_level | INTEGER | NOT NULL, CHECK | Tier level (1, 2, 3, etc.) |
| deleted_at | TIMESTAMP WITH TIME ZONE | NULLABLE, INDEX | Soft delete timestamp |
| created_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | Creation timestamp |
| updated_at | TIMESTAMP WITH TIME ZONE | NULLABLE | Last update timestamp |

**Indexes**:
- `idx_supply_chain_nodes_brand_id` on `brand_id`
- `idx_supply_chain_nodes_deleted_at` on `deleted_at`
- `idx_supply_chain_nodes_tier_level` on `tier_level`

**Constraints**:
- Foreign key: `brand_id` REFERENCES `brands(id)` ON DELETE RESTRICT
- `tier_level` CHECK constraint: `tier_level > 0`

**Relationships**:
- Many-to-one with `brands` (brand_id)

---

### sustainability_criteria

Represents a master requirement that may apply to audits.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY, DEFAULT uuid_generate_v4() | Unique identifier |
| code | TEXT | NOT NULL, UNIQUE, INDEX | Unique criterion code (e.g., 'ENV-001') |
| name | TEXT | NOT NULL | Criterion name |
| description | TEXT | NOT NULL | Criterion description |
| domain | TEXT | NOT NULL, CHECK | Enum: 'Social', 'Environmental', 'Governance' |
| deleted_at | TIMESTAMP WITH TIME ZONE | NULLABLE, INDEX | Soft delete timestamp |
| created_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | Creation timestamp |
| updated_at | TIMESTAMP WITH TIME ZONE | NULLABLE | Last update timestamp |

**Indexes**:
- `idx_sustainability_criteria_code` UNIQUE on `code`
- `idx_sustainability_criteria_domain` on `domain`
- `idx_sustainability_criteria_deleted_at` on `deleted_at`

**Constraints**:
- `code` UNIQUE constraint
- `domain` CHECK constraint: `domain IN ('Social', 'Environmental', 'Governance')`

**Relationships**:
- One-to-many with `criteria_rules` (criteria_id)

---

### criteria_rules

Represents a logic condition that determines when a criterion applies.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY, DEFAULT uuid_generate_v4() | Unique identifier |
| criteria_id | UUID | NOT NULL, FOREIGN KEY -> sustainability_criteria.id | Criterion reference |
| rule_name | TEXT | NOT NULL | Admin reference name |
| condition_expression | TEXT | NOT NULL | Python-like expression string |
| priority | INTEGER | NOT NULL, DEFAULT 0 | Priority (higher = more important) |
| deleted_at | TIMESTAMP WITH TIME ZONE | NULLABLE, INDEX | Soft delete timestamp |
| created_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | Creation timestamp |
| updated_at | TIMESTAMP WITH TIME ZONE | NULLABLE | Last update timestamp |

**Indexes**:
- `idx_criteria_rules_criteria_id` on `criteria_id`
- `idx_criteria_rules_priority` on `priority` (for ordering)
- `idx_criteria_rules_deleted_at` on `deleted_at`
- Composite index: `(criteria_id, priority)` for rule queries

**Constraints**:
- Foreign key: `criteria_id` REFERENCES `sustainability_criteria(id)` ON DELETE RESTRICT

**Relationships**:
- Many-to-one with `sustainability_criteria` (criteria_id)

**Example condition_expression**:
```
context.material == 'Leather' && scope.season == 'SS24'
```

---

### questionnaire_definitions

Represents a form schema for scoping questionnaires.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY, DEFAULT uuid_generate_v4() | Unique identifier |
| name | TEXT | NOT NULL | Questionnaire name |
| form_schema | JSONB | NOT NULL | Form structure (questions, options, etc.) |
| is_active | BOOLEAN | NOT NULL, DEFAULT true, INDEX | Active status |
| deleted_at | TIMESTAMP WITH TIME ZONE | NULLABLE, INDEX | Soft delete timestamp |
| created_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | Creation timestamp |
| updated_at | TIMESTAMP WITH TIME ZONE | NULLABLE | Last update timestamp |

**Indexes**:
- `idx_questionnaire_definitions_is_active` on `is_active`
- `idx_questionnaire_definitions_deleted_at` on `deleted_at`
- GIN index on `form_schema` for JSONB queries

**Relationships**:
- Referenced by `audit_instances` (questionnaire_definition_id)

**JSONB Structure** (form_schema):
```json
[
  {
    "id": "audit_scope_type",
    "label": "What type of certification are you seeking?",
    "type": "select",
    "options": [
      {"value": "collection_specific", "label": "Specific Collection"},
      {"value": "brand_level", "label": "Full Brand Level"}
    ],
    "description": "..."
  },
  ...
]
```

---

### audit_instances

Represents a specific audit execution.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY, DEFAULT uuid_generate_v4() | Unique identifier |
| brand_id | UUID | NOT NULL, FOREIGN KEY -> brands.id | Brand reference |
| questionnaire_definition_id | UUID | NOT NULL, FOREIGN KEY -> questionnaire_definitions.id | Questionnaire reference |
| status | TEXT | NOT NULL, DEFAULT 'IN_PROGRESS', CHECK, INDEX | Status enum |
| scoping_responses | JSONB | NOT NULL | Questionnaire answers |
| brand_context_snapshot | JSONB | NOT NULL | Snapshot of brand data at creation |
| overall_score | NUMERIC(5,2) | NULLABLE | Overall audit score (0-100) |
| deleted_at | TIMESTAMP WITH TIME ZONE | NULLABLE, INDEX | Soft delete timestamp |
| created_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW(), INDEX | Creation timestamp |
| updated_at | TIMESTAMP WITH TIME ZONE | NULLABLE | Last update timestamp |

**Indexes**:
- `idx_audit_instances_brand_id` on `brand_id`
- `idx_audit_instances_status` on `status`
- `idx_audit_instances_created_at` on `created_at`
- `idx_audit_instances_deleted_at` on `deleted_at`
- GIN indexes on `scoping_responses` and `brand_context_snapshot`

**Constraints**:
- Foreign key: `brand_id` REFERENCES `brands(id)` ON DELETE RESTRICT
- Foreign key: `questionnaire_definition_id` REFERENCES `questionnaire_definitions(id)` ON DELETE RESTRICT
- `status` CHECK constraint: `status IN ('IN_PROGRESS', 'REVIEWING', 'CERTIFIED')`

**Relationships**:
- Many-to-one with `brands` (brand_id)
- Many-to-one with `questionnaire_definitions` (questionnaire_definition_id)
- One-to-many with `audit_items` (audit_instance_id)

**State Transitions**:
- Forward-only: IN_PROGRESS → REVIEWING → CERTIFIED
- Can skip: IN_PROGRESS → CERTIFIED
- Cannot revert: CERTIFIED and REVIEWING are terminal

---

### audit_items

Represents a single requirement in an audit checklist.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY, DEFAULT uuid_generate_v4() | Unique identifier |
| audit_instance_id | UUID | NOT NULL, FOREIGN KEY -> audit_instances.id | Audit instance reference |
| criteria_id | UUID | NOT NULL, FOREIGN KEY -> sustainability_criteria.id | Criterion reference |
| triggered_by_rule_id | UUID | NOT NULL, FOREIGN KEY -> criteria_rules.id | Rule that triggered this item |
| status | TEXT | NOT NULL, DEFAULT 'MISSING_EVIDENCE', CHECK, INDEX | Status enum |
| auditor_comments | TEXT | NULLABLE | Auditor notes/comments |
| deleted_at | TIMESTAMP WITH TIME ZONE | NULLABLE, INDEX | Soft delete timestamp |
| created_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | Creation timestamp |
| updated_at | TIMESTAMP WITH TIME ZONE | NULLABLE | Last update timestamp |

**Indexes**:
- `idx_audit_items_audit_instance_id` on `audit_instance_id`
- `idx_audit_items_criteria_id` on `criteria_id`
- `idx_audit_items_status` on `status`
- `idx_audit_items_deleted_at` on `deleted_at`
- Composite index: `(audit_instance_id, criteria_id)` UNIQUE to prevent duplicates

**Constraints**:
- Foreign key: `audit_instance_id` REFERENCES `audit_instances(id)` ON DELETE RESTRICT
- Foreign key: `criteria_id` REFERENCES `sustainability_criteria(id)` ON DELETE RESTRICT
- Foreign key: `triggered_by_rule_id` REFERENCES `criteria_rules(id)` ON DELETE RESTRICT
- `status` CHECK constraint: `status IN ('MISSING_EVIDENCE', 'EVIDENCE_PROVIDED', 'UNDER_REVIEW', 'ACCEPTED', 'REJECTED')`
- UNIQUE constraint: `(audit_instance_id, criteria_id)` - one item per criterion per audit

**Relationships**:
- Many-to-one with `audit_instances` (audit_instance_id)
- Many-to-one with `sustainability_criteria` (criteria_id)
- Many-to-one with `criteria_rules` (triggered_by_rule_id)
- One-to-many with `audit_item_evidence_links` (audit_item_id)

**State Transitions**:
- Forward-only: MISSING_EVIDENCE → EVIDENCE_PROVIDED → UNDER_REVIEW → ACCEPTED/REJECTED
- Cannot revert: ACCEPTED and REJECTED are terminal

---

### evidence_files

Represents an uploaded evidence document.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY, DEFAULT uuid_generate_v4() | Unique identifier |
| brand_id | UUID | NOT NULL, FOREIGN KEY -> brands.id | Brand reference |
| file_path | TEXT | NOT NULL | Relative file path |
| file_name | TEXT | NOT NULL | Original file name |
| file_size | BIGINT | NULLABLE | File size in bytes |
| mime_type | TEXT | NULLABLE | MIME type |
| deleted_at | TIMESTAMP WITH TIME ZONE | NULLABLE, INDEX | Soft delete timestamp |
| uploaded_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW(), INDEX | Upload timestamp |
| created_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | Creation timestamp |
| updated_at | TIMESTAMP WITH TIME ZONE | NULLABLE | Last update timestamp |

**Indexes**:
- `idx_evidence_files_brand_id` on `brand_id`
- `idx_evidence_files_uploaded_at` on `uploaded_at`
- `idx_evidence_files_deleted_at` on `deleted_at`

**Constraints**:
- Foreign key: `brand_id` REFERENCES `brands(id)` ON DELETE RESTRICT

**Relationships**:
- Many-to-one with `brands` (brand_id)
- One-to-many with `audit_item_evidence_links` (evidence_file_id)

---

### audit_item_evidence_links

Represents the association between an audit item and evidence file (many-to-many).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY, DEFAULT uuid_generate_v4() | Unique identifier |
| audit_item_id | UUID | NOT NULL, FOREIGN KEY -> audit_items.id | Audit item reference |
| evidence_file_id | UUID | NOT NULL, FOREIGN KEY -> evidence_files.id | Evidence file reference |
| status | TEXT | NOT NULL, DEFAULT 'PENDING', CHECK, INDEX | Link status enum |
| deleted_at | TIMESTAMP WITH TIME ZONE | NULLABLE, INDEX | Soft delete timestamp |
| created_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | Creation timestamp |
| updated_at | TIMESTAMP WITH TIME ZONE | NULLABLE | Last update timestamp |

**Indexes**:
- `idx_audit_item_evidence_links_audit_item_id` on `audit_item_id`
- `idx_audit_item_evidence_links_evidence_file_id` on `evidence_file_id`
- `idx_audit_item_evidence_links_status` on `status`
- `idx_audit_item_evidence_links_deleted_at` on `deleted_at`
- Composite UNIQUE index: `(audit_item_id, evidence_file_id)` to prevent duplicates

**Constraints**:
- Foreign key: `audit_item_id` REFERENCES `audit_items(id)` ON DELETE RESTRICT
- Foreign key: `evidence_file_id` REFERENCES `evidence_files(id)` ON DELETE RESTRICT
- `status` CHECK constraint: `status IN ('PENDING', 'ACCEPTED', 'REJECTED')`
- UNIQUE constraint: `(audit_item_id, evidence_file_id)` - one link per item-file pair

**Relationships**:
- Many-to-one with `audit_items` (audit_item_id)
- Many-to-one with `evidence_files` (evidence_file_id)

---

## Validation Rules

### Referential Integrity

1. **Cannot delete entities referenced by audit items**:
   - `brands` referenced by `audit_instances.brand_id`
   - `sustainability_criteria` referenced by `audit_items.criteria_id`
   - `criteria_rules` referenced by `audit_items.triggered_by_rule_id`
   - `products` referenced in `audit_instances.brand_context_snapshot` (soft check)
   - `supply_chain_nodes` referenced in `audit_instances.brand_context_snapshot` (soft check)

2. **Cannot delete entities referenced by evidence links**:
   - `audit_items` referenced by `audit_item_evidence_links.audit_item_id`
   - `evidence_files` referenced by `audit_item_evidence_links.evidence_file_id`

3. **Cascade prevention**: All foreign keys use `ON DELETE RESTRICT` to prevent accidental deletions.

### Soft Delete Logic

- Entities with `deleted_at IS NOT NULL` are considered deleted
- Queries should filter: `WHERE deleted_at IS NULL`
- Deletion check: Before soft deleting, verify no references exist
- If referenced, raise exception; otherwise, set `deleted_at = NOW()`

### State Transition Validation

- **AuditInstance**: Forward-only transitions, validated in service layer
- **AuditItem**: Forward-only transitions, validated in service layer
- Database CHECK constraints provide backup validation

## Migration Notes

1. Enable UUID extension: `CREATE EXTENSION IF NOT EXISTS "uuid-ossp";`
2. Create tables in dependency order (brands first, then referencing tables)
3. Add indexes after table creation for performance
4. Add GIN indexes for JSONB columns that will be queried
5. Add CHECK constraints for enums and validation rules
6. All foreign keys use `ON DELETE RESTRICT` for referential integrity

