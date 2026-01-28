# Tasks: Brands Dashboard Endpoint

**Input**: Design documents from `/specs/005-brands-dashboard/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are included to ensure quality. Integration tests verify the endpoint works correctly.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- Paths shown below assume single project structure

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify existing infrastructure is ready

**Note**: This feature uses existing infrastructure (Brand, Audit, AuditWorkflow models, authentication, database). No new setup required.

- [x] T001 Verify existing Brand model in src/brands/models.py has required fields (id, user_id)
- [x] T002 Verify existing Audit model in src/audits/models.py has required fields (id, brand_id, audit_data, created_at)
- [x] T003 Verify existing AuditWorkflow model in src/audit_workflows/models.py has required fields (id, audit_id, status, category_scores, updated_at)
- [x] T004 Verify authentication dependencies (get_current_user, get_db) are available in src/auth/dependencies.py and src/database.py

**Checkpoint**: Infrastructure verified - ready to proceed

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core components that all user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T005 [P] Create DashboardResponse Pydantic schema in src/brands/schemas.py with summary, latestAuditScores, and recentAudits fields
- [x] T006 [P] Create DashboardSummary Pydantic schema in src/brands/schemas.py with totalAudits and completedAudits fields
- [x] T007 [P] Create LatestAuditScores Pydantic schema in src/brands/schemas.py with auditId, productName, targetMarket, completedAt, and categoryScores fields
- [x] T008 [P] Create RecentAudit Pydantic schema in src/brands/schemas.py with auditId, productName, targetMarket, status, categoryScores, and createdAt fields
- [x] T009 [P] Create CategoryScore Pydantic schema in src/brands/schemas.py with category and score fields

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - View Dashboard Summary (Priority: P1) 🎯 MVP

**Goal**: Return summary metrics (total audits count, completed audits count) for the authenticated user's brand

**Independent Test**: Call GET /api/v1/brands/dashboard endpoint and verify summary object contains accurate totalAudits and completedAudits counts. Works independently even if latestAuditScores and recentAudits are null/empty.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T010 [P] [US1] Create integration test for dashboard summary metrics in tests/brands/test_dashboard.py with test_get_dashboard_summary_metrics()
- [x] T011 [P] [US1] Create test case for brand with no audits in tests/brands/test_dashboard.py with test_dashboard_no_audits()
- [x] T012 [P] [US1] Create test case for brand with multiple audit statuses in tests/brands/test_dashboard.py with test_dashboard_multiple_statuses()

### Implementation for User Story 1

- [x] T013 [US1] Add get_dashboard_summary() helper method in src/brands/service.py that queries total audits and completed audits count using SQL aggregation
- [x] T014 [US1] Implement SQL query in get_dashboard_summary() using COUNT with FILTER for completed audits (status = 'PROCESSING_COMPLETE')
- [x] T015 [US1] Add get_dashboard_data() method stub in src/brands/service.py that calls get_dashboard_summary() and returns summary metrics
- [x] T016 [US1] Add GET /api/v1/brands/dashboard endpoint in src/brands/router.py that calls BrandService.get_dashboard_data()
- [x] T017 [US1] Configure endpoint with response_model=DashboardResponse, summary, description, and tags in src/brands/router.py
- [x] T018 [US1] Add error handling for brand not found case (404) in src/brands/router.py

**Checkpoint**: At this point, User Story 1 should be fully functional - endpoint returns summary metrics correctly

---

## Phase 4: User Story 2 - View Latest Audit Scores Breakdown (Priority: P1)

**Goal**: Return the latest completed audit's detailed category scores (Environmental, Social, Circularity, Transparency) as numeric values

**Independent Test**: Call GET /api/v1/brands/dashboard endpoint and verify latestAuditScores object contains auditId, completedAt, and categoryScores array with all four categories. Works independently even if summary or recentAudits have issues.

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T019 [P] [US2] Create integration test for latest audit scores in tests/brands/test_dashboard.py with test_get_latest_audit_scores()
- [x] T020 [P] [US2] Create test case for brand with no completed audits in tests/brands/test_dashboard.py with test_dashboard_no_completed_audits()
- [x] T021 [P] [US2] Create test case for latest audit selection by completion timestamp in tests/brands/test_dashboard.py with test_latest_audit_by_completion_time()
- [x] T022 [P] [US2] Create test case for partial category scores in tests/brands/test_dashboard.py with test_partial_category_scores()

### Implementation for User Story 2

- [x] T023 [US2] Add get_latest_completed_audit() helper method in src/brands/service.py that queries audit with PROCESSING_COMPLETE status ordered by updated_at DESC
- [x] T024 [US2] Implement SQL query in get_latest_completed_audit() with tiebreaker (updated_at DESC, created_at DESC) and LIMIT 1
- [x] T025 [US2] Add extract_category_scores() helper method in src/brands/service.py that converts category_scores JSONB dict to CategoryScore array
- [x] T026 [US2] Add extract_product_info() helper method in src/brands/service.py that extracts productName and targetMarket from audit_data JSONB
- [x] T027 [US2] Update get_dashboard_data() method in src/brands/service.py to call get_latest_completed_audit() and build LatestAuditScores object
- [x] T028 [US2] Handle null case when no completed audits exist (return None for latestAuditScores) in src/brands/service.py

**Checkpoint**: At this point, User Stories 1 AND 2 should both work - endpoint returns summary and latest audit scores

---

## Phase 5: User Story 3 - View Recent Audits List (Priority: P2)

**Goal**: Return a list of up to 5 most recent audits with product information, status, and category scores (when completed)

**Independent Test**: Call GET /api/v1/brands/dashboard endpoint and verify recentAudits array contains up to 5 audits ordered by createdAt DESC, with status mapping and category scores only for completed audits. Works independently even if summary or latestAuditScores have issues.

### Tests for User Story 3

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T029 [P] [US3] Create integration test for recent audits list in tests/brands/test_dashboard.py with test_get_recent_audits()
- [x] T030 [P] [US3] Create test case for recent audits ordering (newest first) in tests/brands/test_dashboard.py with test_recent_audits_ordering()
- [x] T031 [P] [US3] Create test case for status mapping (PROCESSING_COMPLETE → "Completed") in tests/brands/test_dashboard.py with test_status_mapping()
- [x] T032 [P] [US3] Create test case for category scores only on completed audits in tests/brands/test_dashboard.py with test_category_scores_only_completed()
- [x] T033 [P] [US3] Create test case for limit of 5 recent audits in tests/brands/test_dashboard.py with test_recent_audits_limit()

### Implementation for User Story 3

- [x] T034 [US3] Add get_recent_audits() helper method in src/brands/service.py that queries up to 5 audits ordered by created_at DESC
- [x] T035 [US3] Implement SQL query in get_recent_audits() with LEFT JOIN to audit_workflows and LIMIT 5
- [x] T036 [US3] Add map_workflow_status() helper method in src/brands/service.py that maps workflow status to display status (PROCESSING_COMPLETE → "Completed", etc.)
- [x] T037 [US3] Update get_recent_audits() to include workflow status mapping and category scores extraction in src/brands/service.py
- [x] T038 [US3] Update get_dashboard_data() method in src/brands/service.py to call get_recent_audits() and build RecentAudit array
- [x] T039 [US3] Ensure category scores are only included when status is "Completed" in get_recent_audits() method

**Checkpoint**: At this point, all user stories should work - endpoint returns complete dashboard data

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Integration, error handling, edge cases, and performance optimization

- [x] T040 [P] Add comprehensive error handling for database query failures in src/brands/service.py
- [x] T041 [P] Add logging for dashboard data retrieval operations in src/brands/router.py and src/brands/service.py
- [x] T042 [P] Optimize SQL query performance using CTEs (Common Table Expressions) in src/brands/service.py get_dashboard_data() method
- [x] T043 [P] Add validation for edge cases (null category_scores, missing product info) in src/brands/service.py
- [x] T044 [P] Add integration test for complete dashboard response in tests/brands/test_dashboard.py with test_complete_dashboard_response()
- [x] T045 [P] Add performance test to verify <500ms response time in tests/brands/test_dashboard.py with test_dashboard_performance()
- [x] T046 [P] Verify OpenAPI documentation is generated correctly for dashboard endpoint (check /docs endpoint)
- [x] T047 [P] Run ruff linting and fix any issues in src/brands/router.py and src/brands/service.py
- [x] T048 [P] Update API contract documentation if needed in specs/005-brands-dashboard/contracts/dashboard-api.yaml
- [x] T049 [P] Run quickstart.md validation steps to verify implementation matches guide

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - User stories can proceed sequentially in priority order (P1 → P1 → P2)
  - US1 and US2 are both P1, but US2 depends on US1's endpoint structure
  - US3 depends on US1 and US2's service methods
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1)**: Can start after US1 endpoint structure is in place - Shares same endpoint but adds latestAuditScores
- **User Story 3 (P2)**: Can start after US1 and US2 - Adds recentAudits to same endpoint

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Service methods before router endpoint updates
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Foundational tasks (T005-T009) marked [P] can run in parallel (different schemas)
- All test tasks within a user story marked [P] can run in parallel
- Polish phase tasks marked [P] can run in parallel (different concerns)

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Create integration test for dashboard summary metrics in tests/brands/test_dashboard.py"
Task: "Create test case for brand with no audits in tests/brands/test_dashboard.py"
Task: "Create test case for brand with multiple audit statuses in tests/brands/test_dashboard.py"

# Then implement service method:
Task: "Add get_dashboard_summary() helper method in src/brands/service.py"
```

