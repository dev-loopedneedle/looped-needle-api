# Feature Specification: Brands Dashboard Endpoint

**Feature Branch**: `005-brands-dashboard`  
**Created**: 2026-01-26  
**Status**: Draft  
**Input**: User description: "I need a /dashboard endpoint available in brands app that will return data for screen below (skip certifications stuff for now)"

## Clarifications

### Session 2026-01-26

- Q: How should the endpoint be accessed - should it accept a brand_id parameter, or should it automatically use the authenticated user's brand? → A: Auto-scope to current user's brand (endpoint path: `/api/v1/brands/dashboard`)
- Q: What specific score value should be averaged across completed audits? → A: Remove average score requirement entirely
- Q: What are the complete score ranges for all rating labels? → A: Return numeric scores only (0-100); rating labels will be determined by frontend
- Q: How should "latest completed audit" be determined - by completion timestamp or creation date? → A: Latest by completion timestamp (when workflow status became PROCESSING_COMPLETE)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View Dashboard Summary (Priority: P1)

A brand user wants to quickly understand their audit performance at a glance by viewing high-level summary metrics on the dashboard.

**Why this priority**: This provides immediate value by showing key performance indicators (total audits, completion rate) that help users understand their overall audit status without navigating to individual audit details.

**Independent Test**: Can be fully tested by calling the dashboard endpoint and verifying that summary metrics (total audits count, completed audits count) are returned correctly. This delivers immediate visibility into audit performance.

**Acceptance Scenarios**:

1. **Given** a brand has multiple audits with various statuses, **When** the user requests the dashboard, **Then** the system returns accurate counts for total audits and completed audits
2. **Given** a brand has no audits, **When** the user requests the dashboard, **Then** the system returns zero values for all summary metrics

---

### User Story 2 - View Latest Audit Scores Breakdown (Priority: P1)

A brand user wants to see detailed category scores for their most recently completed audit to understand performance across different sustainability dimensions.

**Why this priority**: This provides actionable insights by breaking down the overall audit performance into specific categories (Environmental, Social, Circularity, Transparency), helping users identify areas of strength and improvement.

**Independent Test**: Can be fully tested by verifying that the latest completed audit's category scores are returned with proper breakdown (Environmental, Social, Circularity, Transparency numeric scores). This delivers detailed performance analysis for the most recent audit.

**Acceptance Scenarios**:

1. **Given** a brand has at least one completed audit with category scores, **When** the user requests the dashboard, **Then** the system returns the latest completed audit's detailed category breakdown with numeric scores (0-100) for each category
2. **Given** a brand has completed audits but no category scores available, **When** the user requests the dashboard, **Then** the system returns the latest audit information without category scores or indicates scores are unavailable
3. **Given** a brand has no completed audits, **When** the user requests the dashboard, **Then** the system indicates that no latest audit scores are available

---

### User Story 3 - View Recent Audits List (Priority: P2)

A brand user wants to see a list of their recent audits with key information (product name, scores, status, date) to quickly navigate to specific audits.

**Why this priority**: This enables efficient navigation and provides context about recent audit activity, though it's secondary to the summary and latest scores which provide immediate insights.

**Independent Test**: Can be fully tested by verifying that a paginated list of recent audits is returned with essential information (product identifier, scores by category, status, date). This delivers quick access to recent audit history.

**Acceptance Scenarios**:

1. **Given** a brand has multiple audits, **When** the user requests the dashboard, **Then** the system returns a list of recent audits ordered by creation date (newest first) with product information, scores, status, and dates
2. **Given** a brand has audits in different statuses (completed, processing), **When** the user requests the dashboard, **Then** the system returns audits with appropriate status indicators and shows scores only for completed audits
3. **Given** a brand has more audits than the default page size, **When** the user requests the dashboard, **Then** the system returns the most recent audits up to the page limit

---

### Edge Cases

