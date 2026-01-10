# Feature Specification: Rules Engine for Audit Certification

**Feature Branch**: `004-rules-engine`  
**Created**: 2026-01-06  
**Status**: Draft  
**Input**: User description: "Rules engine for audits: admins define rules (draft/published/disabled) with safe match expressions over audit_data; rules produce evidence claims; generate and persist per-audit workflows listing required claims with traceability to matched rules."

## Clarifications

### Session 2026-01-06

- Q: Should workflow generation be automatic on audit creation, or manual trigger only? → A: Manual trigger only (user clicks "Generate Requirements")
- Q: What level of validation should be performed on rule expressions before allowing publication? → A: Syntax + type checking + test evaluation against sample data
- Q: When a workflow is regenerated, should it replace the existing workflow or create a new generation? → A: Create new generation (preserve history). Note: Workflow regeneration only applies to draft audits; published audits are immutable and cannot have workflows regenerated
- Q: Should rule codes be globally unique across all rules, or unique per code family? → A: Globally unique (no two rules can share the same code, even across different families)
- Q: What level of rule information should brand users see when viewing which rules triggered their evidence requirements? → A: Rule name and code only (transparency without exposing technical expression details)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Admin Creates and Publishes Rules (Priority: P1)

As a system administrator, I need to create rules that define when specific evidence requirements apply to audits, so that the system can automatically determine what evidence brands must provide based on their audit data.

**Why this priority**: Rules are the foundation of the certification engine. Without rules, no evidence requirements can be generated. This enables the core value proposition of automated requirement identification.

**Independent Test**: Can be fully tested by creating a draft rule with a matching expression and evidence claims, publishing it, and verifying it appears in the published rules list. Delivers immediate value by enabling rule-based certification logic.

**Acceptance Scenarios**:

1. **Given** I am a system administrator, **When** I create a new rule with a name, code, description, matching expression, and associated evidence claims, **Then** the rule is saved as DRAFT and I can view it in the rules list
2. **Given** a DRAFT rule exists, **When** I validate the expression against sample audit data, **Then** I see whether it matches and any validation errors
3. **Given** a DRAFT rule with a valid expression exists, **When** I publish the rule, **Then** it becomes PUBLISHED and is used for matching audits
4. **Given** a PUBLISHED rule exists, **When** I need to modify it, **Then** I can clone it to create a new DRAFT version while preserving the original published version

---

### User Story 2 - System Generates Evidence Requirements for Audits (Priority: P1)

As a brand user, I need the system to automatically determine what evidence I must provide for my audit based on the audit data I've entered, so that I know exactly what documentation to prepare.

**Why this priority**: This is the core value proposition - automatically generating personalized evidence requirements instead of requiring manual selection. This saves time and ensures completeness.

**Independent Test**: Can be fully tested by creating an audit with specific data, triggering workflow generation, and verifying that the correct evidence claims are listed based on matching published rules. Delivers value by automating requirement identification.

**Acceptance Scenarios**:

1. **Given** I have created an audit with product and material information, **When** I request workflow generation, **Then** the system evaluates published rules against my audit data and generates a list of required evidence claims
2. **Given** a workflow has been generated for my audit, **When** I view the workflow, **Then** I see all required evidence claims with their names, descriptions, categories, types, and which rules triggered each requirement (showing rule name and code for transparency)
3. **Given** I have a draft audit with a generated workflow, **When** I update my audit data and regenerate the workflow, **Then** the system creates a new generation with updated requirements based on the new data (preserving previous generations)
4. **Given** I have a published audit, **When** I attempt to regenerate its workflow, **Then** the system prevents regeneration because published audits are immutable

---

### User Story 3 - Admin Manages Evidence Claim Catalog (Priority: P2)

As a system administrator, I need to create and manage a catalog of evidence claims that can be attached to rules, so that I can reuse common evidence requirements across multiple rules.

**Why this priority**: Evidence claims are reusable building blocks for rules. While important, this can be implemented after core rule creation and workflow generation are working.

**Independent Test**: Can be fully tested by creating evidence claims with categories, types, and weights, then attaching them to rules. Delivers value by enabling efficient rule management.

**Acceptance Scenarios**:

1. **Given** I am a system administrator, **When** I create a new evidence claim with name, description, category, type, and weight, **Then** it is saved and available to attach to rules
2. **Given** evidence claims exist, **When** I attach them to a rule, **Then** those claims become required whenever that rule matches an audit

---

### Edge Cases