---

## Parallel Example: Foundational Phase

```bash
# Launch all schema creation tasks together:
Task: "Create DashboardResponse Pydantic schema in src/brands/schemas.py"
Task: "Create DashboardSummary Pydantic schema in src/brands/schemas.py"
Task: "Create LatestAuditScores Pydantic schema in src/brands/schemas.py"
Task: "Create RecentAudit Pydantic schema in src/brands/schemas.py"
Task: "Create CategoryScore Pydantic schema in src/brands/schemas.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (verify infrastructure)
2. Complete Phase 2: Foundational (create schemas)
3. Complete Phase 3: User Story 1 (summary metrics)
4. **STOP and VALIDATE**: Test User Story 1 independently - endpoint returns summary only
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP - summary metrics!)
3. Add User Story 2 → Test independently → Deploy/Demo (adds latest audit scores)
4. Add User Story 3 → Test independently → Deploy/Demo (adds recent audits list)
5. Add Polish → Final validation → Deploy
6. Each story adds value without breaking previous stories

### Sequential Strategy (Recommended)

Since all stories share the same endpoint, sequential implementation is recommended:

1. Team completes Setup + Foundational together
2. Implement User Story 1 → Test → Commit
3. Implement User Story 2 → Test → Commit
4. Implement User Story 3 → Test → Commit
5. Polish phase → Final validation → Deploy

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently testable via the endpoint
- Verify tests fail before implementing
- Commit after each user story completion
- Stop at any checkpoint to validate story independently
- SQL-first approach: Use PostgreSQL JSON functions for aggregation
- All database operations must be async
- Follow existing patterns in src/brands/service.py and src/brands/router.py

---

## Task Summary

**Total Tasks**: 49
- Phase 1 (Setup): 4 tasks
- Phase 2 (Foundational): 5 tasks
- Phase 3 (US1): 9 tasks (3 tests + 6 implementation)
- Phase 4 (US2): 10 tasks (4 tests + 6 implementation)
- Phase 5 (US3): 11 tasks (5 tests + 6 implementation)
- Phase 6 (Polish): 10 tasks

**Task Count per User Story**:
- User Story 1: 9 tasks
- User Story 2: 10 tasks
- User Story 3: 11 tasks

**Parallel Opportunities**: 
- Foundational phase: 5 parallel tasks (all schemas)
- Test tasks within each story: Can run in parallel
- Polish phase: 10 parallel tasks

**Independent Test Criteria**:
- **US1**: Endpoint returns summary metrics (totalAudits, completedAudits) correctly
- **US2**: Endpoint returns latestAuditScores with category breakdown correctly
- **US3**: Endpoint returns recentAudits list with status and scores correctly

**Suggested MVP Scope**: User Story 1 only (summary metrics) - provides immediate value with minimal complexity
