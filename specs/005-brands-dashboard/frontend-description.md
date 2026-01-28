# Frontend Integration Guide: Brands Dashboard Endpoint

**Endpoint**: `GET /api/v1/brands/dashboard`  
**Authentication**: Required (Bearer token)  
**Content-Type**: `application/json`

## Overview

The dashboard endpoint provides aggregated audit data for the authenticated user's brand. It returns summary metrics, the latest completed audit's category scores (including overall score and certification), and a list of recent audits - all in a single request.

**Key Features:**
- Summary metrics (total audits, completed audits count)
- Latest completed audit with full scores and certification level
- Recent audits list (up to 5 most recent)
- All data scoped automatically to the authenticated user's brand

## Endpoint Details

**URL**: `/api/v1/brands/dashboard`  
**Method**: `GET`  
**Authentication**: Bearer token (JWT from Clerk)  
**Response Time**: <500ms (target)

## Request

### Headers

```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

### Query Parameters

None - the endpoint automatically scopes to the authenticated user's brand.

## Response Structure

### Success Response (200 OK)

```json
{
  "summary": {
    "totalAudits": 5,
    "completedAudits": 3
  },
  "latestAuditScores": {
    "auditId": "550e8400-e29b-41d4-a716-446655440000",
    "workflowId": "660e8400-e29b-41d4-a716-446655440001",
    "productName": "Organic Cotton Essential Tee",
    "targetMarket": "EU",
    "completedAt": "2026-01-20T10:30:00Z",
    "categoryScores": [
      {
        "category": "ENVIRONMENTAL",
        "score": 82
      },
      {
        "category": "SOCIAL",
        "score": 78
      },
      {
        "category": "CIRCULARITY",
        "score": 65
      },
      {
        "category": "TRANSPARENCY",
        "score": 88
      }
    ],
    "overallScore": 78,
    "certification": "Silver"
  },
  "recentAuditWorkflows": [
    {
      "workflowId": "770e8400-e29b-41d4-a716-446655440003",
      "auditId": "550e8400-e29b-41d4-a716-446655440000",
      "productName": "Organic Cotton Essential Tee",
      "targetMarket": "EU",
      "status": "Completed",
      "categoryScores": [
        {
          "category": "ENVIRONMENTAL",
          "score": 82
        },
        {
          "category": "SOCIAL",
          "score": 78
        },
        {
          "category": "CIRCULARITY",
          "score": 65
        },
        {
          "category": "TRANSPARENCY",
          "score": 88
        }
      ],
      "overallScore": 78,
      "certification": "Silver",
      "createdAt": "2026-01-20T08:00:00Z"
    },
    {
      "workflowId": "880e8400-e29b-41d4-a716-446655440004",
      "auditId": "660e8400-e29b-41d4-a716-446655440001",
      "productName": "Recycled Denim Jacket",
      "targetMarket": "US",
      "status": "Completed",
      "categoryScores": [
        {
          "category": "ENVIRONMENTAL",
          "score": 91
        },
        {
          "category": "SOCIAL",
          "score": 85
        },
        {
          "category": "CIRCULARITY",
          "score": 88
        },
        {
          "category": "TRANSPARENCY",
          "score": 92
        }
      ],
      "overallScore": 89,
      "certification": "Gold",
      "createdAt": "2026-02-05T09:15:00Z"
    },
    {
      "workflowId": "990e8400-e29b-41d4-a716-446655440005",
      "auditId": "770e8400-e29b-41d4-a716-446655440002",
      "productName": "Linen Summer Dress",
      "targetMarket": "EU",
      "status": "Processing",
      "categoryScores": null,
      "createdAt": "2026-03-10T11:20:00Z"
    }
  ]
}
```

### Error Responses

#### 401 Unauthorized
```json
{
  "error": "unauthorized",
  "message": "Authentication required"
}
```

#### 404 Not Found
```json
{
  "error": "brand_not_found",
  "message": "Brand not found for user"
}
```

#### 500 Internal Server Error
```json
{
  "error": "internal_error",
  "message": "An error occurred while processing your request"
}
```

## Response Fields

### Summary Object

| Field | Type | Description |
|-------|------|-------------|
| `totalAudits` | `integer` | Total number of audits for the brand (always ≥ 0) |
| `completedAudits` | `integer` | Number of audits with completed workflows (always ≥ 0, ≤ totalAudits) |

### LatestAuditScores Object (nullable)

Returns `null` if the brand has no completed audits.

| Field | Type | Description |
|-------|------|-------------|
| `auditId` | `string` (UUID) | ID of the latest completed audit |
| `productName` | `string \| null` | Product name from audit data (may be null) |
| `targetMarket` | `string \| null` | Target market from audit data (may be null) |
| `completedAt` | `string` (ISO 8601) | Timestamp when the audit workflow was completed |
| `categoryScores` | `array` | Array of category score objects (see below) |
| `overallScore` | `integer \| null` | Average percent of all category scores (0-100, null if no scores) |
| `certification` | `string \| null` | Certification level: `"Bronze"` (>60%), `"Silver"` (>75%), `"Gold"` (>90%), or `null`. Only awarded when `data_completeness > 90` |

### CategoryScore Object

| Field | Type | Description |
|-------|------|-------------|
| `category` | `string` | One of: `"ENVIRONMENTAL"`, `"SOCIAL"`, `"CIRCULARITY"`, `"TRANSPARENCY"` |
| `score` | `integer` | Numeric score (0-100) |

**Note**: Category scores are returned as numeric values only. The frontend is responsible for:
- Determining rating labels (e.g., "Excellent", "Good", "Fair", "Poor") based on score ranges
- Displaying category descriptions (e.g., "Carbon, water, waste" for Environmental)

### RecentAuditWorkflow Object

| Field | Type | Description |
|-------|------|-------------|
| `workflowId` | `string` (UUID) | ID of the workflow |
| `auditId` | `string` (UUID) | ID of the audit |
| `productName` | `string \| null` | Product name from audit data (may be null) |
| `targetMarket` | `string \| null` | Target market from audit data (may be null) |
| `status` | `string` | Display status: `"Completed"`, `"Processing"`, `"Generated"`, or `"Failed"` |
| `categoryScores` | `array \| null` | Array of category score objects (only present if `status === "Completed"`) |
| `overallScore` | `integer \| null` | Average percent of all category scores (0-100, only present if `status === "Completed"`) |
| `certification` | `string \| null` | Certification level: `"Bronze"`, `"Silver"`, `"Gold"`, or `null`. Only awarded when `data_completeness > 90` (only present if `status === "Completed"`) |
| `createdAt` | `string` (ISO 8601) | Timestamp when the workflow was created |

## Status Mapping

The backend maps internal workflow statuses to user-friendly display statuses:

| Backend Status | Display Status |
|----------------|----------------|
| `PROCESSING_COMPLETE` | `"Completed"` |
| `PROCESSING` | `"Processing"` |
| `GENERATED` | `"Generated"` |
| `PROCESSING_FAILED` | `"Failed"` |
| No workflow | `"Generated"` |

## Certification Calculation

Certification levels are automatically calculated based on `overallScore`, but **only awarded when `data_completeness > 90`**:

| Overall Score Range | Certification |
|---------------------|---------------|
| ≥ 90 | `"Gold"` |
| ≥ 75 | `"Silver"` |
| > 60 | `"Bronze"` |
| ≤ 60 | `null` (no certification) |

**Important Requirements:**
- `data_completeness` must be **> 90** for any certification to be awarded
- If `data_completeness ≤ 90`, certification will be `null` regardless of `overallScore`
- `overallScore` is calculated as the average of all category scores (Environmental, Social, Circularity, Transparency)
- `data_completeness` represents the ratio of evidence claims with uploaded evidence (0-100)

## Edge Cases

### No Audits

When a brand has no audits:

```json
{
  "summary": {
    "totalAudits": 0,
    "completedAudits": 0
  },
  "latestAuditScores": null,
  "recentAuditWorkflows": []
}
```

### No Completed Audits

When a brand has audits but none are completed:

```json
{
  "summary": {
    "totalAudits": 3,
    "completedAudits": 0
  },
  "latestAuditScores": null,
  "recentAuditWorkflows": [
    {
      "auditId": "...",
      "status": "Processing",
      "categoryScores": null,
      ...
    }
  ]
}
```

### Partial Category Scores

If an audit has incomplete category scores, only available categories are returned:

```json
{
  "categoryScores": [
    {
      "category": "ENVIRONMENTAL",
      "score": 82
    },
    {
      "category": "TRANSPARENCY",
      "score": 88
    }
  ]
}
```

Missing categories (SOCIAL, CIRCULARITY) are simply omitted - they are not included as null or 0.

### Null Product Information

Both `productName` and `targetMarket` can be `null` if not provided in the audit data. Handle these gracefully in the UI.

## Frontend Implementation Examples

### TypeScript Types

```typescript
interface CategoryScore {
  category: "ENVIRONMENTAL" | "SOCIAL" | "CIRCULARITY" | "TRANSPARENCY";
  score: number; // 0-100
}

