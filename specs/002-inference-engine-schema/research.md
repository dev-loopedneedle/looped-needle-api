# Research: Dynamic Audit Inference Engine

**Date**: 2025-01-27  
**Feature**: 002-inference-engine-schema

## Research Questions

### 1. JEXL Expression Evaluation Library for Python

**Question**: What Python library should be used for evaluating JEXL (JSON Expression Language) expressions?

**Research Findings**:
- **python-jexl** (https://github.com/mozilla/python-jexl) is the official Python port of JEXL
- Supports async evaluation (can be wrapped in async context)
- Provides error handling for invalid expressions
- Allows custom transforms and functions
- Well-maintained and actively used

**Decision**: Use `python-jexl` library for rule condition expression evaluation.

**Rationale**: 
- Official Python port of JEXL, ensuring compatibility with JEXL syntax
- Supports error handling which aligns with requirement to skip failed rules gracefully
- Can be wrapped in async context for non-blocking evaluation
- Active maintenance and community support

**Alternatives Considered**:
- **jexl-py**: Less maintained, fewer features
- **Custom parser**: Too complex, reinventing the wheel
- **JavaScript JEXL via subprocess**: Overhead and complexity

**Implementation Notes**:
- Install: `pip install python-jexl`
- Wrap evaluation in try/except to catch `JexlException` for invalid expressions
- Log errors before skipping failed rules
- Evaluation is CPU-bound but lightweight, can run synchronously in async context

---

### 2. Soft Delete Pattern in SQLAlchemy/SQLModel

**Question**: How to implement soft delete with referential integrity checks in SQLAlchemy/SQLModel?

**Research Findings**:
- Add `deleted_at: datetime | None` field to models
- Use SQLAlchemy `hybrid_property` or query filters to exclude deleted records
- Check referential integrity before allowing deletion (query for references)
- Use database-level constraints (foreign keys) to prevent hard deletes of referenced entities

**Decision**: Implement soft delete using `deleted_at` timestamp field with query filtering.

**Rationale**:
- Preserves audit trail integrity (FR-025, FR-026)
- Allows cleanup of unused data while maintaining historical references
- Standard pattern in audit/compliance systems
- Can be implemented at model level with minimal code changes

**Alternatives Considered**:
- **Hard delete with cascade**: Would lose audit history
- **Separate archive table**: More complex, harder to query
- **Status enum field**: Less explicit, harder to query by deletion time

**Implementation Notes**:
- Add `deleted_at: datetime | None` to all entities that support soft delete
- Create base mixin class for soft delete functionality
- Filter queries: `.filter(Model.deleted_at.is_(None))`
- Check references before deletion: Query for audit items referencing entity
- Raise exception if referenced, otherwise set `deleted_at = datetime.utcnow()`

---

### 3. State Machine Pattern for Status Transitions

**Question**: How to implement forward-only state transitions for audit instances and audit items?

**Research Findings**:
- Use Python `Enum` for status values
- Validate transitions in service layer before updating
- Use database constraints (CHECK constraint) as backup validation
- Define transition rules as data structure or validation function

**Decision**: Use Python `Enum` with transition validation in service layer.

**Rationale**:
- Simple and explicit
- Easy to test
- Clear error messages
- Can be extended with transition history if needed

**Alternatives Considered**:
- **State machine library (transitions)**: Overkill for simple forward-only transitions
- **Database triggers**: Less maintainable, harder to test
- **ORM-level validation**: Less flexible

**Implementation Notes**:
- Define status enums in `constants.py`:
  - `AuditInstanceStatus`: IN_PROGRESS, REVIEWING, CERTIFIED
  - `AuditItemStatus`: MISSING_EVIDENCE, EVIDENCE_PROVIDED, UNDER_REVIEW, ACCEPTED, REJECTED
- Create transition validation functions:
  - `can_transition_audit_instance(from_status, to_status) -> bool`
  - `can_transition_audit_item(from_status, to_status) -> bool`
- Validate in service layer before database update
- Raise `InvalidStatusTransitionError` if transition not allowed

---

### 4. JSONB Storage for Complex Nested Data

**Question**: How to store and query JSONB data (materials composition, questionnaire schemas, brand snapshots) in PostgreSQL via SQLAlchemy?

**Research Findings**:
- SQLAlchemy supports JSONB via `JSON` type with `postgresql.JSONB`
- SQLModel inherits this support
- PostgreSQL JSONB operators (`@>`, `?`, `->`, `->>`) available via `func()`
- Can index JSONB fields with GIN indexes for performance

**Decision**: Use SQLAlchemy `JSON` type with PostgreSQL-specific JSONB.

**Rationale**:
- Native PostgreSQL support for efficient JSON storage and querying
- SQLAlchemy/SQLModel provide good abstraction
- Can query nested fields using PostgreSQL JSONB operators
- GIN indexes provide good query performance

**Alternatives Considered**:
- **Separate tables**: Too complex, loses atomicity
- **Text/JSON string**: No query capabilities, no validation
- **NoSQL database**: Overkill, adds complexity

**Implementation Notes**:
- Use `JSON` type from `sqlalchemy.types` or `sqlmodel.Field` with `sa_column=Column(JSON)`
- For PostgreSQL-specific JSONB: `sa_column=Column(postgresql.JSONB)`
- Query examples:
  - `session.query(Model).filter(Model.jsonb_field['key'].astext == 'value')`
  - `session.query(Model).filter(Model.jsonb_field.op('@>')({'key': 'value'}))`
- Add GIN indexes for frequently queried JSONB fields

---

### 5. Brand Context Snapshot Implementation

**Question**: How to capture and store a deep snapshot of brand context (brand, products, supply chain) at audit creation time?

**Research Findings**:
- Store snapshot as JSONB in `audit_instances.brand_context_snapshot`
- Snapshot should include: brand profile, all products, all supply chain nodes
- Use SQLAlchemy relationships to fetch related data
- Serialize to dict/JSON before storing
- Can use Pydantic models for validation before serialization

**Decision**: Fetch related data via relationships, serialize to dict, store as JSONB.

**Rationale**:
- Simple and straightforward
- Preserves exact state at creation time
- Can be queried/displayed without joins
- Aligns with requirement for snapshot preservation

**Alternatives Considered**:
- **Separate snapshot tables**: More complex, harder to query
- **Pointers to original data**: Would reflect changes, violates requirement
- **Event sourcing**: Overkill for this use case

**Implementation Notes**:
- In service layer, fetch brand with products and supply chain nodes
- Convert SQLModel instances to dicts (use `model_dump()` or `dict()`)
- Store complete nested structure in `brand_context_snapshot` JSONB field
- Snapshot is read-only after creation (no updates)

---

### 6. Rule Evaluation Performance Optimization

**Question**: How to optimize rule evaluation for up to 1000 rules while meeting <5s p95 performance target?

**Research Findings**:
- Batch evaluation: Evaluate all rules in single pass
- Early termination: Skip evaluation if prerequisite conditions not met
- Database filtering: Pre-filter rules by domain or other criteria if possible
- Caching: Cache compiled JEXL expressions (python-jexl supports this)
- Parallel evaluation: Use asyncio.gather for concurrent evaluation (if rules are independent)

**Decision**: Use batch evaluation with compiled expression caching and early filtering.

**Rationale**:
- Meets performance target (<5s for 1000 rules)
- Simple to implement
- Caching compiled expressions improves repeated evaluations
- Can add parallelization later if needed

**Alternatives Considered**:
- **Sequential evaluation**: Too slow for 1000 rules
- **Database-level evaluation**: Not feasible with JEXL
- **Rule indexing/pre-filtering**: Good optimization, can add later

**Implementation Notes**:
- Load all active rules from database (filter by active status)
- Compile JEXL expressions once, cache compiled expressions
- Build evaluation context from brand context + questionnaire responses
- Evaluate all rules in batch
- Filter matches by priority (highest priority rule per criterion)
- Create audit items for matching criteria
- Use database transaction for atomicity

---

## Summary

All research questions resolved. Key technical decisions:
1. **python-jexl** for JEXL expression evaluation
2. **Soft delete** via `deleted_at` timestamp with referential integrity checks
3. **State transitions** via Enum + service-layer validation
4. **JSONB storage** via SQLAlchemy JSON type with PostgreSQL JSONB
5. **Brand snapshots** via JSONB serialization of related data
6. **Rule evaluation** via batch processing with expression caching

All decisions align with existing codebase patterns and performance requirements.

