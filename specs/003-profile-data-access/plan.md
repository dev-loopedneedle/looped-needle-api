# Implementation Plan: Per-Profile Data Access with Clerk Authentication

**Branch**: `003-profile-data-access` | **Date**: 2026-01-02 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-profile-data-access/spec.md`

## Summary

This feature implements per-profile data access control using Clerk authentication. Users authenticate via Clerk tokens, and the system automatically creates user profiles on first authenticated request. Each user can own exactly one brand, and all brand-related data (products, supply chain nodes, audit instances, audit items) is isolated per user. The core value is ensuring data privacy and security by enforcing strict ownership-based access control across all resources.

This feature also requires a clear role-based exception for audits: users with role `"admin"` can access audit instances (and their items) across all brands, while non-admin users remain restricted to audits for their owned brand.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: FastAPI, SQLAlchemy 2.0 (async), SQLModel, asyncpg, Alembic, Pydantic 2.5+, Clerk Python SDK  
**Storage**: PostgreSQL with UUID, JSONB, and array data types  
**Testing**: pytest, pytest-asyncio, httpx.AsyncClient  
**Target Platform**: Linux server (FastAPI/ASGI)  
**Project Type**: Web API backend  
**Performance Goals**: 
- Authentication requests: <200ms p95
- User profile creation: <500ms p95
- Data access requests filtered by user: <300ms p95
- Access denied errors: <100ms p100
- Support 50 concurrent authenticated requests per user
**Constraints**: 
- All I/O operations must be async
- Database operations must use SQLAlchemy async sessions
- Clerk token validation on every authenticated request (no caching)
- Reject all authenticated requests when Clerk service unavailable
- Database unique constraint on Clerk user ID for idempotent profile creation
- Audit visibility must enforce role-based rules: admin can view all audits; non-admin can view only audits for their owned brand
**Scale/Scope**: 
- One user profile per Clerk user account
- One brand per user profile
- Support multiple users with isolated data access
- User profiles can be marked inactive when Clerk account deleted

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Domain-Driven Structure**: ✅ This feature extends the existing `src/audit_engine/` domain. New components: `src/auth/` module for authentication middleware and user profile management. Structure: `src/auth/router.py`, `src/auth/schemas.py`, `src/auth/models.py`, `src/auth/dependencies.py`, `src/auth/service.py`, `src/auth/middleware.py`, `src/auth/exceptions.py`.

**Async-First**: ✅ All database operations use async SQLAlchemy sessions. Clerk token validation will use async HTTP client. Authentication middleware will be async-compatible.

**Pydantic Models**: ✅ All API request/response models will use Pydantic v2. All endpoints will specify `response_model`, `status_code`, `description`, `tags`, and `summary`.

**Dependency Injection**: ✅ Database sessions injected via FastAPI dependencies (`get_audit_engine_db`). User context will be injected via authentication dependency. Clerk client will be injected via dependency.

**SQL-First**: ✅ User ownership queries will use SQL WHERE clauses and JOINs. All list endpoints will filter by user_id. Access control checks will use SQL queries to validate ownership.

**Testing**: ✅ Integration tests will use `httpx.AsyncClient` with mock Clerk tokens. Test structure mirrors source: `tests/auth/test_router.py`, `test_service.py`, `test_middleware.py`, `test_integration.py`.

**Code Quality**: ✅ Code will pass ruff linting. Pre-commit hooks configured (if available).

**Database Conventions**: ✅ Tables use `lower_case_snake` naming, singular table names. Timestamps use `_at` suffix (`created_at`, `updated_at`, `last_access_at`). Migrations are static and revertable via Alembic.

**RESTful Design**: ✅ Endpoints follow REST conventions. Authentication middleware will protect all endpoints except public ones (health checks, documentation). User context will be available in all authenticated endpoints.

**External Services**: ✅ Clerk authentication service abstracted in service layer. Token validation will use Clerk SDK or direct API calls. Error handling for Clerk service unavailability implemented.

## Project Structure

### Documentation (this feature)

```text
specs/003-profile-data-access/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   ├── auth-api.yaml
│   └── user-profiles-api.yaml
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
# FastAPI Backend Structure (Domain-Driven)
src/
├── auth/                 # New authentication domain module
│   ├── __init__.py
│   ├── router.py         # FastAPI routes for user profiles (if needed)
│   ├── schemas.py        # Pydantic models for user profiles
│   ├── models.py         # SQLModel DB models (UserProfile)
│   ├── dependencies.py   # Authentication dependencies (get_current_user)
│   ├── service.py        # User profile service, Clerk integration
│   ├── middleware.py     # Authentication middleware (optional)
│   ├── exceptions.py     # Auth-specific exceptions
│   └── clerk_client.py   # Clerk SDK wrapper
├── audit_engine/         # Existing domain (modified)
│   ├── models.py         # Add user_id foreign key to Brand
│   ├── brands/
│   │   ├── router.py     # Add user context filtering
│   │   └── service.py    # Add ownership validation
│   ├── audit_runs/
│   │   ├── router.py     # Add user context filtering
│   │   └── service.py     # Add ownership validation
│   └── ...
└── main.py               # Register auth middleware/dependencies
```

## Phase 0: Research

See [research.md](./research.md) for detailed research findings.

**Key Research Areas**:
1. Clerk Python SDK integration patterns
2. FastAPI authentication middleware/dependency patterns
3. Database schema design for user profiles and brand ownership
4. Token validation strategies (JWT verification vs API calls)
5. Idempotent profile creation patterns
6. Clerk public_metadata extraction from JWT token for role-based access control

## Phase 1: Design & Contracts

### Data Model

See [data-model.md](./data-model.md) for complete entity definitions.

**Key Entities**:
- **UserProfile**: Clerk user ID (unique), active status, timestamps
- **Brand**: Add `user_id` foreign key (one-to-one relationship)

### API Contracts

See [contracts/](./contracts/) for OpenAPI specifications.

**Key Endpoints**:
- Authentication middleware protects all endpoints except public ones
- All authenticated endpoints receive user context (including role from public_metadata)
- User profile creation is automatic (no explicit endpoint needed)
- All list endpoints filter by authenticated user
- All resource access validates ownership
- Admin-only endpoints protected by role-based dependency (requires role "admin" in public_metadata)
- Audit instance/item endpoints enforce role-based visibility: admins can list/retrieve across all brands; non-admins are restricted to their owned brand's audits

### Quickstart

See [quickstart.md](./quickstart.md) for setup and usage instructions.

## Phase 2: Implementation Tasks

*Tasks will be generated by `/speckit.tasks` command.*

## Notes

- User profile creation is automatic on first authenticated request
- Clerk token validation happens on every request (no caching)
- Database unique constraint on Clerk user ID ensures idempotent profile creation
- Orphaned brands (created before auth) remain inaccessible until manually associated
- Soft-deleted brands are excluded from user queries
- Inactive user profiles (Clerk account deleted) cannot authenticate but data is preserved
- User role extracted from Clerk token public_metadata during authentication (no API call needed)
- Admin-only endpoints use `get_admin_user` dependency to enforce role-based access control

