# Implementation Tasks: Per-Profile Data Access with Clerk Authentication

**Feature Branch**: `003-profile-data-access`  
**Date**: 2026-01-02  
**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

## Summary

This document breaks down the implementation into actionable, dependency-ordered tasks organized by user story priority. Each user story phase is independently testable and delivers incremental value.

**Total Tasks**: 52  
**User Stories**: 6 (US1-P1, US2-P1, US3-P2, US4-P2, US5-P2, US6-P2)  
**MVP Scope**: Phase 1-3 (Setup, Foundational, US1) - Authentication and user profile creation

## Dependencies

**Story Completion Order**:
1. **US1** (P1) - User Profile Creation and Authentication → **BLOCKS ALL OTHER STORIES**
2. **US2** (P1) - Brand Profile Access Control → Depends on US1
3. **US3** (P2) - Brand Products and Supply Chain Access → Depends on US2
4. **US4** (P2) - Audit Instance Access Control → Depends on US2
5. **US5** (P2) - Audit Item Access Control → Depends on US4
6. **US6** (P2) - Admin Role-Based Access Control → Depends on US1

**Parallel Opportunities**:
- US3 and US4 can be implemented in parallel (both depend on US2)
- US5 depends on US4, so must be sequential

## Implementation Strategy

**MVP First**: Implement Phase 1-3 (Setup, Foundational, US1) to deliver authentication and user profile creation. This enables all subsequent features.

**Incremental Delivery**: Each user story phase is independently testable and can be deployed separately.

---

## Phase 1: Setup

**Goal**: Initialize project structure and install dependencies for Clerk authentication.

**Independent Test**: Project structure exists, dependencies installed, environment variables configured.

- [x] T001 Add clerk-sdk-python dependency to pyproject.toml
- [x] T002 Create src/auth/ directory structure with __init__.py
- [x] T003 Add CLERK_SECRET_KEY and CLERK_PUBLISHABLE_KEY to src/config.py Settings class
- [x] T004 Update .env.example with Clerk configuration variables

---

## Phase 2: Foundational

**Goal**: Create core authentication infrastructure that blocks all user stories.

**Independent Test**: Clerk client can be instantiated, authentication dependency structure exists, database models defined.

- [x] T005 Create src/auth/exceptions.py with AuthenticationError, ServiceUnavailableError, AccessDeniedError
- [x] T006 Create src/auth/clerk_client.py with ClerkClient wrapper class for token verification
- [x] T007 Create src/auth/models.py with UserProfile SQLModel (id, clerk_user_id unique, is_active, timestamps)
- [x] T008 Create Alembic migration to add user_profiles table with unique constraint on clerk_user_id
- [x] T009 Create Alembic migration to add user_id column to brands table (nullable, unique constraint, foreign key)
- [x] T010 Run migrations: alembic upgrade head

---

## Phase 3: User Story 1 - User Profile Creation and Authentication

**Goal**: Users can authenticate with Clerk tokens and have profiles automatically created.

**Independent Test**: Authenticate with valid token → profile created/retrieved, invalid token → 401 error, Clerk unavailable → 503 error.

- [x] T011 [US1] Create src/auth/schemas.py with UserProfileResponse Pydantic model (include role field from user context, not database)
- [x] T012 [US1] Create src/auth/service.py with UserProfileService class
- [x] T013 [US1] Implement get_or_create_user_profile method in UserProfileService with idempotent creation (handle unique constraint violation)
- [x] T014 [US1] Implement update_last_access method in UserProfileService to update last_access_at timestamp
- [x] T015 [US1] Create src/auth/dependencies.py with get_current_user dependency function
- [x] T016 [US1] Implement token extraction from Authorization Bearer header in get_current_user
- [x] T017 [US1] Implement Clerk token verification in get_current_user using ClerkClient
- [x] T018 [US1] Extract public_metadata from verified token claims in get_current_user
- [x] T019 [US1] Extract role from public_metadata.role in get_current_user and attach to user context object (create UserContext dataclass or extend UserProfile with role attribute)
- [x] T020 [US1] Implement automatic profile creation/retrieval in get_current_user dependency
- [x] T021 [US1] Implement error handling in get_current_user (401 for invalid token, 503 for Clerk unavailable)
- [x] T022 [US1] Create src/auth/router.py with GET /api/v1/me endpoint returning UserProfileResponse (include role from user context in response)
- [x] T023 [US1] Register auth router in src/main.py
- [x] T024 [US1] Update src/main.py to mark /health and /docs as public endpoints (no auth required)

---

## Phase 4: User Story 2 - Brand Profile Access Control

**Goal**: Users can only access brands they own, one brand per user.

**Independent Test**: Create brand → associated with user, list brands → only own brands, access other user's brand → 403 error.

