<!--
Sync Impact Report:
Version change: N/A → 1.0.0 (initial constitution)
Modified principles: N/A (new constitution)
Added sections: All sections (initial creation)
Removed sections: N/A
Templates requiring updates:
  ✅ .specify/templates/plan-template.md (updated Constitution Check section)
  ✅ .specify/templates/spec-template.md (aligned with FastAPI structure)
  ✅ .specify/templates/tasks-template.md (aligned with domain-driven structure)
Follow-up TODOs: None
-->

# Looped Needle API Constitution

## Core Principles

### I. Domain-Driven Project Structure (NON-NEGOTIABLE)

The project MUST be organized by domain/module, not by file type. Each domain is a self-contained module with its own router, schemas, models, dependencies, config, constants, exceptions, service, and utils. This structure scales better for monoliths with multiple domains and prevents organizational chaos as the codebase grows.

**Structure Pattern**:
```
src/
├── [domain]/
│   ├── router.py      # FastAPI routes
│   ├── schemas.py     # Pydantic models
│   ├── models.py      # SQLAlchemy/SQLModel DB models
│   ├── dependencies.py
│   ├── config.py      # domain-specific configs
│   ├── constants.py
│   ├── exceptions.py
│   ├── service.py
│   └── utils.py
├── config.py          # global configs
├── models.py          # global models
├── exceptions.py      # global exceptions
├── database.py        # DB connection
└── main.py
```

**Rationale**: File-type organization (e.g., all routers together, all models together) becomes unmaintainable with many domains. Domain-driven structure keeps related code together and makes the codebase navigable.

### II. Async-First Architecture (NON-NEGOTIABLE)

All I/O-bound operations MUST be asynchronous. This includes database queries, external API calls (OpenAI, etc.), file operations, and HTTP requests. CPU-intensive tasks MUST run in thread pools to avoid blocking the event loop.

**Rules**:
- All route handlers MUST be `async def`
- All database operations MUST use async SQLAlchemy/SQLModel
- All external API calls MUST use async HTTP clients
- Dependencies MUST prefer async when possible
- CPU-intensive work MUST use `asyncio.to_thread()` or `run_in_executor()`

**Rationale**: FastAPI's async capabilities provide significant performance improvements for I/O-bound workloads. Blocking operations defeat the purpose of using async frameworks.

### III. Pydantic Models (Excessive Use)

Pydantic models MUST be used extensively for all data validation, serialization, and configuration. Every API request/response, database model, and configuration MUST use Pydantic schemas. A custom base model SHOULD be used for shared fields and behaviors.

**Rules**:
- All API endpoints MUST define `response_model` with Pydantic schemas
- All request bodies MUST use Pydantic models for validation
- Configuration MUST use Pydantic BaseSettings (decoupled from domain logic)
- Custom base model SHOULD extend Pydantic BaseModel for shared fields
- Use `responses` parameter for endpoints with multiple status codes

**Rationale**: Pydantic provides automatic validation, serialization, and OpenAPI documentation. Excessive use ensures type safety and reduces bugs.

### IV. Dependency Injection & Reusability

FastAPI's dependency injection system MUST be used for shared resources, authentication, database sessions, and business logic. Dependencies MUST be chained, cached, and reused across endpoints. Prefer async dependencies.

**Rules**:
- Database sessions MUST be injected via dependencies
- Authentication/authorization MUST use dependencies
- External service clients (OpenAI, etc.) MUST be injected via dependencies
- Dependencies MUST be chained when one depends on another
- Dependency results are cached per request - leverage this for expensive operations
- Prefer async dependencies over sync when possible

**Rationale**: Dependency injection reduces coupling, improves testability, and enables code reuse. FastAPI's caching mechanism prevents redundant work.

### V. SQL-First, Pydantic-Second

Complex data processing, joins, aggregations, and JSON building MUST be done in SQL/PostgreSQL rather than in Python. The database handles data processing faster and cleaner than CPython. Use SQL functions like `json_build_object` for nested responses.

**Rules**:
- Complex joins MUST be done in SQL queries
- Data aggregations MUST use SQL aggregate functions
- Nested JSON responses SHOULD be built using PostgreSQL JSON functions
- Pydantic models are for validation/serialization, not data manipulation
- Minimize Python-side data transformations

**Rationale**: Databases are optimized for data processing. Doing work in SQL reduces application memory usage and improves performance.

### VI. Testing Standards

Integration tests MUST use async test clients from day 0. Tests MUST be organized by domain matching the source structure. Contract tests MUST verify API contracts match specifications.

**Rules**:
- Integration tests MUST use `httpx.AsyncClient` or `async_asgi_testclient.TestClient`
- Test structure MUST mirror source structure (`tests/[domain]/`)
- Contract tests MUST verify request/response schemas
- Tests MUST be independent and runnable in parallel when possible
- Test fixtures MUST use async database sessions

