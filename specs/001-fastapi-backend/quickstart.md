# Quick Start Guide: FastAPI Backend Implementation

**Feature**: FastAPI Backend Implementation  
**Date**: 2025-01-27

## Prerequisites

- Python 3.11 or higher
- PostgreSQL 12 or higher
- Git
- OpenAI API key (optional, for OpenAI integration)

## Setup Steps

### 1. Clone and Initialize Project

```bash
# Clone the repository (or create new project)
git clone <repository-url>
cd looped-needle-api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"
```

### 2. Configure Environment Variables

Create a `.env` file in the project root:

```env
# Database Configuration
POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_DB=looped_needle
DATABASE_URL=postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_SERVER}/${POSTGRES_DB}

# API Configuration
ENVIRONMENT=local
API_V1_PREFIX=/api/v1
SECRET_KEY=your-secret-key-here

# CORS Configuration (development - allow all origins)
CORS_ORIGINS=*

# OpenAI Configuration (optional)
OPENAI_API_KEY=your-openai-api-key

# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=json

# Application Settings
PROJECT_NAME=Looped Needle API
VERSION=1.0.0
```

### 3. Setup Database

```bash
# Start PostgreSQL (if not running)
# Using Docker:
docker run -d \
  --name postgres \
  -e POSTGRES_PASSWORD=your_password \
  -e POSTGRES_DB=looped_needle \
  -p 5432:5432 \
  postgres:15

# Run migrations
alembic upgrade head
```

### 4. Run the Application

```bash
# Development mode
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Or using the run script
python -m src.main
```

### 5. Verify Installation

```bash
# Health check
curl http://localhost:8000/health

# Expected response:
# {"status": "healthy", "timestamp": "2025-01-27T...", "version": "1.0.0"}

# API documentation
# Open in browser: http://localhost:8000/docs
```

## Project Structure

```
looped-needle-api/
├── src/
│   ├── audits/              # Audits domain
│   │   ├── router.py
│   │   ├── schemas.py
│   │   ├── models.py
│   │   ├── service.py
│   │   ├── dependencies.py
│   │   ├── exceptions.py
│   │   └── constants.py
│   ├── openai/              # OpenAI service abstraction
│   │   ├── client.py
│   │   ├── schemas.py
│   │   ├── config.py
│   │   └── exceptions.py
│   ├── config.py            # Global configuration
│   ├── database.py          # Database connection
│   ├── exceptions.py        # Global exceptions
│   └── main.py             # FastAPI application
├── tests/
│   ├── audits/              # Audits domain tests
│   ├── contract/            # API contract tests
│   └── conftest.py         # Pytest fixtures
├── alembic/                 # Database migrations
├── .env                     # Environment variables (gitignored)
├── pyproject.toml           # Project configuration and dependencies
└── README.md
```

## Common Tasks

### Create a New Migration

```bash
# Generate migration
alembic revision --autogenerate -m "descriptive_slug"

# Apply migration
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/audits/test_router.py

# Run async tests
pytest tests/ -v
```

### Code Quality

```bash
# Lint code
ruff check src tests

# Format code
ruff format src tests

# Fix auto-fixable issues
ruff check --fix src tests
```

### API Testing Examples

```bash
# Create audit record
curl -X POST http://localhost:8000/api/v1/audits \
  -H "Content-Type: application/json" \
  -d '{
    "action_type": "create",
    "entity_type": "user",
    "entity_id": "123e4567-e89b-12d3-a456-426614174000",
    "status": "success"
  }'

# List audit records (default limit: 20, max: 50)
curl http://localhost:8000/api/v1/audits?limit=20&offset=0

# Get specific audit record
curl http://localhost:8000/api/v1/audits/{audit_id}

# Update audit record
curl -X PUT http://localhost:8000/api/v1/audits/{audit_id} \
  -H "Content-Type: application/json" \
  -d '{
    "status": "failure",
    "details": {"error": "Validation failed"}
  }'
```

## Development Workflow

1. **Create feature branch**: `git checkout -b feature/your-feature-name`
2. **Make changes**: Follow domain-driven structure and constitution principles
3. **Run tests**: `pytest` to ensure nothing breaks
4. **Check code quality**: `ruff check src tests`
5. **Commit changes**: `git commit -m "feat: your feature description"`
6. **Push and create PR**: Follow PR template and ensure constitution compliance

## Troubleshooting

### Database Connection Issues

```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Test connection
psql -h localhost -U postgres -d looped_needle

# Check DATABASE_URL format
echo $DATABASE_URL
# Should be: postgresql+asyncpg://user:password@host/dbname
```

### Migration Issues

```bash
# Check current migration version
alembic current

# View migration history
alembic history

# Create new migration if autogenerate missed changes
alembic revision -m "manual_migration_name"
```

### Import Errors

```bash
# Ensure virtual environment is activated
which python  # Should show venv path

# Reinstall dependencies
pip install -e ".[dev]" --force-reinstall
```

## Important Configuration Notes

### Authentication & Security
- **No Authentication**: All API endpoints are publicly accessible without authentication
- **CORS**: Configured to allow all origins (`*`) for development
- **Rate Limiting**: Not implemented in initial version

### Logging
- **Format**: Structured JSON logging
- **Level**: INFO (logs requests, responses, and errors)
- **Purpose**: Enables log aggregation and monitoring tools

### Pagination
- **Default**: 20 items per page
- **Maximum**: 50 items per page
- **Usage**: All list endpoints support `limit` and `offset` query parameters

## Next Steps

1. Review API documentation at `http://localhost:8000/docs`
2. Explore the audits domain implementation
3. Add new domains following the same structure
4. Implement additional features per user stories

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLModel Documentation](https://sqlmodel.tiangolo.com/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [OpenAI Python SDK](https://github.com/openai/openai-python)
- Project Constitution: `.specify/memory/constitution.md`

