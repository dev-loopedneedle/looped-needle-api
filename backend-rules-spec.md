## Backend Rules Engine Specification

### Status
- **Status**: Draft
- **Owner**: Backend
- **Scope**: Rules + Evidence Claims + Audit Workflow generation APIs and persistence

### Problem Statement
Admin users need to define **Rules** that match against an audit’s inputs (`Audit.audit_data`) and produce a list of **Evidence Claims** that a brand user must upload or fill in. When an audit is created (or when the user requests it), the backend must generate an **Audit Workflow** containing the evidence requirements derived from the matched rules.

### Goals
- **Admin can manage rules** with lifecycle states: `DRAFT`, `PUBLISHED`, `DISABLED`.
- **Admin can attach Evidence Claims** to each rule.
- **Backend can evaluate rules** against an `Audit` (using `Audit.audit_data`) safely and deterministically.
- **Backend can generate and persist a workflow “requirements set”** per audit (what evidence is required, why, and when it was generated).
- **Brand users can fetch the required evidence claims** for their audit workflow.
- **Traceability/auditability**: we can answer “why is this evidence required?” (which rule(s) matched).

### Non-Goals (for this iteration)
- Full reviewer/auditor review process for submitted evidence (can be added later).
- Advanced rule scheduling/stream processing (rules are evaluated on-demand or on audit create/update).
- Arbitrary code execution or freeform Python evaluation.

---

## Domain Model

### Rule State Machine
- **States**:
  - `DRAFT`: editable, not used for matching.
  - `PUBLISHED`: used for matching; **immutable** (see versioning).
  - `DISABLED`: not used for matching.
- **Transitions**:
  - `DRAFT -> PUBLISHED`
  - `PUBLISHED -> DISABLED`
  - `DISABLED -> PUBLISHED` (optional; only if rule definition is unchanged)

### Versioning / Immutability
When a published rule needs changes, we do **clone-to-draft**:
- Editing a `PUBLISHED` rule creates a **new `Rule` row** with:
  - same `code`
  - incremented `version`
  - state `DRAFT`
  - `replaces_rule_id` pointing to the previous version (optional but recommended)
- Workflow generation stores `rule_id` + `rule_version` used, so requirements are auditable.

---

## Database Schema (PostgreSQL)

### Table: `rules`
- **Purpose**: Admin-authored matching rules and their expression.
- **Columns**
  - `id` UUID PK
  - `code` TEXT NOT NULL (stable identifier, unique per “rule family”)
  - `version` INTEGER NOT NULL (starts at 1, increments on republish via clone)
  - `name` TEXT NOT NULL
  - `description` TEXT NULL
  - `state` TEXT NOT NULL CHECK in (`DRAFT`, `PUBLISHED`, `DISABLED`)
  - `expression` TEXT NOT NULL (validated expression string; see Expression Language)
  - `expression_ast` JSONB NULL (optional: normalized/validated parsed form)
  - `created_by_user_profile_id` UUID NULL FK -> `user_profiles.id` (RESTRICT)
  - `published_at` TIMESTAMPTZ NULL
  - `disabled_at` TIMESTAMPTZ NULL
  - `created_at` TIMESTAMPTZ NOT NULL
  - `updated_at` TIMESTAMPTZ NULL
  - `replaces_rule_id` UUID NULL FK -> `rules.id` (RESTRICT) (optional)
- **Constraints/Indexes**
  - Unique: `(code, version)`
  - Index: `(state)`
  - Index: `(code)`

### Table: `evidence_claims`
- **Purpose**: Evidence requirements definitions (reusable across rules if desired).
- **Columns**
  - `id` UUID PK
  - `name` TEXT NOT NULL
  - `description` TEXT NULL
  - `category` TEXT NOT NULL (enum-like; see `EvidenceClaimCategory`)
  - `type` TEXT NOT NULL (enum-like; see `EvidenceClaimType`)
  - `weight` NUMERIC NOT NULL CHECK (`weight >= 0 AND weight <= 1`)
  - `created_by_user_profile_id` UUID NULL FK -> `user_profiles.id` (RESTRICT)
  - `created_at` TIMESTAMPTZ NOT NULL
  - `updated_at` TIMESTAMPTZ NULL
