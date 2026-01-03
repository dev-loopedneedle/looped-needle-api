# Data Model: Per-Profile Data Access with Clerk Authentication

**Date**: 2026-01-02  
**Feature**: 003-profile-data-access

## Overview

This document defines the database schema changes for user profile management and brand ownership. The schema extends the existing audit engine schema by adding user profiles and associating brands with users.

## Entity Relationships

```
UserProfile
└── owns_one Brand (one-to-one relationship)

Brand (modified)
├── belongs_to UserProfile (via user_id)
├── has_many Products
├── has_many SupplyChainNodes
├── has_many AuditInstances
└── has_many EvidenceFiles

(All brand-related resources inherit access control through brand ownership)
```

## Tables

### user_profiles

Represents a user authenticated via Clerk.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY, DEFAULT uuid_generate_v4() | Unique identifier |
| clerk_user_id | TEXT | NOT NULL, UNIQUE, INDEX | Clerk user identifier (stable, unique) |
| is_active | BOOLEAN | NOT NULL, DEFAULT true | Profile active status (false when Clerk account deleted) |
| created_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW(), INDEX | Creation timestamp |
| updated_at | TIMESTAMP WITH TIME ZONE | NULLABLE | Last update timestamp |
| last_access_at | TIMESTAMP WITH TIME ZONE | NULLABLE, INDEX | Last authentication timestamp |

**Indexes**:
- `idx_user_profiles_clerk_user_id` on `clerk_user_id` (unique index)
- `idx_user_profiles_is_active` on `is_active`
- `idx_user_profiles_last_access_at` on `last_access_at`

**Relationships**:
- Owns exactly one Brand (one-to-one via `brands.user_id`)

**Constraints**:
- `clerk_user_id` must be unique across all profiles (enforced by database unique constraint)
- `is_active` defaults to `true` on creation
- Profile is automatically created on first authenticated request
- Profile marked as inactive when Clerk account is deleted (preserves data)

**Notes**:
- `clerk_user_id` is the stable identifier from Clerk, used for identity mapping
- Unique constraint ensures idempotent profile creation (handles concurrent requests)
- `last_access_at` is updated on every successful authentication
- `is_active = false` prevents authentication but preserves all associated data
- Role is extracted from Clerk token `public_metadata.role` during authentication and stored in user context object (not persisted in database)
- Role is available in user context for access control decisions (admin-only endpoints)

---

### brands (modified)

**New Column Added**:

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| user_id | UUID | NULLABLE, UNIQUE, FOREIGN KEY -> user_profiles.id | Owner user profile identifier |

**New Indexes**:
- `idx_brands_user_id` on `user_id` (unique index to enforce one brand per user)

**New Constraints**:
- `user_id` must be unique (enforced by database unique constraint) - ensures one brand per user
- Foreign key constraint: `ON DELETE RESTRICT` (prevent user deletion if brand exists)
- `user_id` is nullable to support migration of existing orphaned brands

**Modified Relationships**:
- Now belongs to exactly one UserProfile (via `user_id`)
- Each UserProfile can own at most one Brand

**Migration Notes**:
- Existing brands will have `user_id = NULL` (orphaned)
- Orphaned brands remain inaccessible until manually associated with a user profile
- New brands must have `user_id` set (enforced by application logic, not database constraint)

---

## Access Control Rules

### User Profile Access

- Users can only access their own profile
- Profile creation is automatic (no explicit endpoint needed)
- Inactive profiles cannot authenticate

### Brand Access

- Users can only access brands they own (`brands.user_id = current_user.id`)
- Users can only create one brand (enforced by unique constraint on `user_id`)
- Soft-deleted brands are excluded from queries (`deleted_at IS NULL`)
- Orphaned brands (`user_id IS NULL`) are inaccessible

### Product Access

- Users can only access products belonging to their brands
- Filter: `products.brand_id IN (SELECT id FROM brands WHERE user_id = current_user.id AND deleted_at IS NULL)`

### Supply Chain Node Access

- Users can only access supply chain nodes belonging to their brands
- Filter: `supply_chain_nodes.brand_id IN (SELECT id FROM brands WHERE user_id = current_user.id AND deleted_at IS NULL)`

### Audit Instance Access

- Users can only access audit instances for their brands
- Filter: `audit_instances.brand_id IN (SELECT id FROM brands WHERE user_id = current_user.id AND deleted_at IS NULL)`

### Audit Item Access

- Users can only access audit items for their audit instances
- Filter: `audit_items.audit_instance_id IN (SELECT id FROM audit_instances WHERE brand_id IN (SELECT id FROM brands WHERE user_id = current_user.id AND deleted_at IS NULL))`

---

## State Transitions

### User Profile Lifecycle

1. **Creation**: Profile created automatically on first authenticated request
   - `clerk_user_id` extracted from verified Clerk token
   - `is_active = true`
   - `created_at = NOW()`
   - `last_access_at = NOW()`

2. **Authentication**: Profile retrieved and updated on each authenticated request
   - `last_access_at = NOW()`
   - If `is_active = false`, authentication is rejected

3. **Deactivation**: Profile marked inactive when Clerk account deleted
   - `is_active = false`
   - `updated_at = NOW()`
   - Authentication prevented, but data preserved

### Brand Ownership

1. **Brand Creation**: Brand automatically associated with authenticated user
   - `user_id = current_user.id`
   - Unique constraint ensures only one brand per user

2. **Brand Access**: Ownership validated before any operation
   - Read: Filter by `user_id`
   - Update/Delete: Validate `user_id = current_user.id` before allowing

---

## Validation Rules

### User Profile

- `clerk_user_id`: Required, must be non-empty string, must be unique
- `is_active`: Required, boolean, defaults to `true`
- Profile creation is idempotent: multiple requests for same `clerk_user_id` result in single profile

### Brand Ownership

- `user_id`: Required for new brands (application-level), nullable for migration
- Unique constraint: Each `user_id` can own at most one brand
- Foreign key: `user_id` must reference existing `user_profiles.id`
- Orphaned brands (`user_id IS NULL`) are inaccessible

---

## Migration Strategy

### Phase 1: Add User Profile Table

1. Create `user_profiles` table with all columns
2. Create unique index on `clerk_user_id`
3. Create indexes on `is_active` and `last_access_at`

### Phase 2: Add Brand Ownership

1. Add `user_id` column to `brands` table (nullable)
2. Create foreign key constraint to `user_profiles.id`
3. Create unique index on `brands.user_id` (enforces one brand per user)
4. Existing brands will have `user_id = NULL` (orphaned)

### Phase 3: Data Migration (Manual)

1. Orphaned brands remain inaccessible until manually associated
2. Admin tool or migration script can associate brands with user profiles
3. Once associated, users can access their brands normally

---

## Performance Considerations

- Index on `clerk_user_id` ensures fast profile lookups (<10ms)
- Index on `brands.user_id` ensures fast ownership checks (<10ms)
- Composite indexes may be needed for complex queries (e.g., `(user_id, deleted_at)`)
- Query filtering by `user_id` uses index for efficient data isolation
- `last_access_at` index enables tracking and analytics queries

---

## Security Considerations

- Unique constraint on `clerk_user_id` prevents duplicate profiles
- Foreign key constraints ensure referential integrity
- Database-level filtering prevents accidental data leaks
- Ownership validation before mutations prevents unauthorized access
- Inactive profiles cannot authenticate (prevents access to deleted Clerk accounts)

