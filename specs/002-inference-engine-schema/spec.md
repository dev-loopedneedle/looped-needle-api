# Feature Specification: Dynamic Audit Inference Engine

**Feature Branch**: `002-inference-engine-schema`  
**Created**: 2025-01-27  
**Status**: Draft  
**Input**: User description: "Scaffolding the Database Schema (PostgreSQL) and Core Types for the 'Inference Engine' module. We are building a dynamic audit system where Brands define their profile (Context), Admins define Criteria (Requirements) and Rules (JEXL Logic strings), and when a brand starts an audit, they answer a 'Scoping Questionnaire.' The system combines Brand Context + Questionnaire Answers -> runs them against JEXL Rules -> generates a specific list of AuditItems (The Checklist)."

## Clarifications

### Session 2025-01-27

- Q: What are the allowed state transitions for audit instances? → A: Allow all forward transitions (can skip REVIEWING), prevent backward transitions (cannot revert CERTIFIED)
- Q: How should the system handle rule evaluation failures (invalid condition expressions)? → A: Skip failed rules, log errors, continue with valid rules (partial success)
- Q: How should the system handle data deletion and referential integrity? → A: Soft delete with cascade prevention (mark as deleted, prevent deletion if referenced by audit items)
- Q: What happens when audit items are regenerated (e.g., after rules change)? → A: Regeneration creates new items, preserves existing items with evidence (additive approach)
- Q: What are the audit item status values and transitions? → A: MISSING_EVIDENCE → EVIDENCE_PROVIDED → UNDER_REVIEW → ACCEPTED/REJECTED

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Brand Profile Management (Priority: P1)

As a brand administrator, I need to define and manage my brand's profile including company details, products, and supply chain information so that the system can use this context when generating audit requirements.

**Why this priority**: Brand context is foundational input required for all audit generation. Without brand profiles, no audits can be created or requirements inferred.

**Independent Test**: Can be fully tested by creating brand profiles with various configurations (company size, markets, products, supply chain nodes) and verifying the data is stored correctly and can be retrieved. Delivers immediate value by enabling brands to set up their organizational context.

**Acceptance Scenarios**:

1. **Given** I am a brand administrator, **When** I create a brand profile with company details (name, registration country, company size, target markets), **Then** the profile is saved and I can retrieve it later
2. **Given** a brand profile exists, **When** I add product information including materials composition and manufacturing processes, **Then** the products are associated with the brand and stored with all details
3. **Given** a brand profile exists, **When** I define supply chain nodes with roles, countries, and tier levels, **Then** the supply chain information is stored and linked to the brand
4. **Given** brand data exists, **When** I update any brand information, **Then** the changes are persisted and reflected in subsequent retrievals

---

### User Story 2 - Sustainability Criteria and Rules Definition (Priority: P1)

As a system administrator, I need to define sustainability criteria and create rules that determine when each criterion applies to an audit so that the system can automatically generate relevant audit requirements based on context.

**Why this priority**: Criteria and rules are the "brain" of the inference engine. Without these definitions, the system cannot determine which audit items should be included for any given brand and audit scope.

**Independent Test**: Can be fully tested by creating criteria with associated rules containing condition expressions, and verifying they are stored correctly and can be evaluated. Delivers value by enabling the rule-based inference logic.

**Acceptance Scenarios**:

1. **Given** I am a system administrator, **When** I create a sustainability criterion with code, name, description, and domain (Social/Environmental/Governance), **Then** the criterion is saved and can be referenced by rules
2. **Given** a sustainability criterion exists, **When** I create a rule with a condition expression that references brand context and audit scope, **Then** the rule is linked to the criterion and stored with its priority
3. **Given** multiple rules exist for a criterion, **When** I query rules by criterion, **Then** I receive all associated rules ordered by priority
4. **Given** rules exist, **When** I update a rule's condition expression or priority, **Then** the changes are persisted and affect future audit generation

---

### User Story 3 - Audit Scoping Questionnaire (Priority: P2)

As a brand administrator, I need to answer a scoping questionnaire when starting an audit so that the system understands the specific scope and requirements for this audit instance.

**Why this priority**: Questionnaire responses provide the audit-specific context needed to determine which criteria apply. This is required input for audit generation.