- [x] T025 [US2] Update src/audit_engine/models.py Brand model to add user_id field (UUID, nullable, foreign key)
- [x] T026 [US2] Update src/audit_engine/brands/service.py BrandService.create_brand to associate brand with current_user.id
- [x] T027 [US2] Update src/audit_engine/brands/service.py BrandService.list_brands to filter by user_id and exclude soft-deleted (deleted_at IS NULL)
- [x] T028 [US2] Update src/audit_engine/brands/service.py BrandService.get_brand to validate ownership (check user_id matches current_user.id)
- [x] T029 [US2] Update src/audit_engine/brands/service.py BrandService.update_brand to validate ownership before update
- [x] T030 [US2] Update src/audit_engine/brands/service.py BrandService.delete_brand to validate ownership before soft delete
- [x] T031 [US2] Update src/audit_engine/brands/router.py all endpoints to inject get_current_user dependency
- [x] T032 [US2] Add ownership validation in BrandService methods to raise AccessDeniedError for unauthorized access

---

## Phase 5: User Story 3 - Brand Products and Supply Chain Access

**Goal**: Users can only access products and supply chain nodes belonging to their brands.

**Independent Test**: Create product for own brand → success, list products → only own brand's products, access other user's product → 403 error.

- [x] T033 [US3] Update src/audit_engine/brands/service.py ProductService.get_products_by_brand to validate brand ownership before returning products
- [x] T034 [US3] Update src/audit_engine/brands/service.py ProductService.create_product to validate brand ownership before creation
- [x] T035 [US3] Update src/audit_engine/brands/router.py product endpoints to inject get_current_user dependency
- [x] T036 [US3] Update src/audit_engine/brands/service.py SupplyChainNodeService.get_nodes_by_brand to validate brand ownership
- [x] T037 [US3] Update src/audit_engine/brands/service.py SupplyChainNodeService.create_node to validate brand ownership before creation
- [x] T038 [US3] Update src/audit_engine/brands/router.py supply chain node endpoints to inject get_current_user dependency

---

## Phase 6: User Story 4 - Audit Instance Access Control

**Goal**: Users can only access audit instances for their brands.

**Independent Test**: Create audit instance for own brand → success, list audit instances → only own brand's instances, access other user's instance → 403 error.

