# Quickstart: Dynamic Audit Inference Engine

**Date**: 2025-01-27  
**Feature**: 002-inference-engine-schema

## Prerequisites

- Python 3.11+
- PostgreSQL 12+ with UUID extension support
- pip or uv package manager
- Git

## Installation

### 1. Install Dependencies

```bash
# Install Python dependencies
pip install -e ".[dev]"

# Or using uv
uv pip install -e ".[dev]"
```

**New dependencies for this feature**:
- `simpleeval` - Safe expression evaluation library (with custom helper functions)

### 2. Database Setup

Create a PostgreSQL database:

```bash
# Using psql
createdb looped_needle_db

# Or using SQL
psql -c "CREATE DATABASE looped_needle_db;"
```

Enable UUID extension:

```bash
psql looped_needle_db -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"
```

### 3. Environment Configuration

Create or update `.env` file:

```bash
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/looped_needle_db
ENVIRONMENT=local
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### 4. Run Database Migrations

```bash
# Create migration for inference engine schema
alembic revision --autogenerate -m "create_inference_schema"

# Review the generated migration file
# Edit alembic/versions/[timestamp]_create_inference_schema.py if needed

# Apply migration
alembic upgrade head
```

**Migration includes**:
- `brands` table
- `products` table
- `supply_chain_nodes` table
- `sustainability_criteria` table
- `criteria_rules` table
- `questionnaire_definitions` table
- `audit_instances` table
- `audit_items` table
- `evidence_files` table
- `audit_item_evidence_links` table
- All indexes and constraints

### 5. Start the API Server

```bash
# Development server with auto-reload
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Or using make (if Makefile has target)
make run
```

API will be available at:
- API: http://localhost:8000/api/v1
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

## Testing

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/inference/test_router.py
```

### Test API Endpoints

Using `curl`:

```bash
# Health check
curl http://localhost:8000/health

# Create a brand
curl -X POST http://localhost:8000/api/v1/brands \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Example Brand",
    "registration_country": "US",
    "company_size": "SME",
    "target_markets": ["EU", "US"]
  }'

# List brands
curl http://localhost:8000/api/v1/brands
```

Using Python `httpx`:

```python
import httpx

async with httpx.AsyncClient() as client:
    # Create brand
    response = await client.post(
        "http://localhost:8000/api/v1/brands",
        json={
            "name": "Example Brand",
            "registration_country": "US",
            "company_size": "SME",
            "target_markets": ["EU", "US"]
        }
    )
    brand = response.json()
    print(f"Created brand: {brand['id']}")
```

## Example Workflow

### 1. Create Brand Profile

```bash
# Create brand
BRAND_ID=$(curl -s -X POST http://localhost:8000/api/v1/brands \
  -H "Content-Type: application/json" \
  -d '{
    "name": "EcoFashion Co",
    "registration_country": "US",
    "company_size": "SME",
    "target_markets": ["EU", "US"]
  }' | jq -r '.id')

echo "Brand ID: $BRAND_ID"
```

### 2. Add Products

```bash
# Add product
curl -X POST "http://localhost:8000/api/v1/brands/$BRAND_ID/products" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Organic Cotton T-Shirt",
    "category": "Apparel",
    "materials_composition": [
      {"material": "Cotton", "percent": 100}
    ],
    "manufacturing_processes": ["CutAndSew"]
  }'
```

### 3. Create Sustainability Criterion

```bash
# Create criterion
CRITERION_ID=$(curl -s -X POST http://localhost:8000/api/v1/criteria \
  -H "Content-Type: application/json" \
  -d '{
    "code": "ENV-001",
    "name": "Organic Material Certification",
    "description": "Product must use certified organic materials",
    "domain": "Environmental"
  }' | jq -r '.id')

echo "Criterion ID: $CRITERION_ID"
```

### 4. Create Rule

