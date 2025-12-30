# Implementation Plan: FastAPI Backend Implementation

**Branch**: `001-fastapi-backend` | **Date**: 2025-01-27 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-fastapi-backend/spec.md`

**Note**: This plan has been updated after clarifications session. See clarifications in spec.md.

## Summary

Implement a FastAPI backend API for the Looped Needle project, based on the FastAPI full-stack template structure, following FastAPI best practices. The backend will connect to PostgreSQL for data persistence, integrate with OpenAI API for AI capabilities, and implement the audits domain as the first business domain. The implementation will follow domain-driven architecture, async-first patterns, and comprehensive testing standards.

**Key Clarifications Applied**:
- No authentication required (public API endpoints)
- No rate limiting in initial implementation
- Structured JSON logging at INFO level
- Permissive CORS (allow all origins) for development
- Pagination: default 20, maximum 50 items per page

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: FastAPI, SQLAlchemy (async), SQLModel, PostgreSQL (asyncpg), Alembic, Pydantic, OpenAI Python SDK, httpx, pytest, pytest-asyncio, ruff  
**Storage**: PostgreSQL database with async SQLAlchemy/SQLModel ORM  
**Testing**: pytest with httpx.AsyncClient for async integration tests, pytest-asyncio for async test support  
**Target Platform**: Linux server (containerized/virtualized environment)  
**Project Type**: web (backend API)  
**Performance Goals**: 
- Health check responses < 100ms (99th percentile)
- Audit record creation < 500ms (95th percentile)
- Audit queries < 200ms for datasets up to 10,000 records (95th percentile)
- Support 100 concurrent requests without degradation
- OpenAI API calls < 5 seconds (90th percentile when service available)

**Constraints**: 
- All I/O operations must be async
- Database migrations must be static and revertable
- API credentials must be in environment variables
- Code must pass ruff linting
- All endpoints must have complete OpenAPI documentation
- No authentication required (public endpoints)
- No rate limiting in initial implementation
- Structured JSON logging at INFO level
- CORS configured to allow all origins

**Scale/Scope**: 
- Initial implementation: audits domain with CRUD operations
- Database: PostgreSQL with connection pooling
- External integrations: OpenAI API
- Pagination: default 20, max 50 items per page
- Future: Additional domains following same structure

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Domain-Driven Structure**: ✅ **PASS** - This feature establishes the foundation and implements the audits domain. The audits domain will follow the structure: `src/audits/router.py`, `schemas.py`, `models.py`, `dependencies.py`, `service.py`, etc. Global infrastructure files will be at `src/` root level.

**Async-First**: ✅ **PASS** - All database operations will use async SQLAlchemy/SQLModel. OpenAI API calls will use async HTTP client. All route handlers will be `async def`. CPU-intensive work will use thread pools if needed.

**Pydantic Models**: ✅ **PASS** - All API endpoints will define `response_model` with Pydantic schemas. Request bodies will use Pydantic models. All endpoints will include `status_code`, `description`, `tags`, and `summary` for OpenAPI documentation.

**Dependency Injection**: ✅ **PASS** - Database sessions will be injected via FastAPI dependencies. OpenAI client will be injected via dependencies. Dependencies will be chained and reused across endpoints.

**SQL-First**: ✅ **PASS** - Complex queries, joins, and aggregations will be done in SQL. PostgreSQL JSON functions will be used for nested responses. Python-side data manipulation will be minimized.

**Testing**: ✅ **PASS** - Integration tests will use `httpx.AsyncClient`. Test structure will mirror source structure (`tests/audits/`). Contract tests will verify API schemas.

**Code Quality**: ✅ **PASS** - Code will pass ruff linting. Pre-commit hooks will be configured to run ruff automatically.

**Database Conventions**: ✅ **PASS** - Tables will use `lower_case_snake`, singular form (e.g., `audit`). Columns will use `lower_case_snake` with `_at` suffix for datetime. Migrations will be static, revertable, and use descriptive slugs.

**RESTful Design**: ✅ **PASS** - Endpoints will follow REST conventions with appropriate HTTP methods (GET, POST, PUT, DELETE). Proper status codes will be used (200, 201, 400, 404, 500).

**External Services**: ✅ **PASS** - OpenAI API calls will be abstracted in service layer (`src/openai/service.py`). API keys will be stored in environment variables. Service clients will be injected via dependencies.

**All gates pass** - Proceeding to Phase 0 research.

## Project Structure

### Documentation (this feature)

```text
specs/001-fastapi-backend/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   ├── audits-api.yaml
│   └── health-api.yaml
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
# FastAPI Backend Structure (Domain-Driven)
src/
├── audits/              # Audits domain
│   ├── router.py       # FastAPI routes
│   ├── schemas.py      # Pydantic models
│   ├── models.py       # SQLModel DB models
│   ├── dependencies.py
│   ├── service.py
│   ├── exceptions.py
│   └── constants.py
├── openai/              # OpenAI service abstraction
│   ├── client.py
│   ├── schemas.py
│   ├── config.py
│   └── exceptions.py
├── config.py            # Global configs (Pydantic BaseSettings)
├── database.py          # DB connection (async SQLAlchemy)
├── exceptions.py        # Global exceptions
└── main.py              # FastAPI app

tests/
├── audits/              # Tests mirror source structure
│   ├── test_router.py
│   ├── test_service.py
│   └── test_integration.py
├── contract/            # API contract tests
└── conftest.py          # pytest fixtures (async)
```

**Structure Decision**: Domain-driven structure selected per constitution. The audits domain will be the first domain module, demonstrating the pattern for future domains. Global infrastructure (database, config, exceptions) will be at `src/` root. Tests will mirror the source structure with domain-specific test directories.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations - all constitution principles are followed.

## Phase 0: Research Complete

**Output**: `research.md`

Technology decisions documented:
- SQLAlchemy async with SQLModel for ORM
- asyncpg for PostgreSQL async driver
- Official OpenAI Python SDK with async support
- Pydantic BaseSettings for configuration
- pytest with pytest-asyncio for testing
- Alembic for migrations with custom naming conventions
- Domain-driven project structure

**Clarifications Applied**:
- No authentication/authorization in initial implementation
- No rate limiting/throttling in initial implementation
- Structured JSON logging at INFO level
- Permissive CORS configuration (allow all origins)

## Phase 1: Design Complete

**Outputs**: 
- `data-model.md` - Audit Record entity definition
- `contracts/audits-api.yaml` - Audits API OpenAPI contract (updated with pagination limits: default 20, max 50)
- `contracts/health-api.yaml` - Health check API contract
- `quickstart.md` - Setup and development guide

**Design Decisions**:
- Audit Record entity with UUID primary key, JSONB details field
- RESTful API endpoints following OpenAPI 3.1.0 specification
- Pagination support: default 20 items, maximum 50 items per page
- Comprehensive error response schemas
- Health check endpoints for monitoring
- No authentication middleware required
- CORS middleware configured to allow all origins
- Structured JSON logging configuration

## Next Steps

Ready for `/speckit.tasks` to generate implementation tasks.
