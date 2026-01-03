# Research: Per-Profile Data Access with Clerk Authentication

**Date**: 2026-01-02  
**Feature**: 003-profile-data-access

## Research Questions

### 1. Clerk Python SDK Integration for FastAPI

**Question**: What is the best way to integrate Clerk authentication with FastAPI for token validation?

**Research Findings**:
- **Clerk Python SDK** (`clerk-sdk-python`) provides official Python client
- Supports JWT token verification using Clerk's public keys
- Can verify tokens locally (JWT) or via API calls to Clerk
- JWT verification is faster and doesn't require network calls
- SDK handles token expiration and signature validation automatically
- Supports async operations

**Decision**: Use Clerk Python SDK with JWT verification for token validation.

**Rationale**: 
- JWT verification is faster (<50ms) than API calls (>100ms)
- Reduces dependency on Clerk API availability (can cache public keys)
- Official SDK ensures compatibility and security
- Supports async operations matching FastAPI patterns
- Handles token expiration and signature validation automatically

**Alternatives Considered**:
- **Direct API calls to Clerk**: Slower, requires network, fails if Clerk unavailable
- **Manual JWT verification**: More complex, need to manage public keys, reinventing the wheel
- **Third-party JWT libraries**: Less integration with Clerk-specific features

**Implementation Notes**:
- Install: `pip install clerk-sdk-python`
- Use `clerk_client.verify_token()` for JWT verification
- Cache Clerk public keys (JWKS) with TTL to reduce API calls
- Handle `clerk.exceptions.ClerkException` for invalid tokens
- Extract user ID from verified token claims (typically `sub` or `id` field)
- Extract `public_metadata` from verified token claims to access user role
- `public_metadata` is included in JWT token when configured in Clerk, no additional API call needed

---

### 2. FastAPI Authentication Dependency Pattern

**Question**: What is the best pattern for implementing authentication dependencies in FastAPI?

**Research Findings**:
- FastAPI `Depends()` is the standard pattern for authentication
- Create a dependency function that validates token and returns user context
- Use `HTTPBearer` or `HTTPAuthorizationCredentials` for token extraction
- Dependency can raise `HTTPException` for authentication failures
- User context can be injected into route handlers via dependency
- Can create reusable `get_current_user` dependency

**Decision**: Use FastAPI `Depends()` with a `get_current_user` dependency function.

**Rationale**: 
- Standard FastAPI pattern, well-documented
- Clean separation of concerns
- Easy to test with dependency overrides
- Supports async operations
- Can be reused across all authenticated endpoints

**Alternatives Considered**:
- **Middleware approach**: Less flexible, harder to test, runs for all requests
- **Decorator approach**: Less idiomatic for FastAPI, harder to compose
- **Route-level checks**: Duplicates code, harder to maintain