```bash
# Create rule
curl -X POST "http://localhost:8000/api/v1/criteria/$CRITERION_ID/rules" \
  -H "Content-Type: application/json" \
  -d '{
    "rule_name": "Organic Cotton Rule",
    "condition_expression": "context.materials_composition.some(m => m.material == '\''Cotton'\'' && m.percent >= 50)",
    "priority": 10
  }'
```

### 5. Create Audit Instance

```bash
# Get questionnaire definition ID (create one first if needed)
QUESTIONNAIRE_ID=$(curl -s http://localhost:8000/api/v1/questionnaires?is_active=true | jq -r '.items[0].id')

# Create audit instance
AUDIT_ID=$(curl -s -X POST http://localhost:8000/api/v1/audit-instances \
  -H "Content-Type: application/json" \
  -d "{
    \"brand_id\": \"$BRAND_ID\",
    \"questionnaire_definition_id\": \"$QUESTIONNAIRE_ID\",
    \"scoping_responses\": {
      \"audit_scope_type\": \"collection_specific\",
      \"supply_chain_depth\": \"tier_1\",
      \"production_season\": \"SS24\",
      \"has_wet_processing\": false,
      \"new_suppliers_onboarded\": false
    }
  }" | jq -r '.id')

echo "Audit Instance ID: $AUDIT_ID"
```

### 6. Generate Audit Items

```bash
# Trigger audit item generation
curl -X POST "http://localhost:8000/api/v1/audit-instances/$AUDIT_ID/generate-items" \
  -H "Content-Type: application/json"

# List generated audit items
curl "http://localhost:8000/api/v1/audit-instances/$AUDIT_ID/items"
```

## Development

### Project Structure

```
src/inference/
├── __init__.py
├── router.py          # FastAPI routes
├── schemas.py         # Pydantic models
├── models.py          # SQLModel DB models
├── dependencies.py    # Domain dependencies
├── constants.py       # Enums, constants
├── exceptions.py      # Domain exceptions
├── service.py         # Business logic
└── utils.py           # Helper functions
```

### Key Components

1. **Models** (`models.py`): SQLModel database models for all entities
2. **Schemas** (`schemas.py`): Pydantic models for API request/response
3. **Router** (`router.py`): FastAPI route handlers
4. **Service** (`service.py`): Business logic including:
   - Rule evaluation using ExpressionEvaluator
   - Audit item generation
   - State transition validation
   - Soft delete checks

### Adding New Rules

Rules use Python-like expressions that can reference:
- `context.*` - Brand context (products, supply chain, etc.)
- `scope.*` - Questionnaire responses

Example expressions:
```javascript
// Check if brand has products with specific material
context.products.some(p => p.materials_composition.some(m => m.material == 'Leather'))

// Check supply chain depth
scope.supply_chain_depth == 'full_chain'

// Check company size
context.company_size == 'Large'

// Combined conditions
context.target_markets.includes('EU') && scope.has_wet_processing == true
```

## Troubleshooting

### Migration Issues

```bash
# Check current migration version
alembic current

# Rollback last migration
alembic downgrade -1

# View migration history
alembic history
```

### Database Connection

```bash
# Test database connection
python -c "from src.database import check_database_health; import asyncio; print(asyncio.run(check_database_health()))"
```

### Expression Evaluation Errors

Invalid expressions will be logged but won't block audit generation. Check logs for:
```
ERROR: Rule evaluation failed for rule_id={rule_id}: {error_message}
```

## Next Steps

1. Review API documentation at http://localhost:8000/docs
2. Explore API contracts in `contracts/` directory
3. Review data model in `data-model.md`
4. Check research decisions in `research.md`
5. Proceed to implementation tasks in `tasks.md` (generated by `/speckit.tasks`)

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLModel Documentation](https://sqlmodel.tiangolo.com/)
- See `src/inference/EXPRESSION_SYNTAX.md` for expression syntax guide
- [Alembic Documentation](https://alembic.sqlalchemy.org/)

