# Implementation Plan: [FEATURE]

**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link]
**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

[Extract from feature spec: primary requirement + technical approach from research]

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: [e.g., Python 3.11, Swift 5.9, Rust 1.75 or NEEDS CLARIFICATION]  
**Primary Dependencies**: [e.g., FastAPI, UIKit, LLVM or NEEDS CLARIFICATION]  
**Storage**: [if applicable, e.g., PostgreSQL, CoreData, files or N/A]  
**Testing**: [e.g., pytest, XCTest, cargo test or NEEDS CLARIFICATION]  
**Target Platform**: [e.g., Linux server, iOS 15+, WASM or NEEDS CLARIFICATION]
**Project Type**: [single/web/mobile - determines source structure]  
**Performance Goals**: [domain-specific, e.g., 1000 req/s, 10k lines/sec, 60 fps or NEEDS CLARIFICATION]  
**Constraints**: [domain-specific, e.g., <200ms p95, <100MB memory, offline-capable or NEEDS CLARIFICATION]  
**Scale/Scope**: [domain-specific, e.g., 10k users, 1M LOC, 50 screens or NEEDS CLARIFICATION]

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Domain-Driven Structure**: Does this feature belong to an existing domain, or does it require a new domain module? New domains MUST follow the structure: `src/[domain]/router.py`, `schemas.py`, `models.py`, `dependencies.py`, `service.py`, etc.

**Async-First**: Are all I/O operations (DB, external APIs, file ops) async? CPU-intensive work MUST use thread pools.

**Pydantic Models**: Are all API request/response models defined using Pydantic? Are `response_model`, `status_code`, `description`, `tags`, and `summary` specified for endpoints?

**Dependency Injection**: Are shared resources (DB sessions, external clients, auth) injected via FastAPI dependencies? Are dependencies chained and reused?

**SQL-First**: Are complex joins, aggregations, and JSON building done in SQL rather than Python? Database processing preferred over application-side manipulation.

**Testing**: Will integration tests use async test clients (`httpx.AsyncClient`)? Test structure MUST mirror source domain structure.

**Code Quality**: Will code pass ruff linting? Are pre-commit hooks configured? Are imports at the top of files (not inside functions unless circular imports or documented exceptions)?

**Database Conventions**: Do new tables/columns follow naming conventions (lower_case_snake, singular tables, `_at` suffix for datetime)? Are migrations static and revertable?

**RESTful Design**: Do endpoints follow REST conventions? Are HTTP methods and status codes appropriate?

**External Services**: Are external API calls (OpenAI, etc.) abstracted in service layers? Are API keys in environment variables?

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
# FastAPI Backend Structure (Domain-Driven)
src/
├── [domain]/
│   ├── router.py      # FastAPI routes
│   ├── schemas.py     # Pydantic models
│   ├── models.py      # SQLAlchemy/SQLModel DB models
│   ├── dependencies.py
│   ├── config.py      # domain-specific configs
│   ├── constants.py
│   ├── exceptions.py
│   ├── service.py
│   └── utils.py
├── config.py          # global configs
├── models.py          # global models
├── exceptions.py      # global exceptions
├── database.py        # DB connection
└── main.py

tests/
├── [domain]/          # Tests mirror source structure
│   ├── test_router.py
│   ├── test_service.py
│   └── test_integration.py
├── contract/          # API contract tests
└── conftest.py        # pytest fixtures
```

**Structure Decision**: [Document the selected structure and reference the real
directories captured above]

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