**Independent Test**: Can be fully tested by creating questionnaire definitions, answering questions, and verifying responses are stored correctly. Delivers value by capturing audit-specific requirements.

**Acceptance Scenarios**:

1. **Given** I am starting a new audit, **When** I answer the scoping questionnaire (audit scope type, supply chain depth, production season, wet processing, new suppliers), **Then** my responses are saved and associated with the audit instance
2. **Given** a questionnaire definition exists, **When** I retrieve it, **Then** I see the complete form structure with all questions, options, and descriptions
3. **Given** multiple questionnaire definitions exist, **When** I query active questionnaires, **Then** I receive only those marked as active
4. **Given** questionnaire responses exist, **When** I retrieve an audit instance, **Then** I can see the complete scoping responses that were provided

---

### User Story 4 - Dynamic Audit Item Generation (Priority: P2)

As a brand administrator, I need the system to automatically generate a customized checklist of audit items based on my brand context and audit scope so that I know exactly what evidence I need to provide for certification.

**Why this priority**: This is the core value proposition - automatically generating relevant audit requirements instead of requiring manual selection. This saves time and ensures completeness.

**Independent Test**: Can be fully tested by creating an audit instance with brand context and questionnaire responses, triggering the generation process, and verifying that appropriate audit items are created based on matching rules. Delivers value by automating requirement identification.

**Acceptance Scenarios**:

1. **Given** I have created an audit instance with brand context and questionnaire responses, **When** I trigger audit item generation, **Then** the system evaluates all rules against my context and creates audit items for matching criteria
2. **Given** audit items are generated, **When** I view the audit checklist, **Then** I see all items with their associated criteria and the rule that triggered each item
3. **Given** multiple rules match the same criterion, **When** audit items are generated, **Then** only one audit item is created per criterion (highest priority rule determines the trigger)
4. **Given** my brand context changes after audit creation, **When** I view the audit, **Then** I see the snapshot of context that was used at audit creation time (not current context)

---

### User Story 5 - Evidence Management and Linking (Priority: P3)

As a brand administrator, I need to upload evidence files and link them to specific audit items so that I can provide proof of compliance for each requirement.

**Why this priority**: Evidence linking enables brands to demonstrate compliance. While important, this can be implemented after core audit generation is working.

**Independent Test**: Can be fully tested by uploading files, linking them to audit items, and verifying the associations are stored correctly. Delivers value by enabling compliance documentation.

**Acceptance Scenarios**:

1. **Given** I am a brand administrator, **When** I upload an evidence file, **Then** the file is stored and associated with my brand, and I receive confirmation with file details
2. **Given** evidence files and audit items exist, **When** I link a file to an audit item, **Then** the association is created and I can see which files support each audit item
3. **Given** evidence is linked to audit items, **When** I view an audit item, **Then** I see all associated evidence files and their status (pending/accepted/rejected)
4. **Given** multiple evidence files are linked to an audit item, **When** I query evidence by audit item, **Then** I receive all associated files with their current status

---

### Edge Cases

