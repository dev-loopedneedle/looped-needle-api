# Looped Needle API

FastAPI backend API for the Looped Needle project

## Features

- FastAPI with async/await support
- PostgreSQL database with async SQLAlchemy/SQLModel
- Domain-driven project structure
- Alembic database migrations
- OpenAI API integration
- Structured JSON logging
- OpenAPI/Swagger documentation

## Prerequisites

- Python 3.11 or higher
- PostgreSQL 12 or higher
- OpenAI API key (optional, for OpenAI integration)

## Quick Start

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd looped-needle-api
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -e ".[dev]"
   ```

4. **Configure environment variables**:
   Create a `.env` file in the project root:
   ```env
   POSTGRES_SERVER=localhost
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=your_password
   POSTGRES_DB=looped_needle
   DATABASE_URL=postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_SERVER}/${POSTGRES_DB}
   
   ENVIRONMENT=local
   API_V1_PREFIX=/api/v1
   SECRET_KEY=your-secret-key-here
   
   OPENAI_API_KEY=your-openai-api-key
   ```

5. **Run database migrations**:
   ```bash
   alembic upgrade head
   ```

6. **Start the API server**:
   ```bash
   uvicorn src.main:app --reload
   ```

7. **Access API documentation**:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## Project Structure

```
looped-needle-api/
├── src/
│   ├── audits/          # Audits domain
│   ├── openai/          # OpenAI service abstraction
│   ├── config.py        # Global configuration
│   ├── database.py      # Database connection
│   ├── exceptions.py    # Global exceptions
│   └── main.py          # FastAPI application
├── tests/               # Test files
├── alembic/             # Database migrations
└── pyproject.toml       # Project configuration
```

## Development

### Code Quality

```bash
# Lint code
ruff check src tests

# Format code
ruff format src tests

# Fix auto-fixable issues
ruff check --fix src tests
```

### Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## API Endpoints

### Root Endpoint
- `GET /` - API information and available endpoints

### Health Check Endpoints
- `GET /health` - Health check (returns API and database status)
  - Returns overall API health including database connectivity
  - Response includes status, timestamp, version, and individual service checks
- `GET /health/db` - Database health check
  - Specifically checks database connection status
  - Useful for monitoring and load balancer health checks

### Audits API Endpoints

**List Audit Records:**
- `GET /api/v1/audits` - List audit records with filtering and pagination
  - Query Parameters:
    - `action_type` (optional): Filter by action type (create, update, delete, view, etc.)
    - `entity_type` (optional): Filter by entity type (user, post, etc.)
    - `entity_id` (optional): Filter by entity ID (UUID)
    - `user_id` (optional): Filter by user ID (UUID)
    - `status` (optional): Filter by status (success, failure, pending)
    - `created_after` (optional): Filter by creation date (ISO 8601, after this date)
    - `created_before` (optional): Filter by creation date (ISO 8601, before this date)
    - `limit` (default: 20, max: 50): Number of records per page
    - `offset` (default: 0): Number of records to skip
  - Returns paginated list with total count

**Create Audit Record:**
- `POST /api/v1/audits` - Create a new audit record
  - Required fields: `action_type`, `entity_type`, `entity_id`
  - Optional fields: `user_id`, `details`, `status`, `ip_address`, `user_agent`
  - Returns created audit record with generated ID and timestamps

**Get Audit Record:**
- `GET /api/v1/audits/{audit_id}` - Get a specific audit record by ID
  - Path parameter: `audit_id` (UUID)
  - Returns 404 if not found

**Update Audit Record:**
- `PUT /api/v1/audits/{audit_id}` - Update an existing audit record
  - Only `status` and `details` fields can be updated
  - Other fields are immutable
  - Returns updated audit record

**Delete Audit Record:**
- `DELETE /api/v1/audits/{audit_id}` - Permanently delete an audit record
  - Returns 204 No Content on success
  - Returns 404 if not found

### API Documentation

Interactive API documentation is available at:
- **Swagger UI**: http://localhost:8000/docs
  - Interactive API explorer with "Try it out" functionality
  - View request/response schemas
  - Test endpoints directly from the browser
- **ReDoc**: http://localhost:8000/redoc
  - Clean, responsive API documentation
  - Better for reading and sharing documentation

All endpoints include:
- Complete OpenAPI/Swagger documentation
- Request/response schemas
- Example values
- Error response documentation

## Environment Variables

All configuration is managed through environment variables. Create a `.env` file in the project root (this file is gitignored).

### Required Variables

**Database Configuration:**
- `POSTGRES_SERVER` (default: `localhost`): PostgreSQL server hostname
- `POSTGRES_USER` (default: `postgres`): PostgreSQL username
- `POSTGRES_PASSWORD` (default: empty): PostgreSQL password
- `POSTGRES_DB` (default: `looped_needle`): Database name
- `DATABASE_URL` (optional): Full database connection URL. If not provided, will be constructed from individual POSTGRES_* variables.
  - Format: `postgresql+asyncpg://user:password@host/dbname`