- [x] T039 [US4] Update src/audit_engine/audit_runs/service.py AuditInstanceService.create_audit_instance to validate brand ownership
- [x] T040 [US4] Update src/audit_engine/audit_runs/service.py AuditInstanceService.list_audit_instances to enforce role-based visibility (admin: can list across all brands; non-admin: filter to user's owned brand via join on brands.user_id). Ensure any client-supplied brand_id filter cannot expand access for non-admin.
- [x] T041 [US4] Update src/audit_engine/audit_runs/service.py AuditInstanceService.get_audit_instance to enforce role-based visibility (admin: can access any; non-admin: validate ownership via brand.user_id)
- [x] T042 [US4] Update src/audit_engine/audit_runs/service.py AuditInstanceService.update_audit_instance_status to validate ownership before update
- [x] T043 [US4] Update src/audit_engine/audit_runs/router.py audit instance endpoints to inject get_current_user dependency

---

## Phase 7: User Story 5 - Audit Item Access Control

**Goal**: Users can only access audit items belonging to their audit instances.

**Independent Test**: List audit items for own instance → success, access other user's audit item → 403 error, update own audit item → success.

- [x] T044 [US5] Update src/audit_engine/audit_runs/service.py AuditItemService.get_audit_items_by_instance to enforce role-based visibility via audit instance ownership (admin: can access any instance; non-admin: validate through brand ownership)
- [x] T045 [US5] Update src/audit_engine/audit_runs/service.py AuditItemService.get_audit_item to enforce role-based visibility (admin: can access any; non-admin: validate via audit_instance.brand.user_id)
- [x] T046 [US5] Update src/audit_engine/audit_runs/service.py AuditItemService.update_audit_item to validate ownership before update
- [x] T047 [US5] Update src/audit_engine/audit_runs/router.py audit item endpoints to inject get_current_user dependency

---

## Phase 8: User Story 6 - Admin Role-Based Access Control

**Goal**: Admin users (role: "admin" in public_metadata) can access admin-only endpoints while non-admin users receive 403 Forbidden.

**Independent Test**: Admin user accesses admin endpoint → success, non-admin user accesses admin endpoint → 403 Forbidden, user without role accesses admin endpoint → 403 Forbidden.

- [ ] T048 [US6] Create get_admin_user dependency in src/auth/dependencies.py that checks current_user.role == "admin"
- [ ] T049 [US6] Implement 403 Forbidden error in get_admin_user when role is not "admin" or missing
- [ ] T050 [US6] Update src/audit_engine/standards/router.py criteria endpoints to use get_admin_user dependency for create/update operations
- [ ] T051 [US6] Update src/audit_engine/standards/router.py rules endpoints to use get_admin_user dependency for create/update operations

---

## Phase 9: Polish & Cross-Cutting Concerns

**Goal**: Finalize implementation, handle edge cases, ensure consistency.

**Independent Test**: All endpoints properly authenticated, error messages consistent, inactive profiles cannot authenticate.

- [ ] T052 Update src/auth/service.py UserProfileService to check is_active flag and reject authentication for inactive profiles
- [ ] T053 Update src/auth/dependencies.py get_current_user to handle inactive profile case (return 403 Forbidden)
- [ ] T054 Add logging for authentication events (profile creation, access denied, service unavailable) in src/auth/dependencies.py
- [ ] T055 Update all error responses to include consistent error format (error, message, status_code, request_id)
- [ ] T056 Run ruff linting and fix any issues: ruff check src/auth src/audit_engine
- [ ] T057 Update API documentation to reflect authentication requirements on all endpoints

---

## Parallel Execution Examples

### US1 Tasks (Sequential)
- T011 → T012 → T013 → T014 → T015 → T016 → T017 → T018 → T019 → T020 → T021 → T022 → T023 → T024
- Must be sequential due to dependencies (models → service → dependencies → router)
- T018-T019 extract role from token claims (part of authentication flow)

### US2 Tasks (Mostly Sequential)
- T025 → T026 → T027 → T028 → T029 → T030 → T031 → T032
- T026-T030 can be parallelized after T025 (model update)

### US3 Tasks (Can Parallelize)
- T033, T034, T036, T037 can be done in parallel (different services, same pattern)
- T035, T038 must be after their respective service updates

### US4 and US5 Tasks (Sequential)
- US4: T039 → T040 → T041 → T042 → T043
- US5: T044 → T045 → T046 → T047 (depends on US4 completion)

### US6 Tasks (Can be parallel with US2+)
- T048 → T049 → T050 → T051
- Can be implemented after US1 (only depends on role extraction from US1)

---

## Independent Test Criteria

### US1 - User Profile Creation and Authentication
- ✅ Authenticate with valid Clerk token → profile created automatically
- ✅ Authenticate with existing profile → profile retrieved, last_access_at updated
- ✅ Authenticate with invalid token → 401 Unauthorized
- ✅ Authenticate when Clerk unavailable → 503 Service Unavailable
- ✅ GET /api/v1/me returns user profile data

### US2 - Brand Profile Access Control
- ✅ Create brand → associated with authenticated user
- ✅ List brands → only returns user's own brands
- ✅ Get own brand by ID → success
- ✅ Get other user's brand by ID → 403 Forbidden
- ✅ Update own brand → success
- ✅ Update other user's brand → 403 Forbidden
- ✅ Soft-deleted brands excluded from queries

### US3 - Brand Products and Supply Chain Access
- ✅ Create product for own brand → success
- ✅ List products → only own brand's products
- ✅ Access other user's product → 403 Forbidden
- ✅ Create supply chain node for own brand → success
- ✅ List supply chain nodes → only own brand's nodes
- ✅ Access other user's supply chain node → 403 Forbidden

### US4 - Audit Instance Access Control
- ✅ Create audit instance for own brand → success
- ✅ List audit instances → only own brand's instances
- ✅ Get own audit instance → success
- ✅ Get other user's audit instance → 403 Forbidden
- ✅ Update own audit instance → success
- ✅ Generate items for own audit instance → success

### US5 - Audit Item Access Control
- ✅ List audit items for own instance → success
- ✅ Get own audit item → success
- ✅ Get other user's audit item → 403 Forbidden
- ✅ Update own audit item → success
- ✅ Update other user's audit item → 403 Forbidden

### US6 - Admin Role-Based Access Control
- ✅ Admin user (role: "admin") accesses admin endpoint → success
- ✅ Non-admin user accesses admin endpoint → 403 Forbidden
- ✅ User without role accesses admin endpoint → 403 Forbidden
- ✅ GET /api/v1/me returns user role in response
- ✅ Role extracted from Clerk token public_metadata during authentication

---

## Notes

- All tasks include file paths for clarity
- Tasks are ordered by dependencies within each phase
- [P] marker indicates parallelizable tasks (not used in this feature due to tight dependencies)
- [US1-6] labels map tasks to user stories for tracking
- MVP scope: Complete through Phase 3 (US1) for basic authentication
- Orphaned brands (user_id = NULL) remain inaccessible until manually associated (out of scope for these tasks)