- What happens when a brand has no audits at all?
- How does the system handle audits that are in processing state (scores not yet available)?
- What happens when an audit has partial category scores (some categories missing)?
- How does the system handle audits with null or invalid score values?
- What happens when multiple audits have the same completion timestamp (tiebreaker: use most recent workflow updated_at, then audit creation date)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a dashboard endpoint at `/api/v1/brands/dashboard` that automatically scopes to the authenticated user's brand and returns aggregated audit data
- **FR-002**: System MUST return summary metrics including total audits count and completed audits count
- **FR-003**: System MUST return the latest completed audit's detailed category scores (Environmental, Social, Circularity, Transparency) as numeric values (0-100), where "latest" is determined by completion timestamp (when workflow status became PROCESSING_COMPLETE)
- **FR-004**: System MUST return a list of recent audits with product information, category scores (when available), status, and creation date
- **FR-005**: System MUST map audit workflow statuses to user-friendly display statuses (e.g., PROCESSING_COMPLETE → "Completed", PROCESSING → "Processing")
- **FR-006**: System MUST only include audits that belong to the authenticated user's brand
- **FR-007**: System MUST exclude certification-related data from the dashboard response (as specified by user requirement)
- **FR-008**: System MUST handle cases where no audits exist by returning appropriate zero/null values
- **FR-009**: System MUST return category scores in a structured format with category name and numeric score value (0-100)
- **FR-011**: System MUST order recent audits by creation date (newest first)
- **FR-012**: System MUST limit the number of recent audits returned (default page size)

### Key Entities *(include if feature involves data)*

- **Brand**: Represents a brand entity that owns audits, identified by brand_id and associated with a user
- **Audit**: Represents an audit record with status (DRAFT, PUBLISHED), audit_data containing product information, and timestamps
- **AuditWorkflow**: Represents an audit workflow instance with status (GENERATED, PROCESSING, PROCESSING_COMPLETE, PROCESSING_FAILED), category_scores dictionary, and relationship to an audit
- **Category Scores**: Dictionary structure containing scores for ENVIRONMENTAL, SOCIAL, CIRCULARITY, and TRANSPARENCY categories, each with integer values (0-100)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can retrieve dashboard data in under 500 milliseconds for brands with up to 100 audits
- **SC-002**: Dashboard endpoint returns accurate summary metrics (total audits, completed audits) with 100% accuracy for all audit states
- **SC-003**: Dashboard endpoint successfully returns latest audit scores breakdown for 95% of brands that have at least one completed audit
- **SC-004**: Dashboard endpoint returns recent audits list with all required fields (product info, scores, status, date) for 100% of requests
- **SC-005**: Dashboard endpoint handles edge cases (no audits, partial scores, processing audits) without errors, returning appropriate null/zero values
- **SC-006**: Users can access their brand's dashboard data without unauthorized access to other brands' data (100% access control accuracy)

## Assumptions

- The dashboard endpoint automatically scopes to the authenticated user's brand (no brand_id parameter required)
- "Completed" status maps to audit workflows with PROCESSING_COMPLETE status
- "Processing" status maps to audit workflows with PROCESSING status
- "Latest completed audit" is determined by the most recent completion timestamp (when workflow status became PROCESSING_COMPLETE)
- Category scores are stored in the AuditWorkflow.category_scores field as a dictionary with keys: ENVIRONMENTAL, SOCIAL, CIRCULARITY, TRANSPARENCY
- Product information (product name, target market) is stored in Audit.audit_data.productInfo
- Rating labels and descriptions are handled by the frontend; backend returns only numeric scores (0-100)
- Recent audits list defaults to showing the 5 most recent audits
- The endpoint follows RESTful conventions and returns JSON data
- Authentication and authorization are handled by existing middleware (user must be authenticated and have access to the brand)

## Dependencies

- Existing Brand model and service layer
- Existing Audit model and service layer  
- Existing AuditWorkflow model and service layer
- Existing authentication/authorization system to ensure users can only access their own brand's data
- Database queries to aggregate audit data efficiently

## Out of Scope

- Certification-related data (explicitly excluded per user requirement)
- Real-time updates or WebSocket connections for live dashboard updates
- Dashboard customization or user preferences
- Export functionality for dashboard data
- Historical trends or time-series analysis
- Comparison with other brands or industry benchmarks
- Dashboard caching strategy (implementation detail)
