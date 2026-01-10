# Data Model: Rules Engine for Audit Certification

**Branch**: `004-rules-engine` | **Date**: 2026-01-06  
**Spec**: `/specs/004-rules-engine/spec.md`

## Entities

- **Rule**
  - `id` (UUID, PK)
  - `code` (TEXT, globally unique stable identifier)
  - `version` (INT, >=1; immutable per publish)
  - `name` (TEXT)
  - `description` (TEXT)
  - `state` (ENUM: DRAFT, PUBLISHED, DISABLED)
  - `expression` (TEXT; validated syntax/type/sample eval)
  - `expression_ast` (JSONB, optional normalized form)
  - `created_by_user_profile_id` (UUID FK → user_profiles.id)
  - `published_at`, `disabled_at`, `created_at`, `updated_at` (TIMESTAMPTZ)
  - `replaces_rule_id` (UUID FK → rules.id, optional)
  - Constraints: unique(code), unique(code, version); index on state/code

- **EvidenceClaim**
  - `id` (UUID, PK)
  - `name` (TEXT)
  - `description` (TEXT)
  - `category` (ENUM: ENVIRONMENT, SUSTAINABILITY, SOCIAL, GOVERNANCE, TRACEABILITY, OTHER)
  - `type` (ENUM: CERTIFICATE, INVOICE, QUESTIONNAIRE, PHOTO, REPORT, OTHER)
  - `weight` (NUMERIC, 0..1)
  - `created_by_user_profile_id` (UUID FK → user_profiles.id)
  - `created_at`, `updated_at` (TIMESTAMPTZ)

- **RuleEvidenceClaim** (join)
  - `rule_id` (UUID FK → rules.id, CASCADE)
  - `evidence_claim_id` (UUID FK → evidence_claims.id, RESTRICT)
  - `sort_order` (INT, optional)
  - `created_at` (TIMESTAMPTZ)
  - PK: (rule_id, evidence_claim_id)

- **AuditWorkflow**
  - Extends existing table
  - `generation` (INT, default 1)
  - `status` (ENUM: GENERATED, STALE optional)
  - `generated_at` (TIMESTAMPTZ)
  - `engine_version` (TEXT, default v1)
  - `audit_data_snapshot` (JSONB)
  - Unique: (audit_id, generation)

- **AuditWorkflowRuleMatch**
  - `id` (UUID, PK)
  - `audit_workflow_id` (UUID FK → audit_workflows.id, CASCADE)
  - `rule_id` (UUID FK → rules.id, RESTRICT)
  - `rule_code` (TEXT)
  - `rule_version` (INT)
  - `matched` (BOOL)
  - `error` (TEXT, nullable)
  - `evaluated_at` (TIMESTAMPTZ)
  - `match_context` (JSONB, optional)

- **AuditWorkflowRequiredClaim**
  - `id` (UUID, PK)
  - `audit_workflow_id` (UUID FK → audit_workflows.id, CASCADE)
  - `evidence_claim_id` (UUID FK → evidence_claims.id, RESTRICT)
  - `status` (ENUM: REQUIRED, SATISFIED default REQUIRED)
  - `created_at`, `updated_at` (TIMESTAMPTZ)
  - Unique: (audit_workflow_id, evidence_claim_id)

- **AuditWorkflowRequiredClaimSource**
  - `audit_workflow_required_claim_id` (UUID FK → audit_workflow_required_claims.id, CASCADE)
  - `rule_id` (UUID FK → rules.id, RESTRICT)
  - `rule_code` (TEXT)
  - `rule_version` (INT)
  - `created_at` (TIMESTAMPTZ)
  - PK: (audit_workflow_required_claim_id, rule_id)

## State & Rules

- Rule states: DRAFT (editable), PUBLISHED (immutable, used for matching), DISABLED (not used).
- Workflow regeneration: allowed only for draft audits; creates new generation; published audits immutable.
- Manual trigger only for workflow generation.
- Rule expressions: validated (syntax/type/sample eval) before publish; evaluated safely; expressions not exposed to brand users.
- Traceability: rule name/code shown to brand users; expressions hidden.

## Relationships

- Rule ↔ EvidenceClaim: many-to-many via RuleEvidenceClaim.
- AuditWorkflow → Audit: many-to-one (existing).
- AuditWorkflow → AuditWorkflowRuleMatch: one-to-many.
- AuditWorkflow → AuditWorkflowRequiredClaim: one-to-many.
- AuditWorkflowRequiredClaim → AuditWorkflowRequiredClaimSource: one-to-many (sources referencing rules).

## Validation & Constraints

- Evidence weight in [0,1].
- Enum validation for categories/types/states.
- Unique rule code globally; version increments per publish/clone.
- Unique required claim per workflow; sources capture all triggering rules.

