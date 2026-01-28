# Quick Start Guide: Brands Dashboard Endpoint

**Feature**: 005-brands-dashboard  
**Date**: 2026-01-26

## Overview

This guide provides step-by-step instructions for implementing and testing the brands dashboard endpoint that returns aggregated audit data.

## Prerequisites

- Existing FastAPI backend setup (from 001-fastapi-backend)
- PostgreSQL database with `brands`, `audits`, and `audit_workflows` tables
- Authentication system configured (Clerk)
- Test data: at least one brand with associated audits and workflows

## Implementation Steps

### 1. Add Dashboard Schemas

Add Pydantic models to `src/brands/schemas.py`:

```python
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import Literal

class CategoryScore(BaseModel):
    """Category score schema."""
    category: Literal["ENVIRONMENTAL", "SOCIAL", "CIRCULARITY", "TRANSPARENCY"]
    score: int = Field(..., ge=0, le=100)

class DashboardSummary(BaseModel):
    """Dashboard summary metrics."""
    totalAudits: int = Field(..., ge=0)
    completedAudits: int = Field(..., ge=0)

class LatestAuditScores(BaseModel):
    """Latest completed audit scores."""
    auditId: str
    productName: str | None = None
    targetMarket: str | None = None
    completedAt: datetime
    categoryScores: list[CategoryScore]

class RecentAudit(BaseModel):
    """Recent audit information."""
    auditId: str
    productName: str | None = None
    targetMarket: str | None = None
    status: Literal["Completed", "Processing", "Generated", "Failed"]
    categoryScores: list[CategoryScore] | None = None
    createdAt: datetime

class DashboardResponse(BaseModel):
    """Dashboard response schema."""
    summary: DashboardSummary
    latestAuditScores: LatestAuditScores | None
    recentAudits: list[RecentAudit]
```

### 2. Add Dashboard Service Method

Add method to `src/brands/service.py`:

```python
@staticmethod
async def get_dashboard_data(
    db: AsyncSession,
    current_user: UserContext,
) -> dict:
    """
    Get dashboard data for the authenticated user's brand.
    
    Returns aggregated audit data including:
    - Summary metrics (total audits, completed audits)
    - Latest completed audit scores
    - Recent audits list (up to 5)
    """
    # Get user's brand
    brand = await BrandService.get_brand_by_user(db, current_user.profile.id)
    if not brand:
        raise BrandNotFoundError("Brand not found for user")
    
    # SQL query with CTEs for aggregation
    # (See implementation details in service.py)
    # ...
```

### 3. Add Dashboard Endpoint

Add route to `src/brands/router.py`:

```python
@router.get(
    "/brands/dashboard",
    response_model=DashboardResponse,
    summary="Get brand dashboard",
    description="Retrieve aggregated dashboard data for the authenticated user's brand",
    tags=["brands"],
)
async def get_dashboard(
    request_id: str | None = Depends(get_request_id),
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DashboardResponse:
    """Get dashboard data for current user's brand."""
    logger.info("Getting dashboard data", extra={"request_id": request_id})
    dashboard_data = await BrandService.get_dashboard_data(db, current_user)
    return DashboardResponse.model_validate(dashboard_data)
```

### 4. SQL Query Implementation

The service method should use SQL-first approach with PostgreSQL JSON functions:

```python
from sqlalchemy import text

query = text("""
WITH brand_audits AS (
    SELECT a.id, a.brand_id, a.audit_data, a.created_at,
           aw.id as workflow_id, aw.status, aw.category_scores, aw.updated_at
    FROM audits a
    LEFT JOIN audit_workflows aw ON a.id = aw.audit_id
    WHERE a.brand_id = :brand_id
),
summary_metrics AS (
    SELECT 
        COUNT(DISTINCT id) as total_audits,
        COUNT(DISTINCT CASE WHEN status = 'PROCESSING_COMPLETE' THEN id END) as completed_audits
    FROM brand_audits
),
latest_completed AS (
    SELECT *
    FROM brand_audits
    WHERE status = 'PROCESSING_COMPLETE'
    ORDER BY updated_at DESC, created_at DESC
    LIMIT 1
),
recent_audits AS (
    SELECT *
    FROM brand_audits
    ORDER BY created_at DESC
    LIMIT 5
)
SELECT 
    (SELECT row_to_json(sm.*) FROM summary_metrics sm) as summary,
    (SELECT row_to_json(lc.*) FROM latest_completed lc) as latest,
    (SELECT json_agg(ra.*) FROM recent_audits ra) as recent
""")
```