interface DashboardSummary {
  totalAudits: number;
  completedAudits: number;
}

interface LatestAuditScores {
  auditId: string;
  workflowId: string;
  productName: string | null;
  targetMarket: string | null;
  completedAt: string; // ISO 8601 datetime
  categoryScores: CategoryScore[];
  overallScore: number | null; // 0-100
  certification: "Bronze" | "Silver" | "Gold" | null;
}

interface RecentAuditWorkflow {
  workflowId: string;
  auditId: string;
  productName: string | null;
  targetMarket: string | null;
  status: "Completed" | "Processing" | "Generated" | "Failed";
  categoryScores: CategoryScore[] | null;
  overallScore: number | null; // 0-100, only present if status === "Completed"
  certification: "Bronze" | "Silver" | "Gold" | null; // only present if status === "Completed"
  createdAt: string; // ISO 8601 datetime
}

interface DashboardResponse {
  summary: DashboardSummary;
  latestAuditScores: LatestAuditScores | null;
  recentAuditWorkflows: RecentAuditWorkflow[];
}
```

### React Hook Example

```typescript
import { useQuery } from '@tanstack/react-query';
import { DashboardResponse } from './types';

export function useDashboard() {
  return useQuery<DashboardResponse>({
    queryKey: ['dashboard'],
    queryFn: async () => {
      const token = await clerk.session.getToken();
      const response = await fetch('/api/v1/brands/dashboard', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch dashboard data');
      }
      
      return response.json();
    },
  });
}
```

### Rating Label Helper

```typescript

