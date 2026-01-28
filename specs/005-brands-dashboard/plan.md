# Implementation Plan: Brands Dashboard Endpoint

**Branch**: `005-brands-dashboard` | **Date**: 2026-01-26 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/005-brands-dashboard/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Implement a dashboard endpoint (`/api/v1/brands/dashboard`) in the brands domain that returns aggregated audit data for the authenticated user's brand. The endpoint provides summary metrics (total audits, completed audits count), latest completed audit's category scores breakdown, and a list of recent audits. All data aggregation will be performed using SQL-first approach with PostgreSQL JSON functions for efficient querying.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: FastAPI, SQLAlchemy (async), SQLModel, Pydantic  
**Storage**: PostgreSQL (async SQLAlchemy/SQLModel)  
**Testing**: pytest with httpx.AsyncClient for async integration tests  
**Target Platform**: Linux server (FastAPI application)  
**Project Type**: Web API (FastAPI backend)  
**Performance Goals**: Dashboard endpoint must respond in under 500ms for brands with up to 100 audits  
**Constraints**: <500ms response time (p95), SQL-first aggregation approach, async-only I/O operations  
**Scale/Scope**: Single endpoint, aggregates data from existing audits/audit_workflows tables, supports brands with up to 100 audits

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Domain-Driven Structure**: ✅ This feature belongs to the existing `brands` domain. The dashboard endpoint will be added to `src/brands/router.py` and dashboard-specific service methods will be added to `src/brands/service.py`. No new domain module required.

**Async-First**: ✅ All database queries will use async SQLAlchemy/SQLModel. The endpoint handler will be `async def`. No blocking I/O operations.

**Pydantic Models**: ✅ All request/response models will be defined in `src/brands/schemas.py` using Pydantic. The endpoint will include `response_model`, `status_code`, `description`, `tags`, and `summary` parameters.

**Dependency Injection**: ✅ Database session will be injected via `get_db` dependency. User context will be injected via `get_current_user` dependency. Both are already established patterns in the codebase.

**SQL-First**: ✅ Aggregations (counts, latest audit selection) will be performed in SQL using PostgreSQL functions. JSON building for nested responses will use PostgreSQL JSON functions (`json_build_object`, `json_agg`). Minimal Python-side data transformation.

**Testing**: ✅ Integration tests will use `httpx.AsyncClient` and be organized in `tests/brands/test_dashboard.py` mirroring the source structure.

**Code Quality**: ✅ Code will pass ruff linting. Imports will be at the top of files. Pre-commit hooks are configured in the project.

**Database Conventions**: ✅ No new tables required. Uses existing `audits` and `audit_workflows` tables which follow naming conventions. No migrations needed.

**RESTful Design**: ✅ Endpoint follows REST conventions: `GET /api/v1/brands/dashboard`. Uses appropriate HTTP status codes (200 for success, 404 if brand not found).

**External Services**: ✅ No external service calls required. All data comes from PostgreSQL database.

## Project Structure

### Documentation (this feature)

```text
specs/005-brands-dashboard/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   └── dashboard-api.yaml
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
# FastAPI Backend Structure (Domain-Driven)
src/
├── brands/
│   ├── router.py      # Add GET /api/v1/brands/dashboard endpoint
│   ├── schemas.py     # Add DashboardResponse Pydantic model
│   ├── models.py      # No changes (uses existing Brand model)
│   ├── service.py     # Add get_dashboard_data() method
│   └── ...            # Other existing files unchanged
├── audits/
│   └── models.py      # Uses existing Audit model
├── audit_workflows/
│   └── models.py      # Uses existing AuditWorkflow model
└── main.py            # No changes (brands router already included)

tests/
├── brands/
│   ├── test_router.py      # Add test_dashboard_endpoint()
│   └── test_service.py     # Add test_get_dashboard_data()
└── conftest.py        # Existing fixtures
```

**Structure Decision**: The dashboard endpoint belongs to the `brands` domain since it provides brand-specific aggregated data. It will extend the existing `brands` router and service without requiring a new domain module. This follows the domain-driven structure principle and keeps related functionality together.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations - all constitution requirements are met.
