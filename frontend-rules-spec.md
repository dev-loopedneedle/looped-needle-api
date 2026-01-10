## Frontend Rules Engine Specification

### Status
- **Status**: Draft
- **Owner**: Frontend
- **Scope**: Admin rule creation UI + audit workflow requirements UI

### Goals
- Admin users can create and manage Rules and Evidence Claims without writing code.
- Admin users can validate/preview rule condition trees before publishing.
- Brand users can generate an audit workflow and see the required evidence claims they must provide.

### Non-Goals (for this iteration)
- Full evidence review and auditor tooling.
- Advanced visual programming language beyond boolean conditions + grouping.

---

## Personas & Permissions

### Admin user
- Can access `/admin/rules` screens.
- Can create/edit drafts, publish, disable.
- Can manage evidence claims attached to rules.

### Brand user
- Can access audit workflows for audits in their brand.
- Can generate workflow and view required evidence claims.

---

## Admin UX: Rules Management

### Screen: Rules List (`/admin/rules`)
- **Primary actions**
  - Create rule
  - Filter by state (`DRAFT`, `PUBLISHED`, `DISABLED`)
  - Search by `name`/`code`
- **Table columns**
  - Name
  - Code
  - Version
  - State
  - Updated / Published timestamps
  - Actions: View/Edit, Clone, Publish, Disable

### Screen: Rule Editor (`/admin/rules/new`, `/admin/rules/{id}`)

#### Rule fields
- **Name** (required)
- **Code** (required)
  - UX: auto-suggest from name (slug), but editable
  - Constraint: unique per code+version on backend; frontend should warn if code already exists and user is creating a new family vs new version
- **Description** (optional)
- **State** (read-only display; actions control transitions)

#### Section: Condition Tree Builder

##### Structure
Rules use a **JSON-based condition tree** format. The UI should build this tree structure visually.

##### Node Types

**GroupNode** (Logical Group):
- `type`: "group"
- `id`: unique identifier (e.g., "root", "root-group-0")
- `logical`: "AND" or "OR"
- `children`: array of ConditionNode or GroupNode

**ConditionNode** (Field Condition):
- `type`: "condition"
- `id`: unique identifier (e.g., "root-cond-0")
- `fieldPath`: dot-notation path (e.g., "productInfo.auditScope")
- `operator`: operator based on field type
- `value`: string value (even for numbers/booleans)
- `fieldType`: "string", "number", "boolean", or "enum"

##### Inputs
- **Field selector**: dropdown populated from `GET /api/v1/admin/rules/fields`
  - shows label + path (e.g. "Primary material (materials.primary)")
  - fieldPaths object contains all available paths with their types
- **Operator selector**: based on selected field type
  - string: "equals", "not equals", "contains", "exists"
  - number: "equals", "not equals", ">=", "<=", "exists"
  - boolean: "Is" (value: "true" or "false"), "exists"
  - enum: "equals", "not equals", "exists"
- **Value input**
  - string input, number input (as string), boolean toggle (converts to "true"/"false")
  - enum dropdown if field has `values` array
- **Grouping**
  - Add AND/OR groups with nested conditions
  - Ability to add/remove conditions and groups
  - Root node must be a GroupNode

##### Output
- **Condition Tree (JSON)**: visual representation of the tree structure
  - this is the JSON object sent as `conditionTree` to backend
  - show tree structure visually (nested groups, conditions)

##### Validation & Preview
- **Validate button**
  - calls `POST /api/v1/admin/rules/preview` with:
    - the `conditionTree` JSON object
    - a sample `audit_data` (either user-provided or loaded from a selected existing audit)
  - show:
    - Valid/Invalid
    - If valid: the boolean result (matched true/false)
    - Any errors/warnings
- **Optional: Select an Audit to Preview**
  - picker to select an existing audit (admin only) and use its `audit_data` as preview input

#### Section: Evidence Claims (inline list)

##### Claim fields
- **Name** (required)
- **Description** (optional)
- **Category** (required dropdown)
  - options from `GET /api/v1/admin/evidence-claim-categories`
- **Type** (required dropdown)
  - options from `GET /api/v1/admin/evidence-claim-types`
- **Weight** (required 0..1)
  - UX: slider + numeric input

##### Behaviors
- Add claim
- Remove claim
- Reorder (optional; if backend supports `sort_order`)

#### Publish / Disable
- **Publish**
  - confirmation dialog explaining immutability and versioning
  - on success, redirect to view mode
- **Edit Published**
  - show “Clone to Draft” CTA (calls backend clone endpoint) then open new draft
