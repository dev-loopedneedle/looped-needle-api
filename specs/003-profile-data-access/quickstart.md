# Quickstart: Per-Profile Data Access with Clerk Authentication

**Date**: 2026-01-02  
**Feature**: 003-profile-data-access

## Prerequisites

- Python 3.11+
- PostgreSQL 12+ with UUID extension support
- Clerk account and application configured
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
- `clerk-sdk-python` - Official Clerk Python SDK for authentication

### 2. Clerk Setup

1. Create a Clerk account at https://clerk.com
2. Create a new application
3. Get your API keys:
   - **Publishable Key**: Used by frontend
   - **Secret Key**: Used by backend for token verification
4. Configure environment variables (see step 3)

### 3. Environment Configuration

Create or update `.env` file:

```bash
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/looped_needle_db
ENVIRONMENT=local
LOG_LEVEL=INFO
LOG_FORMAT=json

# Clerk Configuration
CLERK_SECRET_KEY=sk_test_...
CLERK_PUBLISHABLE_KEY=pk_test_...
```

### 4. Run Database Migrations

```bash
# Create migration for user profiles and brand ownership
alembic revision --autogenerate -m "add_user_profiles_and_brand_ownership"

# Review the generated migration file
# Edit alembic/versions/[timestamp]_add_user_profiles_and_brand_ownership.py if needed

# Apply migration
alembic upgrade head
```

**Migration includes**:
- `user_profiles` table with Clerk user ID, active status, timestamps
- `user_id` column added to `brands` table (nullable for migration)
- Unique constraints on `clerk_user_id` and `brands.user_id`
- Indexes for performance

### 5. Start the API Server

```bash
# Development server with auto-reload
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Or using make (if Makefile has target)
make dev
```

API will be available at:
- API: http://localhost:8000/api/v1
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

## Usage

### Authentication Flow

1. **Frontend authenticates with Clerk** (handled by Clerk SDK)
2. **Frontend sends token in API requests**:
   ```javascript
   const token = await clerk.session.getToken();
   fetch('/api/v1/brands', {
     headers: {
       'Authorization': `Bearer ${token}`
     }
   });
   ```
3. **Backend validates token** and creates/retrieves user profile automatically
4. **User context is available** in all authenticated endpoints

### Creating a Brand (Authenticated)

```bash
# Get Clerk token from frontend (example)
TOKEN="your_clerk_jwt_token"

# Create brand (automatically associated with authenticated user)
curl -X POST http://localhost:8000/api/v1/brands \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Acme Corp",
    "registration_country": "US",
    "company_size": "Large",
    "target_markets": ["US", "CA", "EU"]
  }'
```

### Accessing Your Brand Data

```bash
# List your brands (only returns brands you own)
curl http://localhost:8000/api/v1/brands \
  -H "Authorization: Bearer $TOKEN"

# Get your profile
curl http://localhost:8000/api/v1/me \
  -H "Authorization: Bearer $TOKEN"
```

### Access Control Examples

**Authorized Access** (your own brand):
```bash
# This works - you own this brand
curl http://localhost:8000/api/v1/brands/{your_brand_id} \
  -H "Authorization: Bearer $TOKEN"
```

**Unauthorized Access** (another user's brand):
```bash
# This fails with 403 Forbidden
curl http://localhost:8000/api/v1/brands/{other_user_brand_id} \
  -H "Authorization: Bearer $TOKEN"
# Response: {"error": "AccessDenied", "message": "You do not have access to this resource"}
```

## Testing

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/auth --cov=src/audit_engine

# Run specific test file
pytest tests/auth/test_router.py
```

### Test Authentication

Tests use mock Clerk tokens. See `tests/auth/` for examples.

## Migration of Existing Data

### Orphaned Brands

Brands created before authentication implementation will have `user_id = NULL` (orphaned). These brands are inaccessible until manually associated with a user profile.

**To associate an orphaned brand with a user**:

1. Get the brand ID and user profile ID
2. Run SQL update:
   ```sql
   UPDATE brands 
   SET user_id = 'user_profile_uuid_here' 
   WHERE id = 'brand_uuid_here';
   ```
3. Verify the association:
   ```sql
   SELECT b.*, u.clerk_user_id 
   FROM brands b 
   JOIN user_profiles u ON b.user_id = u.id 
   WHERE b.id = 'brand_uuid_here';
   ```

**Note**: Ensure the user doesn't already have a brand (unique constraint on `user_id`).

## Troubleshooting

### Authentication Errors

**401 Unauthorized**:
- Token is invalid or expired
- Check that token is being sent in `Authorization: Bearer <token>` header
- Verify Clerk secret key is correct in environment variables

**503 Service Unavailable**:
- Clerk authentication service is unavailable
- Check network connectivity
- Verify Clerk API status

### Profile Creation Issues

**Duplicate Profile Error**:
- Should not occur due to unique constraint
- If it does, check database for duplicate `clerk_user_id` values
- Verify migration was applied correctly

### Access Denied Errors

**403 Forbidden**:
- User is trying to access another user's data
- Verify brand ownership: `SELECT user_id FROM brands WHERE id = '...'`
- Check that user profile is active: `SELECT is_active FROM user_profiles WHERE id = '...'`

## Next Steps

- Review [data-model.md](./data-model.md) for database schema details
- Review [contracts/auth-api.yaml](./contracts/auth-api.yaml) for API specifications
- See [plan.md](./plan.md) for implementation details