**Implementation Notes**:
- Create `get_current_user` dependency in `src/auth/dependencies.py`
- Use `HTTPBearer` security scheme for token extraction
- Validate token using Clerk SDK
- Return user profile (create if doesn't exist)
- Raise `HTTPException(status_code=401)` for invalid tokens
- Raise `HTTPException(status_code=503)` when Clerk service unavailable

---

### 3. Database Schema Design for User Profiles and Brand Ownership

**Question**: How should user profiles and brand ownership be modeled in the database?

**Research Findings**:
- User profile table with unique constraint on Clerk user ID
- Brand table needs `user_id` foreign key (nullable initially for migration)
- One-to-one relationship: one brand per user
- Use database unique constraint to enforce one brand per user
- Add `is_active` boolean field to user profiles for soft-disable
- Add `last_access_at` timestamp for tracking

**Decision**: Create `user_profiles` table with unique `clerk_user_id`, add `user_id` foreign key to `brands` table.

**Rationale**: 
- Database-level constraints ensure data integrity
- Unique constraint on Clerk user ID prevents duplicates
- Foreign key ensures referential integrity
- Nullable `user_id` in brands allows migration of existing data
- `is_active` flag enables soft-disable without data loss

**Alternatives Considered**:
- **Separate ownership table**: More complex, unnecessary for one-to-one relationship
- **Store Clerk user ID in brands directly**: Less normalized, harder to extend
- **No user profile table**: Can't track profile metadata, harder to manage

**Implementation Notes**:
- Create `user_profiles` table with columns: `id` (UUID), `clerk_user_id` (string, unique), `is_active` (boolean, default true), `created_at`, `updated_at`, `last_access_at`
- Add `user_id` foreign key to `brands` table (nullable, unique constraint)
- Migration: Add `user_id` column to existing brands (nullable)
- Create unique constraint on `brands.user_id` to enforce one brand per user
- Create index on `user_profiles.clerk_user_id` for fast lookups

---

### 4. Idempotent Profile Creation Pattern

**Question**: How to ensure idempotent user profile creation when multiple requests arrive simultaneously?

**Research Findings**:
- Database unique constraint on `clerk_user_id` prevents duplicates
- Use "upsert" pattern: try to insert, catch unique violation, then select
- PostgreSQL `ON CONFLICT` clause can handle this atomically
- SQLAlchemy supports `merge()` or raw SQL with `ON CONFLICT`
- Race condition: two requests try to create same profile simultaneously
- Unique constraint ensures only one succeeds, other gets constraint violation

**Decision**: Use database unique constraint with "insert or retrieve" pattern (upsert).

**Rationale**: 
- Database-level constraint is most reliable
- Atomic operation prevents race conditions
- Standard PostgreSQL pattern
- No need for application-level locking
- Handles concurrent requests automatically

**Alternatives Considered**:
- **Application-level locking**: More complex, requires distributed lock for multi-instance
- **Check-then-insert**: Race condition possible, not atomic
- **Separate creation endpoint**: Doesn't match requirement for automatic creation

**Implementation Notes**:
- Use SQLAlchemy `session.merge()` or raw SQL with `ON CONFLICT`
- Catch `IntegrityError` for unique constraint violation
- On violation, query for existing profile and return it
- Update `last_access_at` on every authentication
- Ensure transaction isolation level is sufficient

---

### 5. Access Control Enforcement Pattern

**Question**: How to efficiently enforce access control across all brand-related resources?

**Research Findings**:
- Filter all queries by `user_id` at the database level
- Use SQL WHERE clauses to ensure users only see their own data
- Validate ownership before any update/delete operations
- Use JOIN queries to check ownership through brand relationship
- Cache user's brand_id in request context to avoid repeated queries

**Decision**: Filter all queries by user ownership at the database level, validate ownership before mutations.

**Rationale**: 
- Database-level filtering is most efficient
- Prevents accidental data leaks
- Consistent pattern across all resources
- Can use database indexes for performance
- Clear separation: user context from dependency, ownership checks in service layer

**Alternatives Considered**:
- **Application-level filtering**: Less efficient, risk of missing filters
- **Middleware filtering**: Less flexible, harder to customize per endpoint
- **Separate access control service**: Over-engineered for current needs

**Implementation Notes**:
- All list endpoints: `WHERE user_id = current_user.id` or `WHERE brand.user_id = current_user.id`
- All get-by-id endpoints: Check ownership before returning
- All update/delete endpoints: Validate ownership before allowing operation
- Use SQLAlchemy query filters: `.filter(Brand.user_id == current_user.id)`
- Raise `HTTPException(status_code=403)` for unauthorized access
- For nested resources (products, audit items): Join through brand to check ownership

---

### 6. Clerk Service Unavailability Handling

**Question**: How should the system behave when Clerk authentication service is unavailable?

**Research Findings**:
- Clerk SDK can fail with network errors or timeouts
- JWT verification can fail if public keys can't be fetched
- Options: reject all requests, allow cached tokens, fallback authentication
- Security best practice: fail closed (reject if can't verify)

**Decision**: Reject all authenticated requests with 503 Service Unavailable when Clerk is unavailable.

**Rationale**: 
- Security best practice: fail closed (default deny)
- Prevents unauthorized access during outages
- Clear error message guides users
- Matches requirement FR-022
- Users can retry when service recovers

**Alternatives Considered**:
- **Allow cached tokens**: Security risk, tokens may be expired or revoked
- **Fallback authentication**: Not specified, adds complexity
- **Grace period**: Security risk, unclear how long

**Implementation Notes**:
- Catch `clerk.exceptions.ClerkException` for service errors
- Catch network/timeout exceptions from HTTP client
- Return `HTTPException(status_code=503, detail="Authentication service unavailable")`
- Log error for monitoring
- Don't cache this error (retry on next request)

---

### 7. Clerk Public Metadata and Role Extraction

**Question**: How to extract user role from Clerk public_metadata in JWT token for role-based access control?

**Research Findings**:
- Clerk includes `public_metadata` in JWT token claims when configured
- `public_metadata` is accessible directly from verified token without additional API calls
- Token verification returns decoded claims including `public_metadata` dictionary
- Role can be stored in `public_metadata.role` field
- Fast extraction (<10ms) since it's part of JWT verification process
- No need to fetch user object from Clerk API if metadata is in token

**Decision**: Extract role from `public_metadata` in JWT token claims during token verification.

**Rationale**: 
- Fastest approach (no additional API calls)
- Metadata is already in token, no extra network request
- Consistent with JWT verification flow
- Role available immediately after token verification
- No caching needed since it's part of token verification

**Alternatives Considered**:
- **Fetch user object from Clerk API**: Slower, requires network call, unnecessary if metadata in token
- **Store role in database**: Requires sync mechanism, can become stale
- **Separate role lookup**: Adds complexity and latency

**Implementation Notes**:
- After token verification, extract `public_metadata` from decoded claims
- Access role via `public_metadata.get("role")` or `public_metadata.get("role", None)`
- Store role in user context object for use in dependencies
- Create `get_admin_user` dependency that checks `current_user.role == "admin"`
- Return 403 Forbidden if role is not "admin" or missing

---

## Summary

All research questions resolved. Key decisions:
1. Use Clerk Python SDK with JWT verification
2. FastAPI `Depends()` pattern for authentication
3. Database schema with unique constraints for idempotent creation
4. Database-level access control filtering
5. Fail-closed approach for Clerk unavailability
6. Extract role from `public_metadata` in JWT token claims (no API call needed)

Ready to proceed to Phase 1: Design & Contracts.

