# Research: Brands Dashboard Endpoint

**Feature**: 005-brands-dashboard  
**Date**: 2026-01-26

## Overview

Research findings for implementing the brands dashboard endpoint that aggregates audit data for display.

## Technical Decisions

### SQL-First Aggregation Approach

**Decision**: Use PostgreSQL SQL queries with JSON functions for all data aggregation and response building.

**Rationale**: 
- Follows Constitution Principle V (SQL-First, Pydantic-Second)
- Database is optimized for aggregations and joins
- Reduces application memory usage and improves performance
- PostgreSQL JSON functions (`json_build_object`, `json_agg`) enable building nested responses directly in SQL

**Alternatives considered**:
- Python-side aggregation: Rejected because it requires loading all data into memory and performing joins/aggregations in Python, which is slower and uses more resources
- Separate queries with Python composition: Rejected because multiple round trips to database are less efficient than a single optimized query

### Latest Audit Selection Strategy

**Decision**: Use `updated_at` timestamp from `audit_workflows` table where `status = 'PROCESSING_COMPLETE'` to determine latest completed audit, with tiebreaker using `updated_at` DESC, then `created_at` DESC.

**Rationale**:
- `updated_at` reflects when workflow status changed to PROCESSING_COMPLETE
- Matches user expectation of "most recently completed"
- Efficient to query with indexed timestamp columns

**Alternatives considered**:
- Using `created_at`: Rejected because creation time doesn't reflect completion time
- Using separate completion timestamp: Not available in current schema, would require migration

### Status Mapping

**Decision**: Map internal workflow statuses to user-friendly display statuses:
- `PROCESSING_COMPLETE` → `"Completed"`
- `PROCESSING` → `"Processing"`
- `GENERATED` → `"Generated"` (if needed)
- `PROCESSING_FAILED` → `"Failed"` (if needed)

**Rationale**:
- Provides clear, user-friendly status labels
- Mapping done in SQL CASE statement for efficiency
- Consistent with frontend expectations

**Alternatives considered**:
- Returning raw status values: Rejected because internal statuses are too technical for end users

### Category Scores Structure

**Decision**: Return category scores as structured objects with `category` (name) and `score` (0-100 integer) fields. Frontend handles rating labels and descriptions.

**Rationale**:
- Backend focuses on data, frontend handles presentation
- Reduces backend complexity
- Allows frontend flexibility in rating system

**Alternatives considered**:
- Including rating labels in backend: Rejected per clarification - frontend will determine ratings
- Including category descriptions: Rejected per clarification - frontend handles descriptions

### Query Optimization Strategy

**Decision**: Use a single optimized SQL query with CTEs (Common Table Expressions) to:
1. Get brand's audits with workflow data
2. Calculate summary metrics
3. Find latest completed audit
4. Get recent audits list

**Rationale**:
- Single query reduces database round trips
- CTEs make complex query readable and maintainable
- PostgreSQL optimizer handles CTE efficiently
- Meets performance goal of <500ms for 100 audits

**Alternatives considered**:
- Multiple separate queries: Rejected because multiple round trips add latency
- Application-side joins: Rejected because violates SQL-First principle

## Database Query Patterns

### Aggregation Pattern
```sql
-- Count audits by status
SELECT 
  COUNT(*) FILTER (WHERE aw.status = 'PROCESSING_COMPLETE') as completed_count,
  COUNT(*) as total_count
FROM audits a
JOIN audit_workflows aw ON a.id = aw.audit_id
WHERE a.brand_id = :brand_id
```

### Latest Audit Pattern
```sql
-- Get latest completed audit with category scores
SELECT a.*, aw.category_scores, aw.updated_at as completed_at
FROM audits a
JOIN audit_workflows aw ON a.id = aw.audit_id
WHERE a.brand_id = :brand_id
  AND aw.status = 'PROCESSING_COMPLETE'
ORDER BY aw.updated_at DESC, a.created_at DESC
LIMIT 1
```

### Recent Audits Pattern
```sql
-- Get recent audits with workflow status
SELECT a.*, aw.status, aw.category_scores, aw.updated_at
FROM audits a
LEFT JOIN audit_workflows aw ON a.id = aw.audit_id
WHERE a.brand_id = :brand_id
ORDER BY a.created_at DESC
LIMIT 5
```

## Performance Considerations

- All queries use indexed columns (`brand_id`, `status`, `created_at`, `updated_at`)
- Single query approach minimizes database round trips
- JSON building in SQL reduces Python-side processing
- Query complexity is O(n) where n is number of audits (acceptable for <100 audits)

## Security Considerations

- Endpoint automatically scopes to authenticated user's brand (no brand_id parameter)
- Uses existing `get_current_user` dependency for authentication
- Brand access control enforced via `BrandService.get_brand_by_user()` pattern
- No new security vulnerabilities introduced

## Integration Points

- Uses existing `Brand`, `Audit`, and `AuditWorkflow` models
- Leverages existing `get_db` and `get_current_user` dependencies
- Follows existing router/service pattern in brands domain
- No changes to existing models or database schema required
