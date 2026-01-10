# Implementation Plan: Rules Engine for Audit Certification

**Branch**: `004-rules-engine` | **Date**: 2026-01-06 | **Spec**: `/specs/004-rules-engine/spec.md`  
**Input**: Feature specification from `/specs/004-rules-engine/spec.md`

## Summary

Deliver a rules engine that lets admins author and publish globally-unique rules (draft/published/disabled) with safe, validated expressions over `audit_data`, attach reusable evidence claims, and generate per-audit workflows on manual trigger. Workflow generation evaluates published rules, produces required evidence claims with traceability (rule name/code), creates new generations for draft audits (published audits immutable), and preserves audit-data snapshots.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: FastAPI, SQLModel/SQLAlchemy (async), Alembic, Pydantic v2, simpleeval-based evaluator, httpx (tests)  
**Storage**: PostgreSQL (JSONB for audit_data, new tables for rules/evidence/workflow artifacts)  
**Testing**: pytest with httpx.AsyncClient; tests mirror domain structure  
**Target Platform**: Linux server (FastAPI)  
**Project Type**: Web API (FastAPI, domain-driven)  
**Performance Goals**: Workflow generation ≤10s for ≤100 published rules; viewing required evidence ≤2s; traceability 100% accuracy  
**Constraints**: Manual trigger only; published audits immutable (no regeneration); rule expressions validated (syntax + type + sample eval); rule codes globally unique; brand users see rule name/code only  
**Scale/Scope**: Early-stage—tens to low hundreds of rules; per-audit workflows small (dozens of claims)

## Constitution Check

- **Domain-Driven Structure**: Will add new `src/rules/` domain plus extend `src/audit_workflows/`; follows required structure. ✅  
- **Async-First**: FastAPI async routes/services; async SQLModel; no blocking I/O. ✅  
- **Pydantic Models**: Request/response schemas for all endpoints; `response_model`, `status_code`, `summary`, `description`, `tags`. ✅  
- **Dependency Injection**: DB sessions, auth, and services via FastAPI dependencies; reuse existing patterns. ✅  
- **SQL-First**: Use SQL for joins/filtering; JSONB operators where applicable; avoid Python-side heavy transforms. ✅  
- **Testing**: Async clients (httpx.AsyncClient); tests mirror domains. ✅  
- **Code Quality**: Ruff check/format; adhere to existing tooling. ✅  
- **Database Conventions**: lower_snake_case, singular tables, `_at` for timestamps, explicit FK/index names; static, revertable migrations. ✅  
- **RESTful Design**: RESTful endpoints with correct methods/status codes and OpenAPI metadata. ✅  
- **External Services**: None new. N/A

## Project Structure

### Documentation (this feature)

```text
specs/004-rules-engine/
├── plan.md          # This file
├── research.md      # Phase 0 output
├── data-model.md    # Phase 1 output
├── quickstart.md    # Phase 1 output
├── contracts/       # Phase 1 output (OpenAPI snippets)
└── tasks.md         # From /speckit.tasks (Phase 2)
```

### Source Code (repository root)

```text
src/
├── rules/
│   ├── router.py        # Admin CRUD/publish/disable/clone/preview
│   ├── schemas.py       # Pydantic schemas for rules/claims
│   ├── models.py        # SQLModel tables: rules, evidence_claims, rule_evidence_claims
│   ├── service.py       # Rule CRUD, publish, preview evaluator
│   ├── dependencies.py
│   ├── exceptions.py
│   ├── constants.py
│   └── utils.py         # Expression helpers (optional)
├── audit_workflows/
│   ├── models.py        # Extend with generations, snapshots, matches, required_claims, sources
│   ├── router.py        # Workflow generate/read endpoints
│   ├── schemas.py       # Workflow responses
│   ├── service.py       # Generation logic, evaluator invocation
├── audits/              # Existing audit domain (audit_data)
├── auth/, brands/, ...  # Existing domains
├── main.py              # Include new routers

tests/
├── rules/
│   ├── test_router.py
│   ├── test_service.py
├── audit_workflows/
│   ├── test_router.py
│   ├── test_service.py
└── contract/
    ├── test_rules_api.py
    └── test_workflow_api.py
```

**Structure Decision**: New `rules` domain; extend `audit_workflows` domain; reuse existing `audits` for audit_data input.

## Complexity Tracking

No constitution violations anticipated; section not used.

## Phase 0: Research (Complete)

- Clarifications resolved in spec: manual trigger; validation depth (syntax+type+sample eval); regeneration creates new generations and only for draft audits; rule codes globally unique; brand users see rule name/code only.
- No additional unknowns; research.md captures decisions and rationale.

## Phase 1: Design & Contracts

**Data Model (data-model.md)**  
- Add tables: `rules`, `evidence_claims`, `rule_evidence_claims`, extend `audit_workflows` with generation/snapshot fields, plus `audit_workflow_rule_matches`, `audit_workflow_required_claims`, `audit_workflow_required_claim_sources`.  
- State machines: rule states (draft/published/disabled); workflow status (generated/stale optional); published audits immutable.  
- Constraints: rule code globally unique; evidence claim enums (category/type); weight 0..1; unique (audit_workflow_id, evidence_claim_id).

**API Contracts (contracts/)**  
- Admin (auth: admin):  
  - POST /api/v1/admin/rules (create draft)  
  - GET /api/v1/admin/rules (list/filter)  
  - GET /api/v1/admin/rules/{id}  
  - PUT /api/v1/admin/rules/{id} (draft only)  
  - POST /api/v1/admin/rules/{id}/clone  
  - POST /api/v1/admin/rules/{id}/publish  
  - POST /api/v1/admin/rules/{id}/disable  
  - POST /api/v1/admin/rules/preview (expression validation/test)  
  - GET /api/v1/admin/evidence-claim-categories | /types (dropdowns)  
- Audit workflows (auth: brand or admin with brand scoping):  
  - POST /api/v1/audits/{audit_id}/workflow/generate (manual trigger; draft audits only; new generation)  
  - GET /api/v1/audits/{audit_id}/workflow (latest)  
- Responses include rule name/code as sources; expressions not exposed to brand users.

**Quickstart (quickstart.md)**  
- Setup: apply migrations; run server.  
- Admin flow: create rule + claims, validate via preview, publish.  
- Brand flow: create audit, trigger workflow, view required evidence with rule names/codes.

**Agent Context Update**  
- Run `.specify/scripts/bash/update-agent-context.sh cursor-agent` after design artifacts are added to keep agent context in sync.

## Phase 2: Implementation Planning (tasks.md via /speckit.tasks)

- Break down into DB migration, domain modules, routers/schemas, evaluator integration, workflow generation logic, contracts/tests, and docs updates.