**API Configuration:**
- `ENVIRONMENT` (default: `local`): Environment name (local, development, staging, production)
- `API_V1_PREFIX` (default: `/api/v1`): API version prefix for all endpoints
- `SECRET_KEY` (default: empty): Secret key for application security (required in production)

### Optional Variables

**CORS Configuration:**
- `CORS_ORIGINS` (default: `["*"]`): List of allowed CORS origins. Use `*` for development (allows all origins). For production, specify exact origins: `["https://example.com", "https://app.example.com"]`

**OpenAI Configuration:**
- `OPENAI_API_KEY` (optional): OpenAI API key for AI features. Required only if using OpenAI integration endpoints.

**Logging Configuration:**
- `LOG_LEVEL` (default: `INFO`): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `LOG_FORMAT` (default: `json`): Log format (`json` for structured logging, or standard format)

**Application Settings:**
- `PROJECT_NAME` (default: `Looped Needle API`): Application name displayed in API docs
- `VERSION` (default: `1.0.0`): Application version

### Example `.env` File

```env
# Database Configuration
POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=looped_needle
# DATABASE_URL is optional - will be auto-constructed if not provided
# DATABASE_URL=postgresql+asyncpg://postgres:password@localhost/looped_needle

# API Configuration
ENVIRONMENT=local
API_V1_PREFIX=/api/v1
SECRET_KEY=your-secret-key-change-in-production

# CORS Configuration (development - allow all origins)
CORS_ORIGINS=*

# OpenAI Configuration (optional)
OPENAI_API_KEY=sk-your-openai-api-key-here

# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=json

# Application Settings
PROJECT_NAME=Looped Needle API
VERSION=1.0.0
```

### Production Considerations

- **Never commit `.env` files** to version control
- Use secure secret management (e.g., AWS Secrets Manager, HashiCorp Vault) in production
- Set `CORS_ORIGINS` to specific domains, not `*`
- Use strong `SECRET_KEY` values
- Set `LOG_LEVEL` to `INFO` or `WARNING` in production
- Ensure `DATABASE_URL` uses SSL/TLS in production

## API Examples

### Health Check

**Check API health:**
```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-27T12:00:00Z",
  "version": "1.0.0",
  "checks": {
    "database": {
      "status": "healthy",
      "message": "Database connection check"
    }
  }
}
```

**Check database health:**
```bash
curl http://localhost:8000/health/db
```

### Create Audit Record

**Create a new audit record:**
```bash
curl -X POST http://localhost:8000/api/v1/audits \
  -H "Content-Type: application/json" \
  -d '{
    "action_type": "create",
    "entity_type": "user",
    "entity_id": "123e4567-e89b-12d3-a456-426614174000",
    "user_id": "987e6543-e21b-43d2-b654-321098765432",
    "status": "success",
    "details": {
      "field": "email",
      "old_value": null,
      "new_value": "user@example.com"
    },
    "ip_address": "192.168.1.1",
    "user_agent": "Mozilla/5.0..."
  }'
```