- **Notes**
  - If you prefer Evidence Claims to be fully owned by a Rule (not reusable), keep them separate but add a `rule_id` FK and drop the join table. This spec assumes **many-to-many** to allow reuse.

### Table: `rule_evidence_claims`
- **Purpose**: Many-to-many relationship between rules and evidence claims.
- **Columns**
  - `rule_id` UUID NOT NULL FK -> `rules.id` (CASCADE)
  - `evidence_claim_id` UUID NOT NULL FK -> `evidence_claims.id` (RESTRICT)
  - `sort_order` INTEGER NULL (optional)
  - `created_at` TIMESTAMPTZ NOT NULL
- **Constraints**
  - PK: `(rule_id, evidence_claim_id)`

### Table: `audit_workflows`
- **Purpose**: Represents a generated “requirements set” for an audit.
- **Current status**: Already exists with `id`, `audit_id`, timestamps.
- **Add columns**
  - `generation` INTEGER NOT NULL DEFAULT 1
  - `status` TEXT NOT NULL CHECK in (`GENERATED`, `STALE`) DEFAULT `GENERATED`
  - `generated_at` TIMESTAMPTZ NOT NULL (set on generation)
  - `engine_version` TEXT NOT NULL DEFAULT `v1`
  - `audit_data_snapshot` JSONB NOT NULL (snapshot used for evaluation)
- **Constraints/Indexes**
  - Unique: `(audit_id, generation)`
  - Index: `(audit_id)`

### Table: `audit_workflow_rule_matches`
- **Purpose**: Traceability of rule evaluation.
- **Columns**
  - `id` UUID PK
  - `audit_workflow_id` UUID NOT NULL FK -> `audit_workflows.id` (CASCADE)
  - `rule_id` UUID NOT NULL FK -> `rules.id` (RESTRICT)
  - `rule_code` TEXT NOT NULL
  - `rule_version` INTEGER NOT NULL
  - `matched` BOOLEAN NOT NULL
  - `error` TEXT NULL (evaluation error message if any)
  - `evaluated_at` TIMESTAMPTZ NOT NULL
  - `match_context` JSONB NULL (optional: debug info, extracted fields)
- **Indexes**
  - Index: `(audit_workflow_id)`
  - Index: `(rule_code, rule_version)`

### Table: `audit_workflow_required_claims`
- **Purpose**: Concrete evidence requirements for an audit workflow.
- **Columns**
  - `id` UUID PK
  - `audit_workflow_id` UUID NOT NULL FK -> `audit_workflows.id` (CASCADE)
  - `evidence_claim_id` UUID NOT NULL FK -> `evidence_claims.id` (RESTRICT)
  - `status` TEXT NOT NULL CHECK in (`REQUIRED`, `SATISFIED`) DEFAULT `REQUIRED` (minimal for v1)
  - `created_at` TIMESTAMPTZ NOT NULL
  - `updated_at` TIMESTAMPTZ NULL
- **Constraints**
  - Unique: `(audit_workflow_id, evidence_claim_id)`

### Table: `audit_workflow_required_claim_sources`
- **Purpose**: Many-to-many for “why is this claim required?” (multiple rules may require same claim).
- **Columns**
  - `audit_workflow_required_claim_id` UUID NOT NULL FK -> `audit_workflow_required_claims.id` (CASCADE)
  - `rule_id` UUID NOT NULL FK -> `rules.id` (RESTRICT)
  - `rule_code` TEXT NOT NULL
  - `rule_version` INTEGER NOT NULL
  - `created_at` TIMESTAMPTZ NOT NULL
- **Constraints**
  - PK: `(audit_workflow_required_claim_id, rule_id)`

### (Optional, recommended next): Evidence submission tables
If you want “upload or fill in” in v1, add:
- `evidence_submissions` with:
  - `audit_workflow_required_claim_id` FK
  - `submission_type` (`FILE`, `TEXT`, `URL`, `QUESTIONNAIRE`)
  - `payload` JSONB (or separate columns)
  - `status` (`DRAFT`, `SUBMITTED`)
  - timestamps
This spec keeps submissions optional because storage (S3/etc) and file APIs may be separate.

