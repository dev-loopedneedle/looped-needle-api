# Quickstart: Rules Engine for Audit Certification

**Branch**: `004-rules-engine` | **Date**: 2026-01-06  
**Spec**: `/specs/004-rules-engine/spec.md`

## Prerequisites
- Python 3.11, Poetry/pip with project deps installed
- PostgreSQL configured; `.env` with DATABASE_URL
- Apply migrations: `alembic upgrade head`

## Admin Flow (Rules & Claims)
1. Create evidence claims (name, description, category, type, weight).
2. Create a rule (name, globally-unique code, description, expression).
3. Attach evidence claims to the rule.
4. Preview/validate expression (syntax + type + sample eval).
5. Publish rule (immutable; used for matching). Disable if needed; clone to edit.

## Brand Flow (Workflows)
1. Create an audit with `audit_data` (product/material/supply chain, etc.).
2. Manually trigger workflow generation: POST `/api/v1/audits/{audit_id}/workflow/generate` (draft audits only).
3. View required evidence: GET `/api/v1/audits/{audit_id}/workflow` (shows claims + rule name/code sources).
4. If audit data changes (while draft), trigger a new generation; published audits cannot be regenerated.

## Key Endpoints (preview)
- Admin: rules CRUD/publish/disable/clone, preview; evidence claim dropdowns.
- Workflows: generate (manual), read latest.

## Success Criteria (operational targets)
- Workflow generation ≤10s for ≤100 published rules.
- Required evidence view ≤2s.
- Traceability 100% (rule name/code per claim).

