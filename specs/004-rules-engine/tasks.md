# Tasks: Rules Engine for Audit Certification

**Input**: Design documents from `/specs/004-rules-engine/`  
**Prerequisites**: plan.md (done), spec.md (clarified), research.md, data-model.md, quickstart.md

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare project structure for new domains.

- [X] T001 [P] Create `src/rules/__init__.py` and scaffold domain directories (`router.py`, `schemas.py`, `models.py`, `service.py`, `constants.py`, `dependencies.py`, `exceptions.py`, `utils.py`)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core schema and migration work required by all user stories. No story work until complete.**

- [X] T002 Define rule/evidence enums and shared constants in `src/rules/constants.py`
- [X] T003 Implement SQLModel tables `Rule`, `EvidenceClaim`, `RuleEvidenceClaim` in `src/rules/models.py` (with global unique code, states, weight constraint)
- [X] T004 Extend `src/audit_workflows/models.py` with workflow generations, snapshots, matches, required_claims, and claim_sources tables
- [X] T005 Create Alembic migration adding rules/evidence tables and workflow extensions in `alembic/versions/2026-01-06_rules_engine.py`
- [X] T006 Update `alembic/env.py` model imports to include `src.rules.models` and new audit_workflow models

**Checkpoint**: Foundation ready—user stories can start.

---

## Phase 3: User Story 1 - Admin Creates and Publishes Rules (Priority: P1) 🎯 MVP

**Goal**: Admin authors/manages rules (draft/published/disabled), validates expressions, clones/publishes/disabled; rules carry evidence claims.
**Independent Test**: Admin creates draft rule with claims, validates expression via preview, publishes; rule appears in list and is immutable once published.

### Implementation

- [X] T007 [P] [US1] Add Pydantic schemas for rules (create/update/response) and include evidence claims in `src/rules/schemas.py`
- [X] T008 [P] [US1] Implement rule services (CRUD, clone, publish, disable, attach claims, enforce global code uniqueness) in `src/rules/service.py`
- [X] T009 [P] [US1] Implement expression validation/preview helper (syntax + type + sample eval) in `src/rules/utils.py`
- [X] T010 [US1] Implement admin rule router (create/list/get/update/clone/publish/disable/preview) in `src/rules/router.py` with admin auth dependency
- [X] T011 [US1] Include rules router in `src/main.py` with appropriate tags/summary/response_model metadata
- [X] T012 [US1] Add contract stub for admin rules endpoints in `specs/004-rules-engine/contracts/rules-api.yaml`

**Checkpoint**: US1 independently testable (admin can create/validate/publish rules).

---

## Phase 4: User Story 2 - System Generates Evidence Requirements for Audits (Priority: P1)

**Goal**: Generate per-audit workflows on manual trigger (draft audits only), match published rules, produce required evidence claims with rule name/code traceability, preserve generations/snapshots.
**Independent Test**: Draft audit triggers workflow generation; required claims reflect matches; regeneration creates new generation; published audits reject regeneration.

### Implementation

- [X] T013 [P] [US2] Add workflow response/request schemas (required claims with rule name/code sources, generation metadata) in `src/audit_workflows/schemas.py`
- [X] T014 [US2] Implement workflow generation logic in `src/audit_workflows/service.py` (manual trigger, draft-only, new generation, evaluate published rules, record matches/required claims/sources, handle errors gracefully)
- [X] T015 [US2] Implement workflow router endpoints POST `/api/v1/audits/{audit_id}/workflow/generate` and GET `/api/v1/audits/{audit_id}/workflow` in `src/audit_workflows/router.py` with brand/admin scoping and published-audit guard
- [X] T016 [US2] Add contract stub for workflow endpoints in `specs/004-rules-engine/contracts/workflow-api.yaml`

**Checkpoint**: US2 independently testable (manual generation, generations preserved, published audits immutable).

---

## Phase 5: User Story 3 - Admin Manages Evidence Claim Catalog (Priority: P2)

**Goal**: Admin creates/manages reusable evidence claims; dropdowns for categories/types.
**Independent Test**: Admin creates evidence claim and sees it available to attach to rules; can fetch category/type options.

### Implementation

- [X] T017 [P] [US3] Implement evidence claim schemas (create/response) in `src/rules/schemas.py` if not already covered
- [X] T018 [P] [US3] Implement evidence claim services (create/list, weight validation) in `src/rules/service.py`
- [X] T019 [US3] Implement admin endpoints for evidence claims and dropdown endpoints for categories/types in `src/rules/router.py`
- [X] T020 [US3] Add contract stub for evidence claim endpoints in `specs/004-rules-engine/contracts/evidence-claims-api.yaml`

**Checkpoint**: US3 independently testable (catalog management and dropdown options).

---

## Phase 6: Polish & Cross-Cutting

- [ ] T021 [P] Update `specs/004-rules-engine/quickstart.md` with final endpoint shapes and flows
- [ ] T022 [P] Add/refresh contract tests or examples in `tests/contract/` for rules/workflow endpoints (if desired)
- [X] T023 Run ruff lint/format across modified files

---

## Dependencies & Execution Order

- Phase 1 → Phase 2 → User Stories (3/4/5) → Phase 6.
- US1 and US2 are both P1; after foundation they can proceed in parallel, but US2 depends on published rules existing—implement US1 first for smooth end-to-end.
- US3 (P2) can proceed after foundation; partially depends on evidence claim schemas (shared with US1).

### User Story Dependencies
- US1: Depends on Phase 2.
- US2: Depends on Phase 2; assumes rules/evidence schema from US1 available.
- US3: Depends on Phase 2; can run parallel with US1/US2 after schemas exist.

### Parallel Opportunities
- Tasks marked [P] can be parallelized (distinct files).
- After foundation, US1 and US3 can run in parallel; US2 should start after US1 rules endpoints/services are in place for meaningful E2E tests.

---

## Implementation Strategy

### MVP First
1. Complete Phase 1–2.
2. Deliver US1 (rules authoring/publish).
3. Deliver US2 (workflow generation).

### Incremental Delivery
- Deploy after US1 (admin rules), then after US2 (workflows), then US3 (catalog).

### Team Parallelization
- Dev A: US1
- Dev B: US2 (after US1 stubs exist)
- Dev C: US3