---

## Expression Language (Rule Matching)

### Decision
Use a **safe text expression language** evaluated in Python using the repo’s existing direction:
- `simpleeval`-based evaluator (see prior design under `specs/002-inference-engine-schema/`)
- No `eval`, no arbitrary imports, no attribute access beyond safe objects.

### Expression Input Contract
- Expressions are strings that evaluate to a boolean.
- Expressions reference the audit JSON via stable variables:
  - `audit` (full dict)
  - top-level shortcuts: `productInfo`, `materials`, `supplyChain`, `sustainability` (dicts; missing maps to `{}`)
- Examples:
  - `materials.get("primary") == "Cotton"`
  - `(materials.get("certifiedOrganic") == True) and (materials.get("recycledContent", 0) >= 50)`
  - `productInfo.get("auditScope") in ["Collection", "Brand-wide"]`

### Helper Functions (supported in evaluator)
- `exists(obj, path)` → bool (path like `"materials.primary"` for nested dicts)
- `get(obj, path, default=None)` → value
- `contains(items, value)` → bool
- `any_match(items, field, value)` → bool (for arrays of objects)
- `lower(s)` → string lowercasing

### Validation Rules
On create/update (draft) and publish:
- parse + evaluate against a **synthetic context** where missing fields exist as `{}` / `None`
- ensure result type is boolean
- reject expressions that attempt disallowed operations (implementation detail: restrict names, functions, and AST nodes)

### Admin Preview Endpoint

- **Endpoint**: `POST /api/v1/admin/rules/preview`
- **Auth**: Admin (`Depends(get_admin_user)`)
- **Purpose**: Validate an expression and preview which evidence claims would be required for a given `audit_data` payload (without persisting).
- **Request**
  - `expression`: string
  - `audit_data`: object (same structure as `Audit.audit_data`)
  - `evidence_claim_ids`: optional list of UUIDs (if previewing existing claims)
- **Response**
  - `valid`: boolean
  - `matched`: boolean (expression result if valid)
  - `errors`: list of strings
  - `normalized_expression`: optional string (if we normalize)

---

## API Specification (FastAPI)

### AuthZ Rules
- **Admin endpoints** require `get_admin_user`.
- **Brand users** can only access audits that belong to their brand (existing access control pattern in `AuditService.list_audits` should be reused/expanded for workflow endpoints).

### Admin: Rules

#### Create rule (draft)
- **POST** `/api/v1/admin/rules`
- **Body**
  - `code`, `name`, `description`, `expression`
  - `evidence_claims`: list of claim payloads (create new) and/or IDs (attach existing)
- **Behavior**
  - Creates `rules` row in `DRAFT`, `version=1` (or next version if code exists and latest is published).
  - Creates/links evidence claims and join rows.

#### List rules
- **GET** `/api/v1/admin/rules?state=&code=&q=&limit=&offset=`
- Returns paginated list, including `latest_version` by code if requested.

#### Get rule
- **GET** `/api/v1/admin/rules/{rule_id}`
- Includes linked evidence claims.

#### Update rule (draft only)
- **PUT** `/api/v1/admin/rules/{rule_id}`
- **Behavior**
  - Only allowed for `DRAFT`.
  - For `PUBLISHED`, return `409` with guidance to clone.

#### Clone published rule to draft
- **POST** `/api/v1/admin/rules/{rule_id}/clone`
- Creates a new `DRAFT` rule with `version = previous.version + 1`.

#### Publish rule
- **POST** `/api/v1/admin/rules/{rule_id}/publish`
- **Behavior**
  - Validates expression.
  - Sets `state=PUBLISHED`, `published_at=now`.
  - Publishing does not auto-regenerate existing workflows (see regeneration).

#### Disable rule
- **POST** `/api/v1/admin/rules/{rule_id}/disable`
- Sets `state=DISABLED`, `disabled_at=now`.

### Admin: Evidence Claim catalogs

#### Evidence claim categories and types
- **GET** `/api/v1/admin/evidence-claim-categories`
- **GET** `/api/v1/admin/evidence-claim-types`
- **Purpose**: Provide the frontend dropdown options from a single source of truth.