- **Disable**
  - confirmation dialog

---

## Brand UX: Audit Workflow (Evidence Requirements)

### Entry Points
- Audit detail page: “Evidence Requirements” tab
- Or a dedicated route: `/audits/{audit_id}/workflow`

### Screen: Workflow Summary
- **Header**
  - Workflow status (Generated / Stale)
  - Last generated timestamp
  - CTA: “Generate / Refresh requirements”
    - calls `POST /api/v1/audits/{audit_id}/workflow/generate`

### Screen: Required Evidence Claims (List)
- **Grouping**
  - group by category
  - within category sort by weight desc (or predefined order)
- **Card content**
  - Claim name
  - Description (“how it should look”, expected format)
  - Type badge (certificate/invoice/questionnaire/etc)
  - Weight indicator
  - Status (REQUIRED/SATISFIED)
  - “Why required?” expandable section
    - show the matched rule codes/names (from sources)

### Upload / Fill In (future-compatible UI)
Even if backend submissions are not implemented yet, design the UI with placeholders:
- If claim type is file-like (certificate/invoice/photo/report):
  - upload widget placeholder + “Coming soon” / disabled state until API exists
- If claim type is questionnaire:
  - render a form placeholder (or open a modal) to fill answers

---

## Frontend State & Data Contracts

### Data required from backend for rules editor
- Rule shape:
  - id, code, version, name, description, state, conditionTree (JSON object), timestamps
  - evidence_claims: list of claim definitions
- Field catalog (`GET /api/v1/admin/rules/fields`):
  - fieldPaths: object mapping paths to field metadata (type, values for enums)
  - operators: object mapping field types to available operators
- Preview endpoint result:
  - valid, matched, errors

### Data required from backend for brand workflow UI
- Workflow shape:
  - workflow_id, audit_id, generation, generated_at
  - required_claims: claim + status + sources

---

## Workflow API Endpoints

### List Workflows for Audit
**GET** `/api/v1/audits/{audit_id}/workflows`

Retrieve a paginated list of workflows for an audit, ordered by generation (newest first).

**Query Parameters:**
- `limit` (integer, optional): Maximum number of workflows to return (default: 20, min: 1, max: 100)
- `offset` (integer, optional): Number of workflows to skip (default: 0, min: 0)

**Response:**
```json
{
  "items": [
    {
      "id": "workflow-uuid",
      "auditId": "audit-uuid",
      "generation": 2,
      "status": "GENERATED",
      "generatedAt": "2026-01-09T16:00:00Z",
      "engineVersion": "v1",
      "createdAt": "2026-01-09T16:00:00Z",
      "updatedAt": null
    }
  ],
  "total": 2,
  "limit": 20,
  "offset": 0
}
```

**Use Case:** Display a list of workflow generations for an audit, allowing users to view historical workflows or select a specific workflow to view details.

### Generate Workflow
**POST** `/api/v1/audits/{audit_id}/workflow/generate?force=false`

Generate a new workflow for an audit. If `force=false` and the latest workflow is fresh (matches current audit data), returns the existing workflow instead of creating a new one.

**Query Parameters:**
- `force` (boolean, optional): Force regeneration even if workflow is fresh (default: false)

**Response:** Returns full `WorkflowResponse` with `requiredClaims` and `ruleMatches` (see Get Workflow below).

**Use Case:** Generate or refresh workflow requirements when audit data changes.

### Get Specific Workflow
**GET** `/api/v1/audits/{audit_id}/workflows/{workflow_id}`

Retrieve a specific workflow by ID, including all required evidence claims and rule matches.

**Path Parameters:**
- `audit_id` (UUID): Audit ID
- `workflow_id` (UUID): Workflow ID

**Response:**
```json
{
  "id": "workflow-uuid",
  "auditId": "audit-uuid",
  "generation": 1,
  "status": "GENERATED",
  "generatedAt": "2026-01-09T16:00:00Z",
  "engineVersion": "v1",
  "requiredClaims": [
    {
      "id": "required-claim-uuid",
      "evidenceClaimId": "evidence-claim-uuid",
      "evidenceClaimName": "Product Photo",
      "evidenceClaimDescription": "High-resolution photo of the product",
      "evidenceClaimCategory": "TRACEABILITY",
      "evidenceClaimType": "PHOTO",
      "evidenceClaimWeight": 0.85,
      "status": "REQUIRED",
      "sources": [
        {
          "ruleId": "rule-uuid",
          "ruleCode": "R-001",
          "ruleName": "Product Traceability Rule",
          "ruleVersion": 1
        }
      ],
      "createdAt": "2026-01-09T16:00:00Z",
      "updatedAt": null
    }
  ],
  "ruleMatches": [
    {
      "ruleId": "rule-uuid",
      "ruleCode": "R-001",
      "ruleVersion": 1,
      "matched": true,
      "error": null,
      "evaluatedAt": "2026-01-09T16:00:00Z"
    }
  ],
  "createdAt": "2026-01-09T16:00:00Z",
  "updatedAt": null
}
```