- What happens when a rule's expression fails to evaluate (syntax error, runtime error)? → System skips the rule, logs the error, and continues evaluating other rules
- What happens when multiple rules require the same evidence claim? → System creates one required claim entry but tracks all source rules for traceability
- What happens when a draft audit's data changes after workflow generation? → System can regenerate the workflow, creating a new generation with updated requirements (preserving previous generations)
- What happens when a published audit's data changes? → Published audits are immutable; workflow regeneration is not allowed
- What happens when a published rule is disabled? → Disabled rules are not evaluated for new workflow generations, but existing workflows preserve their historical requirements
- What happens when a rule's expression references audit data fields that don't exist? → Expression evaluator handles missing fields gracefully (returns empty dict/None), allowing rules to check for existence
- How does the system handle concurrent workflow generation requests for the same audit? → System ensures only one generation process runs at a time per audit

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow system administrators to create rules with name, code (globally unique identifier), description, and matching expression
- **FR-002**: System MUST support rule states: DRAFT (editable, not used for matching), PUBLISHED (immutable, used for matching), DISABLED (not used for matching)
- **FR-003**: System MUST validate rule expressions before allowing publication (syntax validation, type checking, and test evaluation against sample audit data to ensure expression returns boolean result)
- **FR-004**: System MUST allow cloning published rules to create new draft versions (preserving original published version for auditability)
- **FR-005**: System MUST allow system administrators to create evidence claims with name, description, category, type, and weight (0-1)
- **FR-006**: System MUST allow attaching evidence claims to rules (many-to-many relationship)
- **FR-007**: System MUST evaluate all PUBLISHED rules against audit data when generating workflows
- **FR-008**: System MUST generate audit workflows containing required evidence claims based on matching rules
- **FR-009**: System MUST track which rules triggered each required evidence claim (traceability) and display rule name and code to brand users (without exposing rule expressions)
- **FR-010**: System MUST handle rule evaluation errors gracefully (skip failed rules, log errors, continue with valid rules)
- **FR-011**: System MUST allow brand users to view required evidence claims for their audit workflows
- **FR-012**: System MUST require explicit user action to trigger workflow generation (manual trigger only, not automatic on audit creation)
- **FR-013**: System MUST support regenerating workflows for draft audits when audit data changes (manual trigger, creates new generation preserving history)
- **FR-014**: System MUST prevent workflow regeneration for published audits (published audits are immutable)
- **FR-015**: System MUST preserve audit data snapshots used for workflow generation (for auditability)
- **FR-016**: System MUST support evidence claim categories: ENVIRONMENT, SUSTAINABILITY, SOCIAL, GOVERNANCE, TRACEABILITY, OTHER
- **FR-017**: System MUST support evidence claim types: CERTIFICATE, INVOICE, QUESTIONNAIRE, PHOTO, REPORT, OTHER

### Key Entities *(include if feature involves data)*

- **Rule**: Represents a matching condition that determines when evidence requirements apply. Key attributes: code (globally unique stable identifier), version, name, description, state (DRAFT/PUBLISHED/DISABLED), expression (matching logic), created by admin user. Relationships: has many Evidence Claims, evaluated against Audits.

- **Evidence Claim**: Represents a reusable evidence requirement definition. Key attributes: name, description, category (enum), type (enum), weight (0-1). Relationships: attached to many Rules, required in Audit Workflows.

- **Audit Workflow**: Represents a generated set of evidence requirements for a specific audit. Key attributes: generation number, status, generated timestamp, audit data snapshot. Relationships: belongs to Audit, contains Required Claims, tracks Rule Matches.

- **Required Claim**: Represents a concrete evidence requirement instance in a workflow. Key attributes: status (REQUIRED/SATISFIED), links to Evidence Claim definition. Relationships: belongs to Audit Workflow, has sources (which rules triggered it).

- **Rule Match**: Represents the result of evaluating a rule against audit data. Key attributes: matched (boolean), error message (if evaluation failed), rule code and version used. Relationships: belongs to Audit Workflow, references Rule.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: System administrators can create and publish a rule in under 5 minutes
- **SC-002**: Workflow generation completes within 10 seconds for audits with up to 100 published rules
- **SC-003**: System correctly identifies required evidence claims for 95% of audits based on matching rules
- **SC-004**: Brand users can view their required evidence claims within 2 seconds of workflow generation
- **SC-005**: System handles rule evaluation errors without blocking workflow generation (failed rules are skipped, errors logged)
- **SC-006**: System maintains complete traceability showing which rules triggered each evidence requirement (100% accuracy)
