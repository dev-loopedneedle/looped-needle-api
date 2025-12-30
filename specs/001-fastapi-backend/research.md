# Research: FastAPI Backend Implementation

**Feature**: FastAPI Backend Implementation  
**Date**: 2025-01-27  
**Phase**: 0 - Research & Technology Decisions

## Technology Decisions

### 1. Database ORM: SQLAlchemy Async vs SQLModel

**Decision**: Use SQLAlchemy async with SQLModel for type safety and FastAPI integration

**Rationale**: 
- SQLModel provides Pydantic integration out of the box, reducing duplication between DB models and API schemas
- SQLAlchemy async supports async/await patterns required by constitution
- SQLModel is built on SQLAlchemy, providing full SQLAlchemy capabilities
- FastAPI full-stack template uses SQLModel, maintaining consistency

**Alternatives Considered**:
- Pure SQLAlchemy async: More verbose, requires separate Pydantic models
- Tortoise ORM: Less mature ecosystem, not used in FastAPI template
- Databases library: Lower-level, more manual work required

### 2. Database Driver: asyncpg vs psycopg2

**Decision**: Use asyncpg for PostgreSQL async operations

**Rationale**:
- asyncpg is the recommended async driver for PostgreSQL with SQLAlchemy async
- Better performance for async operations compared to psycopg2
- Native async/await support without thread pool overhead
- Used in FastAPI full-stack template

**Alternatives Considered**:
- psycopg2: Synchronous driver, would require thread pool wrapper
- psycopg3: Newer but less mature, asyncpg is more established

### 3. OpenAI Client: Official SDK vs httpx

**Decision**: Use official OpenAI Python SDK with async support

**Rationale**:
- Official SDK provides async client (`AsyncOpenAI`)
- Better error handling and retry logic built-in
- Type hints and validation included
- Easier to maintain as API evolves
- Can be wrapped in service layer for abstraction

**Alternatives Considered**:
- Direct httpx calls: More manual work, need to implement retries/error handling
- Custom wrapper: Unnecessary complexity when official SDK exists

### 4. Configuration Management: Pydantic BaseSettings vs python-dotenv

**Decision**: Use Pydantic BaseSettings with python-dotenv for .env file loading

**Rationale**:
- Pydantic BaseSettings provides validation and type safety
- Automatic environment variable parsing
- Supports .env files via python-dotenv
- Consistent with Pydantic usage throughout project
- Required by constitution

**Alternatives Considered**:
- python-dotenv only: No validation, manual parsing required
- dynaconf: Additional dependency, Pydantic BaseSettings sufficient

### 5. Testing Framework: pytest-asyncio vs pytest

**Decision**: Use pytest with pytest-asyncio plugin

**Rationale**:
- pytest is standard for Python projects
- pytest-asyncio enables async test functions
- httpx.AsyncClient integrates well with pytest
- FastAPI testing documentation uses pytest
- Required by constitution for async test clients

**Alternatives Considered**:
- unittest with asyncio: Less feature-rich than pytest
- nose2: Less popular, smaller ecosystem

### 6. Migration Tool: Alembic Configuration

**Decision**: Use Alembic with custom naming conventions and date-based migration files

**Rationale**:
- Alembic is standard for SQLAlchemy migrations
- Supports async SQLAlchemy
- Can configure naming conventions per constitution
- Date-based file naming: `YYYY-MM-DD_descriptive_slug.py`
- Required by constitution for static, revertable migrations

**Alternatives Considered**:
- Django-style migrations: Not compatible with SQLAlchemy
- Manual SQL scripts: No versioning, harder to revert

### 7. Project Structure: Domain-Driven vs File-Type

**Decision**: Domain-driven structure per constitution

**Rationale**:
- Scales better for monoliths with multiple domains
- Keeps related code together (router, schemas, models, service)
- Easier navigation and maintenance
- Required by constitution (NON-NEGOTIABLE)

**Structure**:
```
src/
├── audits/          # First domain
│   ├── router.py
│   ├── schemas.py
│   ├── models.py
│   ├── dependencies.py
│   ├── service.py
│   ├── exceptions.py
│   └── constants.py
├── openai/          # External service abstraction
│   ├── client.py
│   ├── schemas.py
│   ├── config.py
│   └── exceptions.py
├── config.py        # Global config
├── database.py      # DB connection
├── exceptions.py    # Global exceptions
└── main.py          # FastAPI app
```

