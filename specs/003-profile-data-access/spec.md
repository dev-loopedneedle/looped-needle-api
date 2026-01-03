# Feature Specification: Per-Profile Data Access with Clerk Authentication

**Feature Branch**: `003-profile-data-access`  
**Created**: 2026-01-02  
**Status**: Draft  
**Input**: User description: "we need a per-profile data access. we need an auth system that will use clerk auth we have on frontend to create and access specific profile, have access to his personal and brand information, brand audits"

## Clarifications

### Session 2026-01-02

- Q: Should users be able to create multiple brand profiles, or is it one brand per user? → A: One brand profile per user (users represent brand administrators)
- Q: What happens when a user tries to access another user's brand data? → A: Access is denied with appropriate error response
- Q: Should the system support role-based access (e.g., brand admin vs auditor)? → A: System supports role-based access using Clerk public_metadata. Users with { role: "admin" } in metadata can access admin-only endpoints
- Q: For audits, should admins see all audits and non-admins only their brand's audits? → A: Yes. Admins can access audit instances (and their items) across all brands; non-admins are limited to audits for their owned brand.
- Q: How should the system handle Clerk user creation - automatic on first API call or explicit profile creation endpoint? → A: Automatic profile creation on first authenticated API call if profile doesn't exist
- Q: How should existing brands and audit instances (created before authentication) be handled during deployment? → A: Orphaned brands remain inaccessible until manually associated with a user profile (via admin tool or migration script)
- Q: How should the system handle requests when Clerk authentication service is unavailable or returns errors? → A: Reject all authenticated requests with authentication service unavailable error
- Q: How should the system handle multiple simultaneous requests from the same Clerk user attempting to create a profile? → A: Use database unique constraint on Clerk user ID with idempotent creation (insert or retrieve)
- Q: How should the system handle user profiles when the corresponding Clerk user account is deleted? → A: Mark user profile as inactive/disabled and prevent authentication (preserve data)
- Q: Should users be able to access their own brands that have been soft-deleted? → A: Users cannot access soft-deleted brands (return not found or access denied)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - User Profile Creation and Authentication (Priority: P1)

As a brand administrator, I need to authenticate using Clerk and have my profile automatically created in the system so that I can access my personal information and brand data.

**Why this priority**: Authentication and profile creation are foundational requirements. Without user identity, no data access control can be implemented.

**Independent Test**: Can be fully tested by authenticating with Clerk token, verifying profile is created or retrieved, and confirming user can access their own profile data. Delivers immediate value by establishing user identity and enabling personalized data access.

**Acceptance Scenarios**:

1. **Given** I am authenticated with Clerk, **When** I make my first API request with a valid Clerk token, **Then** my user profile is automatically created in the system and I receive confirmation
2. **Given** I have an existing profile, **When** I authenticate with a valid Clerk token, **Then** my existing profile is retrieved and I can access my data
3. **Given** I provide an invalid or expired Clerk token, **When** I make an API request, **Then** I receive an authentication error and access is denied
4. **Given** I am authenticated, **When** I retrieve my profile information, **Then** I see my user details including Clerk user ID, role (from public_metadata), and creation timestamp

---

### User Story 2 - Brand Profile Access Control (Priority: P1)

As a brand administrator, I need to access only my own brand's information so that I can manage my brand profile, products, and supply chain data without seeing other brands' confidential information.

**Why this priority**: Data isolation is a critical security requirement. Users must only access their own brand data to maintain confidentiality and prevent unauthorized access.

**Independent Test**: Can be fully tested by creating brands for different users, authenticating as each user, and verifying each user can only access their own brand data. Delivers value by ensuring data privacy and security.

**Acceptance Scenarios**:

1. **Given** I am authenticated as User A, **When** I create a brand profile, **Then** the brand is associated with my user profile and I can retrieve it
2. **Given** I am authenticated as User A, **When** I query my brand information, **Then** I see only brands associated with my user profile
3. **Given** User B has created a brand, **When** I authenticate as User A and attempt to access User B's brand by ID, **Then** I receive an access denied error
4. **Given** I am authenticated, **When** I update my brand profile, **Then** only my brand data is modified and changes are persisted
5. **Given** I am authenticated, **When** I delete my brand, **Then** only my brand is removed and I receive confirmation

---

### User Story 3 - Brand Products and Supply Chain Access (Priority: P2)