**Response (201 Created):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "action_type": "create",
  "entity_type": "user",
  "entity_id": "123e4567-e89b-12d3-a456-426614174000",
  "user_id": "987e6543-e21b-43d2-b654-321098765432",
  "status": "success",
  "details": {
    "field": "email",
    "old_value": null,
    "new_value": "user@example.com"
  },
  "ip_address": "192.168.1.1",
  "user_agent": "Mozilla/5.0...",
  "created_at": "2025-01-27T12:00:00Z",
  "updated_at": null
}
```

### List Audit Records

**List all audit records (paginated):**
```bash
curl "http://localhost:8000/api/v1/audits?limit=20&offset=0"
```

**List with filters:**
```bash
# Filter by action type
curl "http://localhost:8000/api/v1/audits?action_type=create&limit=10"

# Filter by entity type and user
curl "http://localhost:8000/api/v1/audits?entity_type=user&user_id=987e6543-e21b-43d2-b654-321098765432"

# Filter by date range
curl "http://localhost:8000/api/v1/audits?created_after=2025-01-01T00:00:00Z&created_before=2025-01-31T23:59:59Z"

# Combine multiple filters
curl "http://localhost:8000/api/v1/audits?action_type=update&entity_type=user&status=success&limit=50&offset=0"
```

**Response (200 OK):**
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "action_type": "create",
      "entity_type": "user",
      "entity_id": "123e4567-e89b-12d3-a456-426614174000",
      "status": "success",
      "created_at": "2025-01-27T12:00:00Z",
      ...
    }
  ],
  "total": 150,
  "limit": 20,
  "offset": 0
}
```

### Get Audit Record

**Get a specific audit record by ID:**
```bash
curl "http://localhost:8000/api/v1/audits/550e8400-e29b-41d4-a716-446655440000"
```

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "action_type": "create",
  "entity_type": "user",
  "entity_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "success",
  "created_at": "2025-01-27T12:00:00Z",
  ...
}
```

**Error Response (404 Not Found):**
```json
{
  "error": "AuditNotFound",
  "message": "Audit record with id 550e8400-e29b-41d4-a716-446655440000 not found",
  "status_code": 404,
  "detail": "The requested audit record does not exist or has been deleted.",
  "request_id": "abc123-def456-ghi789"
}
```

### Update Audit Record

**Update audit record status and details:**
```bash
curl -X PUT http://localhost:8000/api/v1/audits/550e8400-e29b-41d4-a716-446655440000 \
  -H "Content-Type: application/json" \
  -d '{
    "status": "failure",
    "details": {
      "error": "Validation failed",
      "field": "email",
      "reason": "Invalid email format"
    }
  }'
```

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "failure",
  "details": {
    "error": "Validation failed",
    "field": "email",
    "reason": "Invalid email format"
  },
  "updated_at": "2025-01-27T12:05:00Z",
  ...
}
```

### Delete Audit Record

**Delete an audit record:**
```bash
curl -X DELETE http://localhost:8000/api/v1/audits/550e8400-e29b-41d4-a716-446655440000
```

**Response (204 No Content):**
```
(empty body)
```

## Error Responses

All error responses follow a consistent format:

```json
{
  "error": "ErrorType",
  "message": "Human-readable error message",
  "status_code": 400,
  "detail": "Additional context about the error",
  "request_id": "abc123-def456-ghi789"
}
```

**Common Error Codes:**
- `400 Bad Request`: Invalid request data or validation errors
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server-side error

**Request ID**: All responses include an `X-Request-ID` header and `request_id` field in error responses for correlation with logs.

## License

[Add your license here]