**Use Case:** Display detailed workflow information including all required evidence claims and which rules matched.

### Frontend Implementation Notes

1. **Workflow Selection Flow:**
   - First, call `GET /api/v1/audits/{audit_id}/workflows` to list available workflows
   - Display the list (showing generation numbers, status, timestamps)
   - When user selects a workflow, call `GET /api/v1/audits/{audit_id}/workflows/{workflow_id}` to get full details
   - Or, if you know the workflow ID (e.g., from generate response), call the get endpoint directly

2. **Generate Workflow Flow:**
   - Call `POST /api/v1/audits/{audit_id}/workflow/generate`
   - Response includes the full workflow with `id` field
   - Store the `id` to fetch it later, or immediately display the workflow details

3. **Pagination:**
   - Use `limit` and `offset` query parameters for pagination
   - `total` indicates total number of workflows across all pages
   - Order is always by generation descending (newest first)

---

## Pagination for List Endpoints

### Overview
All list endpoints in the API use **offset-based pagination** with query parameters. This section describes how pagination works and how the frontend should implement it.

### Key Concepts
- **`total`**: The total count of **all items** matching the query/filters across **all pages**. This is not the count of items on the current page.
- **`items`**: Array of items returned for the current page (length ≤ `limit`)
- **`limit`**: Maximum number of items per page
- **`offset`**: Number of items to skip before returning results

**Example**: If there are 150 rules total and you request `limit=50&offset=0`:
- `items.length` = 50 (items on page 1)
- `total` = 150 (all matching rules across all pages)
- To see all 150 rules, you'd need 3 pages (50 + 50 + 50)

### Pagination Parameters

#### Query Parameters
- **`limit`** (integer, optional)
  - Maximum number of items to return per page
  - Default: varies by endpoint (see below)
  - Minimum: 1
  - Maximum: varies by endpoint (see below)
  
- **`offset`** (integer, optional)
  - Number of items to skip before returning results
  - Default: 0
  - Minimum: 0
  - Example: `offset=50` skips the first 50 items

### Endpoint-Specific Pagination

#### Rules List (`GET /api/v1/admin/rules`)
- **Default limit**: 50
- **Maximum limit**: 100
- **Response format**:
  ```json
  {
    "items": [...],  // Array of RuleResponse objects
    "total": 150,    // Total number of rules matching the query (across all pages)
    "limit": 50,     // Current limit used
    "offset": 0      // Current offset used
  }
  ```

#### Evidence Claims List (`GET /api/v1/admin/rules/evidence-claims`)
- **Default limit**: 50
- **Maximum limit**: 100
- **Response format**:
  ```json
  {
    "items": [...],  // Array of EvidenceClaimResponse objects
    "total": 25,     // Total number of evidence claims matching the query (across all pages)
    "limit": 50,     // Current limit used
    "offset": 0      // Current offset used
  }
  ```

#### Brands List (`GET /api/v1/brands`)
- **Default limit**: 20
- **Maximum limit**: 50
- **Response format**:
  ```json
  {
    "items": [...],  // Array of BrandResponse objects
    "total": 75,     // Total number of brands
    "limit": 20,     // Current limit used
    "offset": 0      // Current offset used
  }
  ```

#### Audits List (`GET /api/v1/audits`)
- **Default limit**: 20
- **Maximum limit**: 50
- **Response format**:
  ```json
  {
    "items": [...],  // Array of AuditResponse objects
    "total": 200,    // Total number of audits matching filters
    "limit": 20,     // Current limit used
    "offset": 0      // Current offset used
  }
  ```

### Frontend Implementation Guide

#### 1. Making Paginated Requests

**Example: Fetching rules with pagination**
```typescript
// First page (items 0-49)
const response = await fetch('/api/v1/admin/rules?limit=50&offset=0');

// Second page (items 50-99)
const response = await fetch('/api/v1/admin/rules?limit=50&offset=50');

// With filters
const response = await fetch(
  '/api/v1/admin/rules?state=PUBLISHED&limit=50&offset=0'
);
```

#### 2. Calculating Pagination Metadata

