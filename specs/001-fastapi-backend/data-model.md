# Data Model: FastAPI Backend Implementation

**Feature**: FastAPI Backend Implementation  
**Date**: 2025-01-27  
**Phase**: 1 - Design

## Entities

### Audit Record

**Purpose**: Tracks system activities, changes, and events for audit trail functionality.

**Table Name**: `audit` (singular, lower_case_snake per constitution)

**Attributes**:

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| `id` | UUID | Primary Key | Unique identifier for the audit record |
| `action_type` | String (50) | Required, Indexed | Type of action performed (e.g., "create", "update", "delete", "view") |
| `entity_type` | String (100) | Required, Indexed | Type of entity affected (e.g., "user", "post", "audit") |
| `entity_id` | UUID | Required, Indexed | Identifier of the affected entity |
| `user_id` | UUID | Optional, Indexed | Identifier of the user who performed the action (null for system actions) |
| `details` | JSONB | Optional | Additional details about the action in JSON format |
| `status` | String (20) | Required, Default: "success" | Status of the action ("success", "failure", "pending") |
| `ip_address` | String (45) | Optional | IP address of the requester (IPv4 or IPv6) |
| `user_agent` | String (500) | Optional | User agent string from the request |
| `created_at` | Timestamp | Required, Default: now() | Timestamp when the audit record was created |
| `updated_at` | Timestamp | Optional | Timestamp when the audit record was last updated |

**Indexes**:
- Primary key: `audit_pkey` on `id`
- Index: `action_type_idx` on `action_type`
- Index: `entity_type_idx` on `entity_type`
- Index: `entity_id_idx` on `entity_id`
- Index: `user_id_idx` on `user_id`
- Index: `created_at_idx` on `created_at` (for time-based queries)

**Validation Rules**:
- `action_type` must be one of: "create", "update", "delete", "view", "export", "import", "login", "logout", "other"
- `status` must be one of: "success", "failure", "pending"
- `entity_type` must be non-empty string
- `entity_id` must be valid UUID format
- `user_id` must be valid UUID format if provided
- `ip_address` must be valid IPv4 or IPv6 format if provided
- `details` must be valid JSON if provided

**State Transitions**:
- Created: `status` = "pending" → "success" or "failure"
- Updated: `updated_at` is set when details are modified

**Relationships**:
- May reference other entities via `entity_type` and `entity_id` (polymorphic relationship)
- May reference users via `user_id` (future foreign key when users domain is added)

**Business Rules**:
- Audit records are immutable once created (no updates except status changes)
- Audit records should not be deleted (soft delete via status if needed)
- `created_at` is set automatically and cannot be modified
- `details` JSONB field allows flexible storage of action-specific data

## Database Schema

### Migration Strategy

**Initial Migration**: `YYYY-MM-DD_create_audit_table.py`

**Naming Conventions** (per constitution):
- Table: `audit` (singular, lower_case_snake)
- Columns: `lower_case_snake` with `_at` suffix for datetime
- Indexes: `%(column_0_label)s_idx` pattern
- Foreign keys: `%(table_name)s_%(column_0_name)s_fkey` pattern

**PostgreSQL Features Used**:
- UUID type for primary keys
- JSONB for flexible details storage
- Timestamps with timezone
- Indexes for query performance

## Pydantic Schemas

### AuditRecordCreate (Request)

```python
class AuditRecordCreate(BaseModel):
    action_type: str  # Enum: create, update, delete, view, export, import, login, logout, other
    entity_type: str
    entity_id: UUID
    user_id: Optional[UUID] = None
    details: Optional[Dict[str, Any]] = None
    status: str = "success"  # Enum: success, failure, pending
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
```

### AuditRecordResponse (Response)

```python
class AuditRecordResponse(BaseModel):
    id: UUID
    action_type: str
    entity_type: str
    entity_id: UUID
    user_id: Optional[UUID]
    details: Optional[Dict[str, Any]]
    status: str
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
```

### AuditRecordUpdate (Request - Limited)

```python
class AuditRecordUpdate(BaseModel):
    status: Optional[str] = None  # Only status can be updated
    details: Optional[Dict[str, Any]] = None  # Details can be appended
```

### AuditRecordList (Query Parameters)

```python
class AuditRecordList(BaseModel):
    action_type: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    status: Optional[str] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    limit: int = 50  # Pagination
    offset: int = 0  # Pagination
```

## SQLModel Model

```python
class Audit(SQLModel, table=True):
    __tablename__ = "audit"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    action_type: str = Field(max_length=50, index=True)
    entity_type: str = Field(max_length=100, index=True)
    entity_id: UUID = Field(index=True)
    user_id: Optional[UUID] = Field(default=None, index=True)
    details: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSONB))
    status: str = Field(default="success", max_length=20)
    ip_address: Optional[str] = Field(default=None, max_length=45)
    user_agent: Optional[str] = Field(default=None, max_length=500)
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True), index=True))
    updated_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True)))
```

## Query Patterns

### Common Queries

1. **List audits by entity**: Filter by `entity_type` and `entity_id`
2. **List audits by user**: Filter by `user_id`
3. **List audits by action**: Filter by `action_type`
4. **Time-based queries**: Filter by `created_at` range
5. **Pagination**: Use `limit` and `offset` for large result sets

### Performance Considerations

- Indexes on frequently queried columns (`action_type`, `entity_type`, `entity_id`, `user_id`, `created_at`)
- JSONB `details` field allows efficient querying of nested data
- Pagination required for list endpoints to prevent large result sets
