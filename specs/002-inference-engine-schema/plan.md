# Implementation Plan: Dynamic Audit Inference Engine

**Branch**: `002-inference-engine-schema` | **Date**: 2025-01-27 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-inference-engine-schema/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

This feature implements the database schema and core types for a dynamic audit inference engine. The system allows brands to define their profiles (context), system administrators to define sustainability criteria and JEXL-based rules, and automatically generates customized audit checklists based on brand context and scoping questionnaire responses. The core value is automating requirement identification through rule-based inference, eliminating manual selection of audit requirements.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: FastAPI, SQLAlchemy 2.0 (async), SQLModel, asyncpg, Alembic, Pydantic 2.5+, JEXL (python-jexl)  
**Storage**: PostgreSQL with UUID, JSONB, and array data types  
**Testing**: pytest, pytest-asyncio, httpx.AsyncClient  
**Target Platform**: Linux server (FastAPI/ASGI)  
**Project Type**: Web API backend  
**Performance Goals**: 
- Brand profile creation: <500ms p95
- Audit item generation: <5s p95 for up to 1000 rules
- Support 50 concurrent audit generation requests
- Query audit items: <500ms p95 for up to 200 items
**Constraints**: 
- All I/O operations must be async
- Database operations must use SQLAlchemy async sessions
- State transitions must be validated (forward-only)
- Soft delete with referential integrity checks
**Scale/Scope**: 
- Up to 1000 rules per audit generation
- Up to 200 audit items per audit instance
- Support multiple brands, products, supply chain nodes
- JSONB storage for complex nested data (materials composition, questionnaire schemas, brand snapshots)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Domain-Driven Structure**: ✅ This feature creates a new domain module `src/inference/` following the existing pattern from `src/audits/`. Structure: `router.py`, `schemas.py`, `models.py`, `dependencies.py`, `service.py`, `constants.py`, `exceptions.py`.

**Async-First**: ✅ All database operations use async SQLAlchemy sessions. Rule evaluation (JEXL) is CPU-bound but lightweight; will run synchronously in async context. File uploads for evidence will use async file operations.

**Pydantic Models**: ✅ All API request/response models will use Pydantic v2. All endpoints will specify `response_model`, `status_code`, `description`, `tags`, and `summary`.

**Dependency Injection**: ✅ Database sessions injected via FastAPI dependencies (`get_db`). Shared services (rule evaluator, file storage) will be injected via dependencies.

**SQL-First**: ✅ Complex queries (audit item generation, rule evaluation filtering) will use SQL WHERE clauses and JOINs. JSONB queries for questionnaire responses and brand snapshots will use PostgreSQL JSONB operators. Aggregations (rule matching counts) will be done in SQL.

**Testing**: ✅ Integration tests will use `httpx.AsyncClient`. Test structure mirrors source: `tests/inference/test_router.py`, `test_service.py`, `test_integration.py`.

**Code Quality**: ✅ Code will pass ruff linting. Pre-commit hooks configured (if available).

**Database Conventions**: ✅ Tables use `lower_case_snake` naming, singular table names. Timestamps use `_at` suffix (`created_at`, `updated_at`, `uploaded_at`). Migrations are static and revertable via Alembic.

**RESTful Design**: ✅ Endpoints follow REST conventions:
- `GET /api/v1/brands` - list brands
- `POST /api/v1/brands` - create brand
- `GET /api/v1/brands/{id}` - get brand
- `PUT /api/v1/brands/{id}` - update brand
- `DELETE /api/v1/brands/{id}` - soft delete brand
- Similar patterns for products, criteria, rules, audit instances, audit items
- `POST /api/v1/audit-instances/{id}/generate-items` - trigger audit item generation

**External Services**: ✅ JEXL evaluation library abstracted in service layer. File storage abstracted (local filesystem or S3-compatible). No external API calls required for core functionality.

## Project Structure

### Documentation (this feature)

```text
specs/002-inference-engine-schema/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   ├── brands-api.yaml
│   ├── products-api.yaml
│   ├── criteria-api.yaml
│   ├── rules-api.yaml
│   ├── questionnaires-api.yaml
│   ├── audit-instances-api.yaml
│   └── audit-items-api.yaml
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
# FastAPI Backend Structure (Domain-Driven)
src/
├── inference/           # New domain module
│   ├── __init__.py
│   ├── router.py       # FastAPI routes for inference engine
│   ├── schemas.py       # Pydantic models for API
│   ├── models.py        # SQLModel DB models
│   ├── dependencies.py  # Domain-specific dependencies
│   ├── constants.py     # Status enums, constants
│   ├── exceptions.py    # Domain-specific exceptions
│   ├── service.py       # Business logic (rule evaluation, audit generation)
│   └── utils.py         # Helper functions
├── audits/             # Existing domain (unchanged)
├── config.py           # Global configs
├── database.py         # DB connection (existing)
└── main.py             # App entry point (add inference router)

alembic/
├── versions/
│   └── [timestamp]_create_inference_schema.py  # New migration
└── env.py

tests/
├── inference/          # Tests mirror source structure
│   ├── test_router.py
│   ├── test_service.py
│   ├── test_models.py
│   └── test_integration.py
└── conftest.py         # pytest fixtures
```

**Structure Decision**: Following the existing domain-driven structure pattern from `src/audits/`. The inference engine is a new domain module that will integrate with the existing FastAPI application. All database models use SQLModel (which extends SQLAlchemy) for async support.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | No violations | All requirements align with existing patterns |