For all paginated list endpoints:
```typescript
interface PaginatedResponse<T> {
  items: T[];        // Items on the current page (length <= limit)
  total: number;     // Total count of ALL items matching the query across ALL pages
  limit: number;     // Current page size (always present)
  offset: number;    // Current offset (always present)
}

// Understanding the values:
// - items.length = number of items on current page (may be less than limit on last page)
// - total = total number of items matching filters/query across all pages
// - limit = maximum items per page
// - offset = number of items skipped before current page

// Calculate pagination info using returned limit/offset
const currentPage = Math.floor(offset / limit) + 1;
const totalPages = Math.ceil(total / limit);
const hasNextPage = offset + limit < total;
const hasPreviousPage = offset > 0;

// Example: If total=150, limit=50, offset=0
// - items.length = 50 (first page)
// - total = 150 (all matching items)
// - totalPages = 3
// - Display: "Showing 1-50 of 150 items"
```

#### 3. Building Pagination UI

**Recommended pagination controls:**
- **Page numbers**: Show current page and adjacent pages
- **Previous/Next buttons**: Enable/disable based on `hasPreviousPage`/`hasNextPage`
- **Page size selector**: Allow users to change `limit` (e.g., 20, 50, 100)
- **Total count display**: Show "Showing X-Y of Z items"

**Example pagination component state:**
```typescript
interface PaginationState {
  limit: number;      // Current page size
  offset: number;     // Current offset
  total: number;      // Total items from API
  currentPage: number; // Calculated: Math.floor(offset / limit) + 1
  totalPages: number; // Calculated: Math.ceil(total / limit)
}
```

#### 4. Handling Page Changes

**When user clicks "Next Page":**
```typescript
const nextOffset = currentOffset + limit;
fetch(`/api/v1/admin/rules?limit=${limit}&offset=${nextOffset}`);
```

**When user changes page size:**
```typescript
// Reset to first page when changing limit
const newLimit = 100; // User selected 100 items per page
const newOffset = 0;  // Reset to beginning
fetch(`/api/v1/admin/rules?limit=${newLimit}&offset=${newOffset}`);
```

**When user navigates to specific page:**
```typescript
const pageNumber = 3; // User clicked page 3
const newOffset = (pageNumber - 1) * limit;
fetch(`/api/v1/admin/rules?limit=${limit}&offset=${newOffset}`);
```

#### 5. Preserving Filters with Pagination

**Important**: When paginating, preserve all filter parameters:
```typescript
// Good: Preserve filters when changing pages
const filters = { state: 'PUBLISHED', code: 'MATERIAL' };
const queryParams = new URLSearchParams({
  ...filters,
  limit: limit.toString(),
  offset: offset.toString(),
});
fetch(`/api/v1/admin/rules?${queryParams}`);

// Bad: Losing filters when paginating
fetch(`/api/v1/admin/rules?limit=${limit}&offset=${offset}`); // Filters lost!
```

#### 6. Handling Edge Cases

**Empty results:**
- When `total === 0`, show empty state message
- When `items.length === 0` but `total > 0`, this shouldn't happen, but handle gracefully

**Last page:**
- When `offset + limit >= total`, disable "Next" button
- Show "Showing X-Y of Z items" where Y might be less than `offset + limit`

**Invalid offset:**
- If user manually enters an offset >= total, API will return empty array
- Frontend should validate or reset to valid offset

### Best Practices

1. **Store pagination state in URL query params** for shareable/bookmarkable links
   ```
   /admin/rules?state=PUBLISHED&limit=50&offset=0
   ```

2. **Debounce rapid page changes** to avoid excessive API calls

3. **Show loading states** while fetching paginated data

4. **Cache pagination metadata** (total count) when possible, but refresh when filters change

5. **Reset to page 1** when filters change (set `offset=0`)

6. **Handle API errors gracefully** - if pagination request fails, show error but keep previous page data visible

### Example: Complete Pagination Hook

