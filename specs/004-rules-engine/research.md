# Research: Rules Engine for Audit Certification

**Branch**: `004-rules-engine` | **Date**: 2026-01-06  
**Spec**: `/specs/004-rules-engine/spec.md`

## Decisions

- Manual workflow generation trigger; no automatic generation on audit creation.
- Rule expression validation depth: syntax + type checking + sample evaluation to ensure boolean result.
- Workflow regeneration: creates new generations and only for draft audits; published audits are immutable.
- Rule codes: globally unique across all rules.
- Rule visibility to brand users: show rule name and code (hide expressions).

## Rationale

- Manual trigger prevents premature/incorrect requirements when audit data is incomplete and avoids surprise computations.
- Validation depth catches common authoring errors without blocking valid use cases; full logical validation is infeasible.
- Generations preserve audit history and traceability; immutability of published audits protects certified snapshots.
- Global uniqueness of codes simplifies traceability, lookup, and avoids collision across rule families.
- Showing name/code provides transparency without exposing technical details to non-technical users.

## Alternatives Considered

- Automatic generation on audit create → rejected to avoid noise and unexpected results with partial data.
- Full logical validation of expressions → rejected as impractical and brittle; relies on sample eval instead.
- Overwriting workflows on regeneration → rejected to preserve history and auditability.
- Per-family rule codes → rejected due to ambiguity and collision risk.
- Exposing full rule expressions to brand users → rejected to reduce confusion and avoid leaking internals.