As a brand administrator, I need to access and manage products and supply chain nodes for my brand so that I can maintain complete brand information for audit purposes.

**Why this priority**: Products and supply chain data are part of brand context needed for audits. Users need full access to manage their brand's complete profile.

**Independent Test**: Can be fully tested by creating products and supply chain nodes for a brand, authenticating as the brand owner, and verifying access is restricted to that brand's data. Delivers value by enabling complete brand profile management.

**Acceptance Scenarios**:

1. **Given** I am authenticated and have a brand, **When** I create a product for my brand, **Then** the product is associated with my brand and I can retrieve it
2. **Given** I am authenticated, **When** I list products for my brand, **Then** I see only products belonging to my brand
3. **Given** User B has products for their brand, **When** I authenticate as User A and attempt to access User B's products, **Then** I receive an access denied error
4. **Given** I am authenticated and have a brand, **When** I create supply chain nodes for my brand, **Then** the nodes are associated with my brand and I can retrieve them
5. **Given** I am authenticated, **When** I list supply chain nodes for my brand, **Then** I see only nodes belonging to my brand

---

### User Story 4 - Audit Instance Access Control (Priority: P2)

As a brand administrator, I need to access only audit instances created for my brand so that I can view audit history, status, and manage audit items without accessing other brands' audit data.

**Why this priority**: Audit data is sensitive and must be isolated per brand. Users need access to their own audit instances to track progress and manage compliance.

**Independent Test**: Can be fully tested by creating audit instances for different brands, authenticating as each brand owner, and verifying each user can only access their own audit instances. Delivers value by ensuring audit data privacy.

**Acceptance Scenarios**:

1. **Given** I am authenticated and have a brand, **When** I create an audit instance for my brand, **Then** the audit instance is associated with my brand and I can retrieve it
2. **Given** I am authenticated, **When** I list audit instances, **Then** I see only audit instances for brands I own
3. **Given** User B has created an audit instance for their brand, **When** I authenticate as User A and attempt to access User B's audit instance by ID, **Then** I receive an access denied error
4. **Given** I am authenticated, **When** I update an audit instance for my brand, **Then** only my audit instance is modified and changes are persisted
5. **Given** I am authenticated, **When** I generate audit items for my audit instance, **Then** items are created for my audit instance and I can retrieve them
6. **Given** I am authenticated with role "admin", **When** I list audit instances, **Then** I see audit instances across all brands
7. **Given** I am authenticated with role "admin", **When** I retrieve an audit instance by ID for any brand, **Then** I can access it successfully

---

### User Story 5 - Audit Item Access Control (Priority: P2)

As a brand administrator, I need to access and manage audit items for my audit instances so that I can track compliance requirements and provide evidence without accessing other brands' audit items.

**Why this priority**: Audit items contain sensitive compliance information. Users must only access items for their own audit instances to maintain data privacy.

**Independent Test**: Can be fully tested by creating audit items for different audit instances, authenticating as each brand owner, and verifying each user can only access their own audit items. Delivers value by ensuring audit item data privacy.

**Acceptance Scenarios**:

1. **Given** I am authenticated and have an audit instance, **When** I list audit items for my audit instance, **Then** I see only items belonging to my audit instance
2. **Given** User B has audit items for their audit instance, **When** I authenticate as User A and attempt to access User B's audit item by ID, **Then** I receive an access denied error
3. **Given** I am authenticated, **When** I update an audit item for my audit instance, **Then** only my audit item is modified and changes are persisted
4. **Given** I am authenticated, **When** I view audit item details, **Then** I see complete information for items belonging to my audit instances only
5. **Given** I am authenticated with role "admin", **When** I retrieve audit items for an audit instance belonging to any brand, **Then** I can access those items successfully

---

### User Story 6 - Admin Role-Based Access Control (Priority: P2)

As a system administrator, I need to access admin-only endpoints (such as criteria and rules management) so that I can manage system-wide configuration without allowing regular brand administrators to modify these settings.

**Why this priority**: Admin-only endpoints protect system configuration from unauthorized modification. This enables separation between brand administrators (who manage their own data) and system administrators (who manage global settings).

**Independent Test**: Can be fully tested by authenticating as admin user (role: "admin" in public_metadata) and non-admin user, verifying admin can access admin endpoints while non-admin receives 403 Forbidden. Delivers value by enabling secure system administration.

**Acceptance Scenarios**:

1. **Given** I am authenticated with role "admin" in Clerk public_metadata, **When** I access an admin-only endpoint, **Then** I can successfully perform the operation
2. **Given** I am authenticated without admin role, **When** I attempt to access an admin-only endpoint, **Then** I receive a 403 Forbidden error
3. **Given** I am authenticated with role "admin", **When** I retrieve my profile information, **Then** I see my role included in the response
4. **Given** I am authenticated without a role in metadata, **When** I access an admin-only endpoint, **Then** I receive a 403 Forbidden error

---

### Edge Cases

- What happens when a Clerk user is deleted but their profile still exists in the system? (User profile is marked as inactive/disabled, authentication is prevented, but data is preserved)
- How does the system handle concurrent profile creation requests for the same Clerk user? (Database unique constraint on Clerk user ID ensures idempotent creation - insert or retrieve existing)
- What happens when a user tries to access a brand that was soft-deleted? (Users cannot access soft-deleted brands - return not found or access denied)
- How does the system handle token refresh during an active session?
- What happens when a user's Clerk account is suspended or disabled? (Authentication will fail, access denied)
- What happens when Clerk authentication service is temporarily unavailable? (All authenticated requests are rejected with service unavailable error)
- How does the system handle requests with missing or malformed authentication headers?
- What happens when a user tries to create a second brand profile (should be prevented)?
- How does the system handle audit instances created before user authentication was implemented? (Orphaned brands and audit instances remain inaccessible until manually associated with a user profile)
- What happens when a brand is deleted but audit instances still reference it?
- How does the system handle very large numbers of audit instances per brand (performance considerations)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST authenticate API requests using Clerk authentication tokens provided in request headers
- **FR-002**: System MUST validate Clerk tokens on every authenticated request and reject invalid or expired tokens
- **FR-022**: System MUST reject all authenticated requests with appropriate error when Clerk authentication service is unavailable or returns errors
- **FR-003**: System MUST automatically create a user profile when a valid Clerk token is provided for a user that doesn't exist in the system
- **FR-023**: System MUST use database unique constraint on Clerk user ID to prevent duplicate profiles and implement idempotent profile creation (insert or retrieve existing)
- **FR-004**: System MUST associate each user profile with a Clerk user ID for identity mapping
- **FR-005**: System MUST associate each brand with exactly one user profile (one brand per user)
- **FR-006**: System MUST enforce that users can only access brands they own
- **FR-007**: System MUST enforce that users can only create one brand profile
- **FR-008**: System MUST enforce that users can only access products belonging to their brands
- **FR-009**: System MUST enforce that users can only access supply chain nodes belonging to their brands
- **FR-010**: System MUST enforce that users can only access audit instances for their brands
- **FR-011**: System MUST enforce that users can only access audit items belonging to their audit instances
- **FR-012**: System MUST return appropriate access denied errors when users attempt to access data they don't own
- **FR-013**: System MUST include user context in all data access operations to enforce ownership
- **FR-014**: System MUST support querying brands, products, supply chain nodes, audit instances, and audit items filtered by authenticated user
- **FR-025**: System MUST exclude soft-deleted brands from user queries and return not found or access denied when users attempt to access soft-deleted brands
- **FR-015**: System MUST store user profile information including Clerk user ID and creation timestamp
- **FR-024**: System MUST mark user profiles as inactive/disabled when corresponding Clerk user account is deleted and prevent authentication for inactive profiles
- **FR-016**: System MUST validate brand ownership before allowing any brand-related operations (create, read, update, delete)
- **FR-017**: System MUST validate audit instance ownership before allowing any audit instance operations
- **FR-018**: System MUST validate audit item ownership (via audit instance ownership) before allowing any audit item operations
- **FR-019**: System MUST handle authentication errors gracefully with clear error messages
- **FR-020**: System MUST support unauthenticated access to public endpoints (health checks, public documentation)
- **FR-021**: System MUST prevent access to brands that are not associated with any user profile (orphaned brands) until they are manually associated with a user
- **FR-026**: System MUST extract user role from Clerk token public_metadata during authentication
- **FR-027**: System MUST store user role in user profile context for access control decisions
- **FR-028**: System MUST provide admin-only dependency that restricts endpoints to users with role "admin" in public_metadata
- **FR-029**: System MUST return 403 Forbidden error when non-admin users attempt to access admin-only endpoints
- **FR-030**: System MUST allow users with role "admin" to list and retrieve audit instances across all brands
- **FR-031**: System MUST allow users with role "admin" to list and retrieve audit items for audit instances across all brands