### Admin: Field Catalog for Rule Builder

#### List available audit fields
- **GET** `/api/v1/admin/rules/fields`
- **Response**: list of:
  - `path`: e.g. `materials.primary`
  - `label`: `Primary material`
  - `type`: `string|number|boolean|enum|object`
  - `operators`: allowed ops (`eq`, `neq`, `in`, `gte`, `lte`, `exists`, etc)
  - `enum_values`: optional list (for dropdown fields)
- **Source of truth**
  - Initially: a curated static list matching `src/audits/schemas.py` (best UX).
  - Later: can be generated from Pydantic schema metadata.

---

## Workflow Generation

### Core Endpoint
- **POST** `/api/v1/audits/{audit_id}/workflow/generate`
- **Auth**: authenticated user (`get_current_user`) + brand ownership check
- **Query params**
  - `force`: boolean (default false). If false and latest workflow is fresh for current audit data, return it.
- **Response**
  - `workflow_id`, `audit_id`, `generation`, `generated_at`
  - `required_claims`: list of evidence claims + requirement status + sources (rule code/version)
  - `rule_matches`: optional (admin only or hidden behind flag)

### Read Endpoint
- **GET** `/api/v1/audits/{audit_id}/workflow`
- Returns latest workflow (or 404 if none).

### “Freshness” / Regeneration Rule
We determine whether a workflow is stale by comparing:
- `audit_workflow.audit_data_snapshot` with current `audit.audit_data` (deep equality), or
- store a `snapshot_hash` (preferred later) and compare hashes

If different → create a new workflow generation.

### Matching Algorithm (v1)
- Load `Audit` by id.
- Build evaluation context:
  - `audit = audit.audit_data` (dict)
  - `productInfo = audit.get("productInfo", {})`, etc.
- Fetch all `rules` where `state='PUBLISHED'`.
- For each rule:
  - Evaluate `rule.expression` using the safe evaluator.
  - On exception: record `matched=false`, store `error`, continue.
  - Store a row in `audit_workflow_rule_matches`.
- Collect union of evidence claims for matched rules:
  - For each matched rule, load associated evidence claims via join.
  - Deduplicate by `evidence_claim_id`.
  - For each deduped claim, create `audit_workflow_required_claims` row.
  - For each “source” rule, create `audit_workflow_required_claim_sources` row.

### Output Contract for Required Claims
Each required claim should include:
- claim definition: `name`, `description`, `category`, `type`, `weight`
- requirement instance: `required_claim_id`, `status`
- sources: list of `{rule_id, rule_code, rule_version, rule_name}`

---

## Evidence Claim Types (v1 dropdown options)

### EvidenceClaimCategory
- `ENVIRONMENT`
- `SUSTAINABILITY`
- `SOCIAL`
- `GOVERNANCE`
- `TRACEABILITY`
- `OTHER`

### EvidenceClaimType
- `CERTIFICATE`
- `INVOICE`
- `QUESTIONNAIRE`
- `PHOTO`
- `REPORT`
- `OTHER`

---

## Error Handling
- **Invalid expressions**: reject on publish; allow saving drafts but `preview` must show errors.
- **Evaluation runtime errors** during workflow generation:
  - Do not fail the whole generation.
  - Record `audit_workflow_rule_matches.error`.
  - Continue evaluating other rules.

---

## Observability
- Log workflow generation with request id + audit id + generation + counts:
  - number of rules evaluated
  - number matched
  - number of required claims
  - number of evaluation errors

---

## Performance Notes
- v1 evaluates rules in Python in-process. This is fine for early scale and simplicity.
- If rule count grows large, we can add:
  - caching of compiled expressions
  - async batching for DB reads (preload rule->claims mapping)
  - optional SQL pushdown for simple predicates using JSONB operators (only when safe)

---

## Implementation Plan (Backend)
- Add new domain module `src/rules/`:
  - `models.py`, `schemas.py`, `router.py`, `service.py`
- Extend `src/audit_workflows/models.py` with generation + snapshot fields (plus new models for match/required claims).
- Add Alembic migration:
  - create new tables + add columns
  - update `alembic/env.py` imports to include new models
- Add endpoints to `src/main.py` via router include.