**Rationale**: Sync test clients cause event loop issues with async codebases. Async clients from the start prevent future migration pain.

### VII. Code Quality & Tooling

Ruff MUST be used for linting and formatting. Code MUST pass all linting checks before commit. Pre-commit hooks SHOULD enforce code quality.

**Rules**:
- Ruff MUST be configured for linting (`ruff check`)
- Ruff MUST be used for formatting (`ruff format`)
- Code MUST pass linting before merge
- Pre-commit hooks SHOULD run ruff automatically
- Ruff replaces black, autoflake, isort, and many other tools

**Rationale**: Ruff is fast, comprehensive, and reduces tooling complexity. Consistent formatting improves code readability and reduces merge conflicts.

### VIII. Database Conventions

PostgreSQL naming conventions MUST be consistent and explicit. Database indexes, constraints, and foreign keys MUST follow explicit naming conventions. Migrations MUST be static, revertable, and descriptively named.

**Rules**:
- Table names: `lower_case_snake`, singular form (e.g., `post`, `user_playlist`)
- Column names: `lower_case_snake` (e.g., `profile_id`, `created_at`)
- Use `_at` suffix for datetime columns, `_date` for date columns
- Indexes MUST use explicit naming convention: `%(column_0_label)s_idx`
- Foreign keys MUST use explicit naming: `%(table_name)s_%(column_0_name)s_fkey`
- Migrations MUST use descriptive slugs: `YYYY-MM-DD_descriptive_slug.py`
- Migrations MUST be revertable and static (no dynamic structure changes)

**Rationale**: Consistent naming improves database maintainability. Explicit conventions prevent SQLAlchemy's auto-generated names from causing issues.

### IX. RESTful API Design

APIs MUST follow REST conventions. Endpoints MUST be well-documented with OpenAPI/Swagger. Response models, status codes, descriptions, tags, and summaries MUST be specified.

**Rules**:
- Use standard HTTP methods (GET, POST, PUT, DELETE, PATCH)
- Use proper HTTP status codes (200, 201, 202, 400, 401, 403, 404, 500)
- Endpoints MUST include `response_model`, `status_code`, `description`, `tags`, `summary`
- Multiple response types MUST use `responses` parameter
- API documentation MUST be accurate and complete

**Rationale**: RESTful design improves API usability and maintainability. Complete OpenAPI documentation enables automatic client generation and better developer experience.

### X. External Service Integration

External service clients (OpenAI, etc.) MUST be abstracted behind service layers. API keys and credentials MUST be stored in environment variables. Service clients MUST be injected via dependencies.

**Rules**:
- External API calls MUST be wrapped in service modules
- API keys MUST be in environment variables, never hardcoded
- Service clients MUST be created via dependency injection
- External calls MUST be async
- Error handling MUST be domain-specific (use custom exceptions)
- Rate limiting and retries SHOULD be implemented for external APIs

**Rationale**: Abstraction enables testing, swapping implementations, and centralized error handling. Environment variables prevent credential leaks.

## Technology Stack

**Language**: Python 3.11+  
**Framework**: FastAPI  
**Database**: PostgreSQL (async SQLAlchemy/SQLModel)  
**Migrations**: Alembic  
**Testing**: pytest with async test clients (httpx.AsyncClient)  
**Linting/Formatting**: Ruff  
**External APIs**: OpenAI API (via async client)  
**Documentation**: OpenAPI/Swagger (auto-generated by FastAPI)

## Development Workflow

### Code Review Requirements

- All PRs MUST verify constitution compliance
- Database migrations MUST be reviewed for naming conventions
- Async operations MUST be verified (no blocking calls)
- Pydantic models MUST be used for all API boundaries
- Tests MUST be included for new features

### Quality Gates

- Code MUST pass ruff linting
- All tests MUST pass
- Integration tests MUST use async clients
- API documentation MUST be complete
- Database migrations MUST be revertable

### Environment Configuration

- Configuration MUST use Pydantic BaseSettings
- Environment variables MUST be documented
- `.env` files MUST be in `.gitignore`
- Production secrets MUST use secure secret management

## Governance

This constitution supersedes all other development practices and conventions. All code MUST comply with these principles.

**Amendment Process**:
1. Proposed amendments MUST be documented with rationale
2. Amendments require review and approval
3. Version MUST be incremented per semantic versioning:
   - MAJOR: Backward incompatible principle changes
   - MINOR: New principles or significant expansions
   - PATCH: Clarifications and minor refinements
4. Dependent templates and documentation MUST be updated
5. Sync Impact Report MUST be included in constitution file

**Compliance**:
- All PRs/reviews MUST verify constitution compliance
- Violations MUST be justified or fixed before merge
- Complexity additions MUST be documented in plan.md Complexity Tracking section

**Version**: 1.0.0 | **Ratified**: 2025-01-27 | **Last Amended**: 2025-01-27