- What happens when a brand has no products defined but starts an audit?
- How does the system handle questionnaire responses that don't match expected values?
- What happens when multiple rules with different priorities match the same criterion?
- How does the system handle brand context updates after audit creation? (Should use snapshot)
- What happens when a rule's condition expression is invalid or cannot be evaluated? (System skips the rule, logs an error, and continues with valid rules)
- How does the system handle very large numbers of rules (performance considerations)?
- What happens when a criterion is deleted but rules still reference it? (Deletion is prevented if referenced by audit items; soft delete allowed if not referenced)
- How does the system handle concurrent audit generation requests for the same brand?
- What happens when audit items are regenerated after rules or criteria change? (New items are created, existing items with evidence are preserved)
- What happens when evidence files are deleted but links still exist? (Deletion is prevented if linked to audit items; soft delete allowed if not linked)
- How does the system handle audit instances with missing or incomplete questionnaire responses?
- What happens when attempting to transition an audit instance to an invalid state (e.g., reverting CERTIFIED to IN_PROGRESS)? (Transition is rejected with error)
- What happens when attempting to transition an audit item to an invalid state (e.g., reverting ACCEPTED to MISSING_EVIDENCE)? (Transition is rejected with error)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow brands to create and manage brand profiles with company details (name, registration country, company size, target markets)
- **FR-002**: System MUST allow brands to define products associated with their brand, including materials composition (complex blends) and manufacturing processes
- **FR-003**: System MUST allow brands to define supply chain nodes with role, country, and tier level information
- **FR-004**: System MUST allow system administrators to create sustainability criteria with unique codes, names, descriptions, and domain classifications (Social/Environmental/Governance)
- **FR-005**: System MUST allow system administrators to create rules linked to criteria, with condition expressions and priority values
- **FR-006**: System MUST store condition expressions as text strings that can be evaluated using rule evaluation logic
- **FR-007**: System MUST allow system administrators to create questionnaire definitions with form schemas stored as structured data
- **FR-008**: System MUST support marking questionnaire definitions as active or inactive
- **FR-009**: System MUST allow brands to create audit instances linked to their brand and a questionnaire definition
- **FR-010**: System MUST store questionnaire responses (scoping responses) as structured data associated with each audit instance
- **FR-011**: System MUST capture a snapshot of brand context (brand profile, products, supply chain) at the time of audit instance creation
- **FR-012**: System MUST support audit instance status tracking (IN_PROGRESS, REVIEWING, CERTIFIED) with forward-only transitions (can transition from IN_PROGRESS to REVIEWING or CERTIFIED, from REVIEWING to CERTIFIED, but cannot revert CERTIFIED or REVIEWING to previous states)
- **FR-013**: System MUST automatically generate audit items by evaluating rules against combined brand context and questionnaire responses, skipping rules that fail to evaluate and logging errors for failed rule evaluations
- **FR-014**: System MUST create one audit item per matching criterion, tracking which rule triggered the item creation
- **FR-027**: System MUST support regeneration of audit items, creating new items for newly matching criteria while preserving existing audit items that have evidence or comments
- **FR-015**: System MUST support audit item status tracking with values: MISSING_EVIDENCE (default), EVIDENCE_PROVIDED, UNDER_REVIEW, ACCEPTED, REJECTED, with forward-only transitions (cannot revert ACCEPTED or REJECTED)
- **FR-016**: System MUST allow auditors to add comments to audit items
- **FR-017**: System MUST allow brands to upload evidence files associated with their brand
- **FR-018**: System MUST support linking evidence files to audit items with status tracking (PENDING, ACCEPTED, REJECTED)
- **FR-019**: System MUST support multiple evidence files linked to a single audit item
- **FR-020**: System MUST support querying audit items by audit instance
- **FR-021**: System MUST support querying evidence files by audit item
- **FR-022**: System MUST use unique identifiers (UUIDs) for all entities
- **FR-023**: System MUST store timestamps for creation and modification of entities
- **FR-024**: System MUST validate all data before storage to ensure referential integrity
- **FR-025**: System MUST prevent deletion of entities (criteria, rules, brands, products) that are referenced by audit items, preserving audit trail integrity
- **FR-026**: System MUST support soft deletion (marking as deleted/inactive) for entities that are not referenced by audit items, allowing cleanup while preserving historical references

### Key Entities *(include if feature involves data)*

- **Brand**: Represents an organization seeking certification. Key attributes: unique identifier, name, registration country, company size (Micro/SME/Large), target markets (array), creation timestamp. Relationships: has many Products, has many SupplyChainNodes, has many AuditInstances.

- **Product**: Represents a product manufactured or sold by a brand. Key attributes: unique identifier, brand reference, name, category, materials composition (structured data with material types and percentages), manufacturing processes (array). Relationships: belongs to Brand.

- **SupplyChainNode**: Represents a node in the brand's supply chain. Key attributes: unique identifier, brand reference, role (e.g., CutAndSew, FabricMill), country, tier level (integer). Relationships: belongs to Brand.

- **SustainabilityCriterion**: Represents a master requirement that may apply to audits. Key attributes: unique identifier, code (unique), name, description, domain (Social/Environmental/Governance). Relationships: has many CriteriaRules.