export function getCategoryDescription(category: string): string {
  const descriptions: Record<string, string> = {
    ENVIRONMENTAL: "Carbon, water, waste",
    SOCIAL: "Labor, community",
    CIRCULARITY: "Design, end-of-life",
    TRANSPARENCY: "Traceability, disclosure",
  };
  return descriptions[category] || "";
}
```

### Latest Certification Card Component

The "Latest Certification" card displays the most recent certification achieved by any completed audit workflow. Use the `latestAuditScores` object from the dashboard response.

**Required Fields:**
- `workflowId` - UUID of the completed audit workflow
- `certification` - Certification level ("Bronze", "Silver", or "Gold")
- `productName` - Product name that achieved the certification
- `completedAt` - Date when the certification was awarded

**Example Component:**

```typescript
import { format } from 'date-fns';

interface LatestCertificationProps {
  latestAuditScores: LatestAuditScores | null;
}

function LatestCertification({ latestAuditScores }: LatestCertificationProps) {
  // Handle case when no completed audits exist
  if (!latestAuditScores || !latestAuditScores.certification) {
    return (
      <div className="certification-card">
        <h3>Latest Certification</h3>
        <p>No certifications yet</p>
      </div>
    );
  }

  const { workflowId, certification, productName, completedAt } = latestAuditScores;
  
  // Format certification display text
  const certificationText = `${certification} Certified`;
  
  // Format completion date (e.g., "Jan 20, 2024")
  const formattedDate = format(new Date(completedAt), 'MMM d, yyyy');
  
  // workflowId can be used for navigation to workflow details
  const handleClick = () => {
    // Navigate to workflow details page
    router.push(`/workflows/${workflowId}`);
  };

  return (
    <div className="certification-card">
      <h3>Latest Certification</h3>
      <div className="certification-icon">
        {/* Shield icon - render your shield SVG/icon here */}
      </div>
      <div className="certification-level">{certificationText}</div>
      <div className="product-name">{productName || 'Unnamed Product'}</div>
      <div className="certification-date">{formattedDate}</div>
    </div>
  );
}
```

**Usage:**

```typescript
function Dashboard() {
  const { data, isLoading } = useDashboard();
  
  if (isLoading) return <div>Loading...</div>;
  if (!data) return <div>Error loading dashboard</div>;
  
  return (
    <div>
      <LatestCertification latestAuditScores={data.latestAuditScores} />
      {/* Other dashboard components */}
    </div>
  );
}
```

**Data Mapping:**

| UI Element | Data Source | Notes |
|------------|-------------|-------|
| Workflow ID | `latestAuditScores.workflowId` | UUID of the workflow (useful for linking to workflow details) |
| Certification Level | `latestAuditScores.certification` | "Bronze", "Silver", or "Gold" |
| Certification Text | `latestAuditScores.certification + " Certified"` | Display as "Silver Certified", etc. |
| Product Name | `latestAuditScores.productName` | May be `null` - handle gracefully |
| Completion Date | `latestAuditScores.completedAt` | ISO 8601 datetime - format for display |
| Shield Icon | N/A | Frontend renders based on certification level |

**Edge Cases:**
- If `latestAuditScores` is `null`: Show "No certifications yet" or hide the card
- If `certification` is `null`: Same as above (shouldn't happen if `latestAuditScores` exists, but handle defensively)
- If `productName` is `null`: Display fallback text like "Unnamed Product" or omit product name

### Display Component Example

```typescript
function DashboardSummary({ summary }: { summary: DashboardSummary }) {
  return (
    <div>
      <div>Total Audits: {summary.totalAudits}</div>
      <div>Completed Audits: {summary.completedAudits}</div>
    </div>
  );
}