```typescript
function usePaginatedRules(filters: RuleFilters) {
  const [limit, setLimit] = useState(50);
  const [offset, setOffset] = useState(0);
  const [data, setData] = useState<PaginatedResponse<Rule>>();
  const [loading, setLoading] = useState(false);

  const fetchRules = async () => {
    setLoading(true);
    const params = new URLSearchParams({
      ...filters,
      limit: limit.toString(),
      offset: offset.toString(),
    });
    const response = await fetch(`/api/v1/admin/rules?${params}`);
    const json = await response.json();
    setData(json);
    setLoading(false);
  };

  useEffect(() => {
    fetchRules();
  }, [limit, offset, ...Object.values(filters)]);

  const goToPage = (page: number) => {
    setOffset((page - 1) * limit);
  };

  const changePageSize = (newLimit: number) => {
    setLimit(newLimit);
    setOffset(0); // Reset to first page
  };

  // Note: You can use returned limit/offset from data, or track locally.
  // Tracking locally is useful for controlling pagination before the request completes.
  const currentLimit = data?.limit ?? limit;
  const currentOffset = data?.offset ?? offset;

  return {
    rules: data?.items ?? [],
    total: data?.total ?? 0,
    limit: currentLimit,
    offset: currentOffset,
    loading,
    goToPage,
    changePageSize,
    currentPage: Math.floor(currentOffset / currentLimit) + 1,
    totalPages: Math.ceil((data?.total ?? 0) / currentLimit),
  };
}
```

---

## Condition Tree Format

### Overview
Rules use a **JSON-based condition tree** format instead of string expressions. The `conditionTree` field is a JSON object that represents nested logical conditions.

### Structure

#### GroupNode (Logical Group)
```json
{
  "type": "group",
  "id": "root",
  "logical": "AND",  // or "OR"
  "children": [
    // Array of ConditionNode or GroupNode
  ]
}
```

#### ConditionNode (Field Condition)
```json
{
  "type": "condition",
  "id": "root-cond-0",
  "fieldPath": "productInfo.auditScope",
  "operator": "equals",
  "value": "Single Product",
  "fieldType": "enum"
}
```

### Field Paths
Field paths use dot notation to reference nested audit data:
- `productInfo.productName`
- `productInfo.auditScope`
- `materials.certifiedOrganic`
- `supplyChain.visibility.tier1Documented`
- `sustainability.environmental.chemicalManagement`

### Supported Operators

| Field Type | Operators |
|------------|-----------|
| `string` | `equals`, `not equals`, `contains`, `exists` |
| `number` | `equals`, `not equals`, `>=`, `<=`, `exists` |
| `boolean` | `Is` (value: `"true"` or `"false"`), `exists` |
| `enum` | `equals`, `not equals`, `exists` |

### Example: Complex Condition Tree

```json
{
  "type": "group",
  "id": "root",
  "logical": "AND",
  "children": [
    {
      "type": "condition",
      "id": "root-cond-0",
      "fieldPath": "productInfo.auditScope",
      "operator": "equals",
      "value": "Single Product",
      "fieldType": "enum"
    },
    {
      "type": "group",
      "id": "root-group-0",
      "logical": "OR",
      "children": [
        {
          "type": "condition",
          "id": "root-group-0-cond-0",
          "fieldPath": "materials.certifiedOrganic",
          "operator": "Is",
          "value": "true",
          "fieldType": "boolean"
        },
        {
          "type": "condition",
          "id": "root-group-0-cond-1",
          "fieldPath": "materials.recycledContent",
          "operator": ">=",
          "value": "50",
          "fieldType": "number"
        }
      ]
    }
  ]
}
```

This represents: `(auditScope = "Single Product") AND ((certifiedOrganic = true) OR (recycledContent >= 50))`

### Validation Requirements

1. **Root node must be a GroupNode** with `type: "group"`
2. **Logical operator** must be `"AND"` or `"OR"`
3. **Children array** must contain valid ConditionNode or GroupNode objects
4. **Field paths** must reference valid audit data fields (check against `/fields` endpoint)
5. **Operators** must match the field type
6. **Values** must be strings (even for numbers/booleans - convert `true` to `"true"`, `50` to `"50"`)

### API Endpoints

- **Create/Update Rule**: Send `conditionTree` as JSON object in request body
- **Get Rule**: Receive `conditionTree` as JSON object in response
- **Preview Rule**: Send `conditionTree` to `/preview` endpoint for validation and evaluation

---

## UX Edge Cases
- Rule validation fails on publish: show backend errors inline and keep rule in draft.
- Workflow generation returns zero claims: show an empty state (“No evidence required yet based on current audit data”).
- Audit data incomplete: workflow still generates; rules relying on missing fields evaluate to false unless `exists(...)` checks are used.

---

## Implementation Notes (Frontend)
- Build condition tree structure visually using drag-and-drop or form-based UI
- Store condition tree as JSON object in component state
- Root node must always be a GroupNode with type "group"
- Generate unique IDs for each node (e.g., "root", "root-cond-0", "root-group-0")
- Prefer backend-driven field catalog for consistency with backend evaluation and schema evolution
- All values must be strings (convert numbers/booleans to strings before sending)