**Alternatives Considered**:
- File-type organization (all routers together): Rejected per constitution

### 8. FastAPI Template Structure

**Decision**: Base structure on FastAPI full-stack template, adapted to domain-driven architecture

**Rationale**:
- Template provides proven patterns
- Includes Docker, CI/CD, and best practices
- Can adapt file-type structure to domain-driven structure
- Maintains compatibility with template's tooling

**Key Adaptations**:
- Reorganize from file-type to domain-driven structure
- Keep global infrastructure at root level
- Maintain template's dependency management and tooling

### 9. Error Handling: Custom Exceptions vs Standard

**Decision**: Use custom exceptions per domain with global exception handlers

**Rationale**:
- Domain-specific exceptions provide better error context
- Global handlers ensure consistent error response format
- FastAPI exception handlers enable clean error responses
- Per constitution: error handling must be domain-specific

**Structure**:
- Global exceptions in `src/exceptions.py`
- Domain exceptions in `src/[domain]/exceptions.py`
- FastAPI exception handlers in `main.py`

### 10. Logging: Structured Logging

**Decision**: Use Python's logging module with structured format

**Rationale**:
- Standard library, no additional dependencies
- Can be enhanced with structlog later if needed
- JSON formatting for production log aggregation
- Per constitution: structured logging required

**Alternatives Considered**:
- structlog: Additional dependency, can add later if needed
- loguru: Non-standard, harder to integrate with existing tools

## Integration Patterns

### Database Connection Pattern

**Pattern**: Async database session via dependency injection

```python
# src/database.py
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
```

**Rationale**: Per constitution, database sessions must be injected via dependencies. Async pattern required.

### OpenAI Service Pattern

**Pattern**: Service layer abstraction with dependency injection

```python
# src/openai/service.py
from openai import AsyncOpenAI
from fastapi import Depends

async def get_openai_client() -> AsyncOpenAI:
    return AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

async def call_openai(prompt: str, client: AsyncOpenAI = Depends(get_openai_client)):
    # Service logic
    pass
```

**Rationale**: Per constitution, external API calls must be abstracted in service layers and injected via dependencies.

### Domain Structure Pattern

**Pattern**: Self-contained domain modules

Each domain (`audits`, etc.) contains:
- `router.py`: FastAPI routes
- `schemas.py`: Pydantic models for API
- `models.py`: SQLModel/SQLAlchemy DB models
- `service.py`: Business logic
- `dependencies.py`: Domain-specific dependencies
- `exceptions.py`: Domain-specific exceptions
- `constants.py`: Domain constants

**Rationale**: Per constitution, domain-driven structure keeps related code together and scales better.

## Clarifications Applied (2025-01-27)

1. **Authentication**: No authentication required - all endpoints are publicly accessible
2. **Rate Limiting**: No rate limiting - all requests processed without throttling
3. **Logging**: Structured JSON logging with INFO level (request/response/errors)
4. **CORS**: Allow all origins - permissive CORS for development
5. **Pagination**: Default 20 items per page, maximum 50 items per page

## Best Practices Adopted

1. **Async-First**: All I/O operations use async/await
2. **Pydantic Everywhere**: Request/response validation, configuration
3. **Dependency Injection**: Shared resources injected via FastAPI dependencies
4. **SQL-First**: Complex queries done in SQL, not Python
5. **Type Hints**: Full type annotations for better IDE support
6. **Error Handling**: Custom exceptions with consistent error responses
7. **Testing**: Async test clients from day 0
8. **Code Quality**: Ruff for linting and formatting
9. **No Authentication**: Public API endpoints (authentication deferred to future feature)
10. **Structured Logging**: JSON format at INFO level for log aggregation
11. **Permissive CORS**: Allow all origins for development flexibility

## References

- [FastAPI Full-Stack Template](https://github.com/fastapi/full-stack-fastapi-template)
- [FastAPI Best Practices](https://github.com/zhanymkanov/fastapi-best-practices)
- [SQLModel Documentation](https://sqlmodel.tiangolo.com/)
- [SQLAlchemy Async Documentation](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [OpenAI Python SDK](https://github.com/openai/openai-python)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)