- **CriteriaRule**: Represents a logic condition that determines when a criterion applies. Key attributes: unique identifier, criterion reference, rule name, condition expression (text string for evaluation), priority (integer). Relationships: belongs to SustainabilityCriterion.

- **QuestionnaireDefinition**: Represents a form schema for scoping questionnaires. Key attributes: unique identifier, name, form schema (structured data), active status. Relationships: referenced by AuditInstances.

- **AuditInstance**: Represents a specific audit execution. Key attributes: unique identifier, brand reference, questionnaire definition reference, status (IN_PROGRESS/REVIEWING/CERTIFIED), scoping responses (structured data), brand context snapshot (structured data), overall score (numeric). Relationships: belongs to Brand, references QuestionnaireDefinition, has many AuditItems.

- **AuditItem**: Represents a single requirement in an audit checklist. Key attributes: unique identifier, audit instance reference, criterion reference, triggered rule reference, status (defaults to MISSING_EVIDENCE, possible values: MISSING_EVIDENCE, EVIDENCE_PROVIDED, UNDER_REVIEW, ACCEPTED, REJECTED), auditor comments. Relationships: belongs to AuditInstance, references SustainabilityCriterion and CriteriaRule, has many EvidenceLinks.

- **EvidenceFile**: Represents an uploaded evidence document. Key attributes: unique identifier, brand reference, file path, file name, upload timestamp. Relationships: belongs to Brand, has many EvidenceLinks.

- **AuditItemEvidenceLink**: Represents the association between an audit item and evidence file. Key attributes: unique identifier, audit item reference, evidence file reference, status (PENDING/ACCEPTED/REJECTED). Relationships: belongs to AuditItem and EvidenceFile.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Brand profile creation completes successfully within 500 milliseconds, 95% of the time
- **SC-002**: Product and supply chain data can be added to brand profiles within 300 milliseconds per item, 95% of the time
- **SC-003**: Sustainability criteria and rules can be created and retrieved within 200 milliseconds, 95% of the time
- **SC-004**: Audit instance creation with questionnaire responses completes within 1 second, 95% of the time
- **SC-005**: Audit item generation for an audit instance completes within 5 seconds for datasets with up to 1000 rules, 95% of the time
- **SC-006**: System can handle 50 concurrent audit generation requests without errors or performance degradation
- **SC-007**: Evidence file upload completes within 2 seconds for files up to 10MB, 95% of the time
- **SC-008**: Evidence linking to audit items completes within 300 milliseconds, 95% of the time
- **SC-009**: Querying audit items for an audit instance returns results within 500 milliseconds for audits with up to 200 items, 95% of the time
- **SC-010**: All data operations maintain referential integrity, with 100% accuracy for foreign key relationships
- **SC-011**: Brand context snapshots accurately preserve the state of brand data at audit creation time, 100% of the time
- **SC-012**: Rule evaluation correctly identifies matching criteria based on condition expressions, with 100% accuracy for valid expressions

## Assumptions

- PostgreSQL database is available and supports UUID, JSONB, and array data types
- Brand administrators have appropriate permissions to manage their own brand data
- System administrators have appropriate permissions to manage criteria and rules
- Questionnaire form schemas follow a consistent structure that can be stored as structured data
- Condition expressions in rules use a standard evaluation syntax (JEXL) that can be processed by the system
- Brand context snapshots are deep copies that preserve the state at audit creation time
- Evidence files are stored in a file system or object storage accessible to the application
- File paths in evidence files are relative to a configured base storage location
- Audit item generation is triggered explicitly (not automatically on audit creation)
- Multiple rules matching the same criterion result in a single audit item (highest priority rule determines the trigger)
- Invalid condition expressions in rules will cause rule evaluation to fail gracefully without blocking audit generation (failed rules are skipped, errors are logged, and generation continues with valid rules)
- The system will handle concurrent modifications to brand data and audit instances appropriately
- Overall score for audit instances may be calculated later and is optional at creation time
- Auditor comments can be added after audit item creation and may be empty initially
- Entities referenced by audit items cannot be hard deleted to preserve audit trail integrity; soft deletion (marking as inactive/deleted) is supported for entities not referenced by audit items
- Audit item regeneration creates new items for newly matching criteria while preserving existing items that have evidence or comments, maintaining audit history