### Key Entities *(include if feature involves data)*

- **User Profile**: Represents a user authenticated via Clerk. Key attributes include: unique identifier (UUID), Clerk user ID (string, unique constraint), role (string, extracted from Clerk public_metadata), creation timestamp, last access timestamp, active status (boolean). Relationships: owns exactly one Brand, indirectly owns Products, SupplyChainNodes, AuditInstances, and AuditItems through brand ownership. The Clerk user ID must be unique across all profiles to prevent duplicates and enable idempotent creation. Profiles can be marked as inactive when the corresponding Clerk user account is deleted, preventing authentication while preserving data. Role is extracted from Clerk token public_metadata during authentication and stored in user context for access control decisions.

- **Brand Ownership**: Relationship between User Profile and Brand. Each Brand is owned by exactly one User Profile, and each User Profile can own at most one Brand. This relationship enables data access control for all brand-related resources.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Authentication requests complete successfully within 200 milliseconds, 95% of the time
- **SC-002**: User profile creation completes successfully within 500 milliseconds, 95% of the time
- **SC-003**: Data access requests return results filtered by user ownership within 300 milliseconds, 95% of the time
- **SC-004**: Access denied errors are returned within 100 milliseconds when users attempt unauthorized access, 100% of the time
- **SC-005**: Invalid authentication tokens are rejected with appropriate errors, 100% of the time
- **SC-006**: Users can successfully access all their own brand data (brands, products, supply chain nodes, audit instances, audit items), 100% of the time when authenticated
- **SC-007**: Users cannot access other users' brand data, 100% of the time (zero unauthorized access incidents)
- **SC-008**: System handles 50 concurrent authenticated requests per user without errors or performance degradation
- **SC-009**: Profile creation is idempotent - multiple requests for the same Clerk user result in a single profile, 100% of the time
- **SC-010**: All authenticated endpoints properly validate user identity and enforce access control, 100% of the time
- **SC-011**: Admin-only endpoints reject non-admin users with 403 Forbidden, 100% of the time
- **SC-012**: User role extraction from Clerk public_metadata completes within 50 milliseconds, 95% of the time

## Assumptions

- Clerk authentication service is available and accessible from the API server; when unavailable, all authenticated requests are rejected
- Clerk API credentials (API keys, webhook secrets) will be provided via environment variables
- Frontend application will provide Clerk authentication tokens in request headers (Authorization header with Bearer token format)
- Clerk user IDs are stable and unique identifiers that can be used for user profile mapping
- One user represents one brand administrator (one-to-one relationship between users and brands)
- Existing brands and audit instances created before authentication implementation will remain inaccessible (orphaned) until manually associated with a user profile via admin tool or migration script
- Public endpoints (health checks, API documentation) remain accessible without authentication
- Clerk token validation will be performed on every authenticated request (no token caching)
- User profiles are created automatically on first authenticated request; no explicit profile creation endpoint is required
- Brand creation automatically associates the brand with the authenticated user's profile
- All brand-related operations (products, supply chain nodes, audit instances, audit items) inherit access control from brand ownership
- Clerk public_metadata contains user role information (e.g., { role: "admin" }) accessible in JWT token claims
- User role is extracted from Clerk token public_metadata during authentication and stored in user context
- Admin-only endpoints are protected by role-based dependency that checks for role "admin" in public_metadata
- Multiple roles per user or complex permission levels are out of scope (single role per user supported)
- Clerk webhook integration for user lifecycle events (user created, deleted, updated) is out of scope for this feature and can be added in future features

## Dependencies

- Clerk authentication service must be configured and accessible
- Existing brand and audit data models must support user association
- Database schema must support user profile storage and brand-user relationships
- Frontend application must be configured to send Clerk authentication tokens with API requests

## Out of Scope

- Multiple roles per user or complex permission hierarchies (single role per user supported)
- Clerk webhook integration for user lifecycle management
- Multi-brand support per user (users owning multiple brands)
- User profile management endpoints (update profile, delete profile)
- User-to-user data sharing or collaboration features
- Audit trail for user actions (who accessed what data)
- Session management or token refresh handling (handled by Clerk)
- User registration or account management (handled by Clerk)