function CategoryScoreDisplay({ score }: { score: CategoryScore }) {
  return (
    <div>
      <span>{score.category}</span>
      <span>{score.score} / 100</span>
      <span>{getRatingLabel(score.score)}</span>
      <span>{getCategoryDescription(score.category)}</span>
    </div>
  );
}

function LatestAuditScores({ scores }: { scores: LatestAuditScores | null }) {
  if (!scores) {
    return <div>No completed audits yet</div>;
  }
  
  return (
    <div>
      <h3>{scores.productName || "Unnamed Product"}</h3>
      <p>Target Market: {scores.targetMarket || "N/A"}</p>
      <p>Completed: {new Date(scores.completedAt).toLocaleDateString()}</p>
      <div>
        {scores.categoryScores.map((score) => (
          <CategoryScoreDisplay key={score.category} score={score} />
        ))}
      </div>
    </div>
  );
}
```

## Data Ordering

- **Recent Workflows**: Ordered by workflow `created_at` descending (newest first)
- **Latest Audit**: Selected by `completedAt` (workflow `updated_at`) descending, with tiebreaker by audit `created_at` descending
- **Category Scores**: Order is consistent but not guaranteed - sort by category name if needed

## Performance Considerations

- The endpoint is optimized for brands with up to 100 audits
- Response time target: <500ms
- All data is fetched in a single request (no pagination needed for recent workflows - limited to 3)
- Recent workflows query is optimized with direct workflow table access and index on `updated_at`
- Consider caching the dashboard response for 30-60 seconds to reduce server load

## Notes

- **Certifications**: Certification levels (`Bronze`, `Silver`, `Gold`) are automatically calculated based on `overallScore` and included in `latestAuditScores` and `recentAudits` (when status is "Completed")
- **Rating Labels**: Backend returns numeric scores only - frontend determines rating labels and descriptions
- **Product Identifier Format**: The UI can format `productName` and `targetMarket` as "Product • Market" (e.g., "Organic Cotton Tee • EU")
- **Empty States**: Handle `null` values gracefully:
  - `latestAuditScores: null` → Show "No completed audits" message or hide "Latest Certification" card
  - `certification: null` → Show "No certifications yet" or hide certification badge
  - `productName: null` → Show "Unnamed Product" or similar placeholder
  - `categoryScores: null` in recent audits → Only show for "Completed" status

## Testing

Test the endpoint with:

```bash
# Get authentication token from Clerk
TOKEN="your_jwt_token"

# Fetch dashboard data
curl -X GET "http://localhost:8000/api/v1/brands/dashboard" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"
```

## Related Endpoints

- `GET /api/v1/audits` - List all audits (with pagination)
- `GET /api/v1/audits/{audit_id}` - Get specific audit details
- `GET /api/v1/brands` - List user's brands
