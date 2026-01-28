# Data Model: Brands Dashboard

**Feature**: 005-brands-dashboard  
**Date**: 2026-01-26

## Overview

The dashboard endpoint aggregates data from existing entities (`Brand`, `Audit`, `AuditWorkflow`) without requiring new database tables or schema changes. This document describes the data structures used in the dashboard response.

## Entities Used

### Brand
- **Table**: `brands`
- **Purpose**: Identifies the brand for which dashboard data is aggregated
- **Key Fields Used**:
  - `id` (UUID): Brand identifier
  - `user_id` (UUID): Owner user identifier (for access control)

### Audit
- **Table**: `audits`
- **Purpose**: Represents audit records owned by a brand
- **Key Fields Used**:
  - `id` (UUID): Audit identifier
  - `brand_id` (UUID): Foreign key to brands table
  - `status` (str): Audit status (DRAFT, PUBLISHED)
  - `audit_data` (JSONB): Product information including `productInfo.productName` and `productInfo.targetMarket`
  - `created_at` (datetime): Creation timestamp (used for ordering recent audits)

### AuditWorkflow
- **Table**: `audit_workflows`
- **Purpose**: Represents workflow instances for audits with scores and status
- **Key Fields Used**:
  - `id` (UUID): Workflow identifier
  - `audit_id` (UUID): Foreign key to audits table
  - `status` (str): Workflow status (GENERATED, PROCESSING, PROCESSING_COMPLETE, PROCESSING_FAILED)
  - `category_scores` (JSONB): Dictionary with category scores:
    - `ENVIRONMENTAL` (int, 0-100)
    - `SOCIAL` (int, 0-100)
    - `CIRCULARITY` (int, 0-100)
    - `TRANSPARENCY` (int, 0-100)
  - `updated_at` (datetime): Last update timestamp (used to determine latest completed audit)

## Response Data Structures

### DashboardResponse (Pydantic Schema)

```python
{
  "summary": {
    "totalAudits": int,
    "completedAudits": int
  },
  "latestAuditScores": {
    "auditId": str (UUID),
    "productName": str | None,
    "targetMarket": str | None,
    "completedAt": datetime,
    "categoryScores": [
      {
        "category": str,  # "ENVIRONMENTAL" | "SOCIAL" | "CIRCULARITY" | "TRANSPARENCY"
        "score": int  # 0-100
      }
    ]
  } | None,
  "recentAudits": [
    {
      "auditId": str (UUID),
      "productName": str | None,
      "targetMarket": str | None,
      "status": str,  # "Completed" | "Processing" | "Generated" | "Failed"
      "categoryScores": [
        {
          "category": str,
          "score": int
        }
      ] | None,  # None if status is not "Completed"
      "createdAt": datetime
    }
  ]
}
```

## Relationships

```
Brand (1) ──< (many) Audit (1) ──< (many) AuditWorkflow
```

- One Brand has many Audits
- One Audit can have many AuditWorkflows (though typically one active workflow)
- Dashboard aggregates data across this relationship tree

## Data Aggregation Rules

### Summary Metrics
- **totalAudits**: Count of all audits for the brand (regardless of status)
- **completedAudits**: Count of audits that have at least one workflow with `status = 'PROCESSING_COMPLETE'`

### Latest Audit Selection
- Select audit with workflow where `status = 'PROCESSING_COMPLETE'`
- Order by `audit_workflows.updated_at DESC` (most recent completion)
- Tiebreaker: `audits.created_at DESC`
- Return `None` if no completed audits exist

### Recent Audits List
- Select up to 5 most recent audits (ordered by `audits.created_at DESC`)
- Include workflow status (mapped to display status)
- Include category scores only if workflow status is `'PROCESSING_COMPLETE'`
- If no workflow exists for an audit, status is `None` or omitted

### Category Scores Extraction
- Extract from `audit_workflows.category_scores` JSONB field
- Convert dictionary keys (ENVIRONMENTAL, SOCIAL, CIRCULARITY, TRANSPARENCY) to array of objects
- Each object contains `category` (string) and `score` (integer 0-100)
- Handle missing categories gracefully (omit from array)

### Status Mapping
- `PROCESSING_COMPLETE` → `"Completed"`
- `PROCESSING` → `"Processing"`
- `GENERATED` → `"Generated"`
- `PROCESSING_FAILED` → `"Failed"`
- No workflow → `None` or omitted

## Edge Cases

### No Audits
- `summary.totalAudits = 0`
- `summary.completedAudits = 0`
- `latestAuditScores = None`
- `recentAudits = []`

### No Completed Audits
- `summary.completedAudits = 0`
- `latestAuditScores = None`
- `recentAudits` includes audits but without category scores

### Partial Category Scores
- Include only categories that exist in `category_scores` dictionary
- Missing categories are omitted (not included as null/0)

### Multiple Workflows per Audit
- For latest audit: Select workflow with `PROCESSING_COMPLETE` status, most recent `updated_at`
- For recent audits: Select most recent workflow by `updated_at`

## Validation Rules

- All UUIDs must be valid UUID format
- Category scores must be integers between 0-100
- Category names must be one of: ENVIRONMENTAL, SOCIAL, CIRCULARITY, TRANSPARENCY
- Timestamps must be valid ISO 8601 datetime format
- Product name and target market can be null/None

## Indexes Used

- `audits.brand_id` (indexed) - for filtering audits by brand
- `audits.created_at` (indexed) - for ordering recent audits
- `audit_workflows.audit_id` (indexed) - for joining workflows to audits
- `audit_workflows.status` (indexed) - for filtering completed workflows
- `audit_workflows.updated_at` (indexed) - for ordering by completion time