## Testing

### 1. Unit Tests

Create `tests/brands/test_service.py`:

```python
import pytest
from uuid import uuid4
from src.brands.service import BrandService

@pytest.mark.asyncio
async def test_get_dashboard_data_with_audits(db_session, test_user, test_brand):
    """Test dashboard data retrieval with existing audits."""
    # Create test audits and workflows
    # ...
    
    dashboard = await BrandService.get_dashboard_data(db_session, test_user)
    
    assert dashboard["summary"]["totalAudits"] > 0
    assert dashboard["summary"]["completedAudits"] >= 0
    assert isinstance(dashboard["recentAudits"], list)
```

### 2. Integration Tests

Create `tests/brands/test_router.py`:

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_dashboard_endpoint(client: AsyncClient, auth_headers):
    """Test dashboard endpoint."""
    response = await client.get(
        "/api/v1/brands/dashboard",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "latestAuditScores" in data
    assert "recentAudits" in data
```

### 3. Manual Testing

```bash
# Start the server
uvicorn src.main:app --reload

# Get authentication token (from Clerk or test token)
TOKEN="your-jwt-token"

# Test dashboard endpoint
curl -X GET "http://localhost:8000/api/v1/brands/dashboard" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"

# Expected response:
# {
#   "summary": {
#     "totalAudits": 5,
#     "completedAudits": 3
#   },
#   "latestAuditScores": {
#     "auditId": "...",
#     "productName": "Organic Cotton Tee",
#     "targetMarket": "EU",
#     "completedAt": "2026-01-20T...",
#     "categoryScores": [
#       {"category": "ENVIRONMENTAL", "score": 82},
#       {"category": "SOCIAL", "score": 78},
#       {"category": "CIRCULARITY", "score": 65},
#       {"category": "TRANSPARENCY", "score": 88}
#     ]
#   },
#   "recentAudits": [...]
# }
```

## Performance Testing

```bash
# Test with multiple audits
# Create 100 audits for a brand
python scripts/create_test_audits.py --count 100 --brand-id <brand-id>

# Measure response time
time curl -X GET "http://localhost:8000/api/v1/brands/dashboard" \
  -H "Authorization: Bearer $TOKEN"

# Should complete in <500ms per SC-001
```

## Edge Cases to Test

1. **No audits**: Brand with no audits should return zeros and nulls
2. **No completed audits**: Should return `latestAuditScores: null`
3. **Partial category scores**: Should only include available categories
4. **Multiple workflows**: Should select most recent completed workflow
5. **Unauthorized access**: Should return 401/403

## Verification Checklist

- [ ] Dashboard endpoint returns 200 for authenticated user
- [ ] Summary metrics are accurate
- [ ] Latest audit scores are correct (most recent completion)
- [ ] Recent audits are ordered by creation date (newest first)
- [ ] Status mapping works correctly (PROCESSING_COMPLETE → "Completed")
- [ ] Category scores are structured correctly
- [ ] Edge cases handled (no audits, no completed audits, partial scores)
- [ ] Performance meets <500ms target
- [ ] Tests pass (unit + integration)
- [ ] OpenAPI documentation is accurate

## Next Steps

After implementation:
1. Run full test suite
2. Verify OpenAPI docs at `/docs`
3. Deploy to staging environment
4. Monitor performance metrics
5. Gather user feedback
