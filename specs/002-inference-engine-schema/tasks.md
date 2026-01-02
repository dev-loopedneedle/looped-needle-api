# Implementation Tasks: Dynamic Audit Inference Engine

**Feature**: 002-inference-engine-schema  
**Branch**: `002-inference-engine-schema`  
**Date**: 2025-01-27  
**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

## Summary

This document breaks down the implementation into actionable, dependency-ordered tasks organized by user story. Each user story phase is independently testable and delivers incremental value.

**Total Tasks**: 143  
**User Stories**: 5 (2 P1, 2 P2, 1 P3)  
**MVP Scope**: Phases 1-3 (Setup + Foundational + Brand Profile Management) - 52 tasks

## Implementation Strategy

**MVP First**: Start with User Story 1 (Brand Profile Management) to establish the foundation. This enables brands to set up their profiles before any audit functionality is needed.

**Incremental Delivery**: Each user story phase is independently testable and can be deployed separately:
1. Phase 3: Brand Profile Management (US1) - Foundation
2. Phase 4: Criteria and Rules (US2) - Rule engine setup
3. Phase 5: Questionnaire (US3) - Audit scoping
4. Phase 6: Audit Item Generation (US4) - Core value proposition
5. Phase 7: Evidence Management (US5) - Compliance documentation

**Parallel Opportunities**: Within each phase, model creation, service implementation, and router setup can be parallelized where dependencies allow.

## Dependencies

**Story Completion Order**:
- US1 (Brand Profile) → US3 (Questionnaire) → US4 (Audit Generation)
- US2 (Criteria/Rules) → US4 (Audit Generation)
- US4 (Audit Generation) → US5 (Evidence)

**Critical Path**: US1 → US2 → US4 (core functionality)

## Phase 1: Setup

**Goal**: Initialize project structure and install dependencies

**Independent Test**: Project structure exists, dependencies installed, domain module created

### Tasks

- [X] T001 Install python-jexl dependency in pyproject.toml
- [X] T002 Create src/inference/ directory structure
- [X] T003 Create src/inference/__init__.py
- [X] T004 Create src/inference/constants.py with status enums
- [X] T005 Create src/inference/exceptions.py with domain exceptions
- [X] T006 Create src/inference/dependencies.py for domain dependencies
- [X] T007 Create tests/inference/ directory structure
- [X] T008 Create tests/inference/__init__.py

## Phase 2: Foundational

**Goal**: Database migration and base infrastructure

**Independent Test**: Migration runs successfully, database schema created, base utilities available

**Prerequisites**: Phase 1 complete

### Tasks

- [X] T009 Create Alembic migration file for inference schema in alembic/versions/[timestamp]_create_inference_schema.py
- [X] T010 Add brands table to migration with all columns, indexes, and constraints
- [X] T011 Add products table to migration with JSONB column and foreign key
- [X] T012 Add supply_chain_nodes table to migration with foreign key
- [X] T013 Add sustainability_criteria table to migration with unique code constraint
- [X] T014 Add criteria_rules table to migration with foreign key and priority index
- [X] T015 Add questionnaire_definitions table to migration with JSONB form_schema
- [X] T016 Add audit_instances table to migration with JSONB columns and status enum
- [X] T017 Add audit_items table to migration with foreign keys and status enum
- [X] T018 Add evidence_files table to migration with foreign key
- [X] T019 Add audit_item_evidence_links table to migration with composite unique constraint
- [X] T020 Add all GIN indexes for JSONB columns in migration
- [X] T021 Add all CHECK constraints for enums in migration
- [X] T022 Add soft delete indexes (deleted_at) to all tables in migration
- [X] T023 Create src/inference/utils.py with helper functions for soft delete checks

## Phase 3: User Story 1 - Brand Profile Management (P1)

**Goal**: Brands can create and manage profiles, products, and supply chain nodes

**Independent Test**: Create brand with products and supply chain nodes, retrieve and update data, verify soft delete prevention when referenced

**Prerequisites**: Phase 2 complete

**Acceptance Criteria**:
- ✅ Create brand profile with company details
- ✅ Add products with materials composition
- ✅ Define supply chain nodes
- ✅ Update brand information
- ✅ Soft delete prevention when referenced by audit instances

### Tasks

- [X] T024 [P] [US1] Create Brand SQLModel in src/inference/models.py with all fields and relationships
- [X] T025 [P] [US1] Create Product SQLModel in src/inference/models.py with JSONB materials_composition
- [X] T026 [P] [US1] Create SupplyChainNode SQLModel in src/inference/models.py
- [X] T027 [US1] Create BrandCreate schema in src/inference/schemas.py
- [X] T028 [US1] Create BrandUpdate schema in src/inference/schemas.py
- [X] T029 [US1] Create BrandResponse schema in src/inference/schemas.py
- [X] T030 [US1] Create ProductCreate schema in src/inference/schemas.py
- [X] T031 [US1] Create ProductResponse schema in src/inference/schemas.py
- [X] T032 [US1] Create SupplyChainNodeCreate schema in src/inference/schemas.py
- [X] T033 [US1] Create SupplyChainNodeResponse schema in src/inference/schemas.py
- [X] T034 [US1] Create BrandService.create_brand method in src/inference/service.py
- [X] T035 [US1] Create BrandService.get_brand method in src/inference/service.py
- [X] T036 [US1] Create BrandService.update_brand method in src/inference/service.py
- [X] T037 [US1] Create BrandService.delete_brand method in src/inference/service.py with referential integrity check
- [X] T038 [US1] Create BrandService.list_brands method in src/inference/service.py with pagination
- [X] T039 [US1] Create ProductService.create_product method in src/inference/service.py
- [X] T040 [US1] Create ProductService.get_products_by_brand method in src/inference/service.py
- [X] T041 [US1] Create SupplyChainNodeService.create_node method in src/inference/service.py
- [X] T042 [US1] Create SupplyChainNodeService.get_nodes_by_brand method in src/inference/service.py
- [X] T043 [US1] Create POST /api/v1/brands endpoint in src/inference/router.py
- [X] T044 [US1] Create GET /api/v1/brands endpoint in src/inference/router.py
- [X] T045 [US1] Create GET /api/v1/brands/{brand_id} endpoint in src/inference/router.py
- [X] T046 [US1] Create PUT /api/v1/brands/{brand_id} endpoint in src/inference/router.py
- [X] T047 [US1] Create DELETE /api/v1/brands/{brand_id} endpoint in src/inference/router.py
- [X] T048 [US1] Create POST /api/v1/brands/{brand_id}/products endpoint in src/inference/router.py
- [X] T049 [US1] Create GET /api/v1/brands/{brand_id}/products endpoint in src/inference/router.py
- [X] T050 [US1] Create POST /api/v1/brands/{brand_id}/supply-chain-nodes endpoint in src/inference/router.py
- [X] T051 [US1] Create GET /api/v1/brands/{brand_id}/supply-chain-nodes endpoint in src/inference/router.py
- [X] T052 [US1] Register inference router in src/main.py

## Phase 4: User Story 2 - Sustainability Criteria and Rules Definition (P1)

**Goal**: System administrators can define criteria and rules with JEXL expressions

**Independent Test**: Create criterion with rules, evaluate rules, update rules, verify rule evaluation with JEXL

**Prerequisites**: Phase 2 complete

**Acceptance Criteria**:
- ✅ Create sustainability criterion
- ✅ Create rule with JEXL condition expression
- ✅ Query rules by criterion ordered by priority
- ✅ Update rule condition expression
- ✅ Rule evaluation with JEXL library

### Tasks

- [X] T053 [P] [US2] Create SustainabilityCriterion SQLModel in src/inference/models.py
- [X] T054 [P] [US2] Create CriteriaRule SQLModel in src/inference/models.py
- [X] T055 [US2] Create CriterionCreate schema in src/inference/schemas.py
- [X] T056 [US2] Create CriterionResponse schema in src/inference/schemas.py
- [X] T057 [US2] Create RuleCreate schema in src/inference/schemas.py
- [X] T058 [US2] Create RuleUpdate schema in src/inference/schemas.py
- [X] T059 [US2] Create RuleResponse schema in src/inference/schemas.py
- [X] T060 [US2] Create RuleEvaluator class in src/inference/service.py with JEXL evaluation
- [X] T061 [US2] Implement RuleEvaluator.evaluate method with error handling in src/inference/service.py
- [X] T062 [US2] Create CriterionService.create_criterion method in src/inference/service.py
- [X] T063 [US2] Create CriterionService.get_criterion method in src/inference/service.py
- [X] T064 [US2] Create CriterionService.list_criteria method in src/inference/service.py with domain filter
- [X] T065 [US2] Create RuleService.create_rule method in src/inference/service.py
- [X] T066 [US2] Create RuleService.get_rules_by_criterion method in src/inference/service.py ordered by priority
- [X] T067 [US2] Create RuleService.update_rule method in src/inference/service.py
- [X] T068 [US2] Create POST /api/v1/criteria endpoint in src/inference/router.py
- [X] T069 [US2] Create GET /api/v1/criteria endpoint in src/inference/router.py
- [X] T070 [US2] Create GET /api/v1/criteria/{criterion_id} endpoint in src/inference/router.py
- [X] T071 [US2] Create POST /api/v1/criteria/{criterion_id}/rules endpoint in src/inference/router.py
- [X] T072 [US2] Create GET /api/v1/criteria/{criterion_id}/rules endpoint in src/inference/router.py
- [X] T073 [US2] Create GET /api/v1/rules/{rule_id} endpoint in src/inference/router.py
- [X] T074 [US2] Create PUT /api/v1/rules/{rule_id} endpoint in src/inference/router.py

## Phase 5: User Story 3 - Audit Scoping Questionnaire (P2)

**Goal**: Brands can answer scoping questionnaires when starting audits

**Independent Test**: Create questionnaire definition, create audit instance with responses, retrieve audit instance with responses

**Prerequisites**: Phase 3 complete (US1)

**Acceptance Criteria**:
- ✅ Create questionnaire definition with form schema
- ✅ Create audit instance with questionnaire responses
- ✅ Retrieve questionnaire definition
- ✅ Query active questionnaires
- ✅ Retrieve audit instance with scoping responses

### Tasks

- [X] T075 [P] [US3] Create QuestionnaireDefinition SQLModel in src/inference/models.py with JSONB form_schema
- [X] T076 [P] [US3] Create AuditInstance SQLModel in src/inference/models.py with JSONB columns
- [X] T077 [US3] Create QuestionnaireDefinitionCreate schema in src/inference/schemas.py
- [X] T078 [US3] Create QuestionnaireDefinitionResponse schema in src/inference/schemas.py
- [X] T079 [US3] Create AuditInstanceCreate schema in src/inference/schemas.py
- [X] T080 [US3] Create AuditInstanceUpdate schema in src/inference/schemas.py
- [X] T081 [US3] Create AuditInstanceResponse schema in src/inference/schemas.py
- [X] T082 [US3] Create QuestionnaireService.create_questionnaire method in src/inference/service.py
- [X] T083 [US3] Create QuestionnaireService.get_questionnaire method in src/inference/service.py
- [X] T084 [US3] Create QuestionnaireService.list_active_questionnaires method in src/inference/service.py
- [X] T085 [US3] Create AuditInstanceService.create_audit_instance method in src/inference/service.py with brand context snapshot
- [X] T086 [US3] Implement brand context snapshot capture in AuditInstanceService.create_audit_instance in src/inference/service.py
- [X] T087 [US3] Create AuditInstanceService.get_audit_instance method in src/inference/service.py
- [X] T088 [US3] Create AuditInstanceService.update_audit_instance_status method in src/inference/service.py with state transition validation
- [X] T089 [US3] Create state transition validation function in src/inference/utils.py
- [X] T090 [US3] Create POST /api/v1/questionnaires endpoint in src/inference/router.py
- [X] T091 [US3] Create GET /api/v1/questionnaires endpoint in src/inference/router.py with is_active filter
- [X] T092 [US3] Create GET /api/v1/questionnaires/{questionnaire_id} endpoint in src/inference/router.py
- [X] T093 [US3] Create POST /api/v1/audit-instances endpoint in src/inference/router.py
- [X] T094 [US3] Create GET /api/v1/audit-instances endpoint in src/inference/router.py
- [X] T095 [US3] Create GET /api/v1/audit-instances/{audit_instance_id} endpoint in src/inference/router.py
- [X] T096 [US3] Create PUT /api/v1/audit-instances/{audit_instance_id} endpoint in src/inference/router.py

## Phase 6: User Story 4 - Dynamic Audit Item Generation (P2)

**Goal**: System automatically generates audit items by evaluating rules against brand context

**Independent Test**: Trigger audit item generation, verify items created for matching criteria, verify highest priority rule selected, verify failed rules logged

**Prerequisites**: Phase 3 (US1), Phase 4 (US2), Phase 5 (US3) complete

**Acceptance Criteria**:
- ✅ Trigger audit item generation
- ✅ Evaluate all rules against brand context and questionnaire responses
- ✅ Create audit items for matching criteria
- ✅ Select highest priority rule per criterion
- ✅ Skip failed rules and log errors
- ✅ Preserve existing items with evidence during regeneration

### Tasks

- [X] T097 [P] [US4] Create AuditItem SQLModel in src/inference/models.py with all foreign keys
- [X] T098 [US4] Create AuditItemResponse schema in src/inference/schemas.py
- [X] T099 [US4] Create AuditItemUpdate schema in src/inference/schemas.py
- [X] T100 [US4] Create AuditItemGenerationResponse schema in src/inference/schemas.py
- [X] T101 [US4] Create AuditItemService.generate_audit_items method in src/inference/service.py
- [X] T102 [US4] Implement rule evaluation batch processing in AuditItemService.generate_audit_items in src/inference/service.py
- [X] T103 [US4] Implement highest priority rule selection per criterion in AuditItemService.generate_audit_items in src/inference/service.py
- [X] T104 [US4] Implement failed rule error logging in AuditItemService.generate_audit_items in src/inference/service.py
- [X] T105 [US4] Implement existing item preservation logic in AuditItemService.generate_audit_items in src/inference/service.py
- [X] T106 [US4] Create AuditItemService.get_audit_items_by_instance method in src/inference/service.py
- [X] T107 [US4] Create AuditItemService.update_audit_item method in src/inference/service.py with status transition validation
- [X] T108 [US4] Create audit item status transition validation function in src/inference/utils.py
- [X] T109 [US4] Create POST /api/v1/audit-instances/{audit_instance_id}/generate-items endpoint in src/inference/router.py
- [X] T110 [US4] Create GET /api/v1/audit-instances/{audit_instance_id}/items endpoint in src/inference/router.py
- [X] T111 [US4] Create GET /api/v1/audit-items/{audit_item_id} endpoint in src/inference/router.py
- [X] T112 [US4] Create PUT /api/v1/audit-items/{audit_item_id} endpoint in src/inference/router.py

## Phase 7: User Story 5 - Evidence Management and Linking (P3)

**Goal**: Brands can upload evidence files and link them to audit items

**Independent Test**: Upload evidence file, link to audit item, retrieve evidence by audit item, verify link status

**Prerequisites**: Phase 6 (US4) complete

**Acceptance Criteria**:
- ✅ Upload evidence file
- ✅ Link evidence file to audit item
- ✅ View evidence files for audit item
- ✅ Update evidence link status

### Tasks

- [ ] T113 [P] [US5] Create EvidenceFile SQLModel in src/inference/models.py
- [ ] T114 [P] [US5] Create AuditItemEvidenceLink SQLModel in src/inference/models.py
- [ ] T115 [US5] Create EvidenceFileCreate schema in src/inference/schemas.py
- [ ] T116 [US5] Create EvidenceFileResponse schema in src/inference/schemas.py
- [ ] T117 [US5] Create EvidenceLinkCreate schema in src/inference/schemas.py
- [ ] T118 [US5] Create EvidenceLinkUpdate schema in src/inference/schemas.py
- [ ] T119 [US5] Create EvidenceLinkResponse schema in src/inference/schemas.py
- [ ] T120 [US5] Create EvidenceService.upload_file method in src/inference/service.py with file storage
- [ ] T121 [US5] Create EvidenceService.get_file method in src/inference/service.py
- [ ] T122 [US5] Create EvidenceService.get_files_by_brand method in src/inference/service.py
- [ ] T123 [US5] Create EvidenceService.create_evidence_link method in src/inference/service.py
- [ ] T124 [US5] Create EvidenceService.get_evidence_links_by_item method in src/inference/service.py
- [ ] T125 [US5] Create EvidenceService.update_evidence_link_status method in src/inference/service.py
- [ ] T126 [US5] Create POST /api/v1/brands/{brand_id}/evidence endpoint in src/inference/router.py with file upload
- [ ] T127 [US5] Create GET /api/v1/brands/{brand_id}/evidence endpoint in src/inference/router.py
- [ ] T128 [US5] Create GET /api/v1/evidence/{evidence_file_id} endpoint in src/inference/router.py
- [ ] T129 [US5] Create POST /api/v1/audit-items/{audit_item_id}/evidence endpoint in src/inference/router.py
- [ ] T130 [US5] Create GET /api/v1/audit-items/{audit_item_id}/evidence endpoint in src/inference/router.py
- [ ] T131 [US5] Create PUT /api/v1/evidence-links/{link_id} endpoint in src/inference/router.py

## Phase 8: Polish & Cross-Cutting Concerns

**Goal**: Integration, error handling, performance optimizations

**Prerequisites**: All user story phases complete

### Tasks

- [X] T132 Add comprehensive error handling for invalid state transitions in src/inference/router.py
- [X] T133 Add referential integrity error handling for soft delete operations in src/inference/service.py
- [X] T134 Add request validation error handling in src/inference/router.py
- [X] T135 Add logging for audit item generation performance in src/inference/service.py
- [ ] T136 Optimize rule evaluation with expression caching in src/inference/service.py (optional optimization)
- [X] T137 Add database query optimization (eager loading) for audit items with criteria in src/inference/service.py
- [X] T138 Add pagination to all list endpoints in src/inference/router.py
- [X] T139 Add OpenAPI documentation tags and descriptions to all endpoints in src/inference/router.py
- [X] T140 Verify all endpoints return appropriate HTTP status codes in src/inference/router.py
- [X] T141 Add input validation for JSONB fields (materials_composition, form_schema) in src/inference/schemas.py
- [X] T142 Add database transaction handling for multi-step operations in src/inference/service.py
- [ ] T143 Add concurrent request handling tests for audit generation in tests/inference/test_integration.py (testing - skip for now)

## Parallel Execution Examples

### Phase 3 (US1) - Can parallelize:
- T024-T026: Model creation (different files, no dependencies)
- T027-T033: Schema creation (different schemas, no dependencies)
- T043-T051: Router endpoints (different endpoints, depend on services)

### Phase 4 (US2) - Can parallelize:
- T053-T054: Model creation
- T055-T059: Schema creation
- T068-T074: Router endpoints

### Phase 6 (US4) - Can parallelize:
- T101-T105: Service method implementations (different methods)
- T109-T112: Router endpoints

## Task Summary

| Phase | Tasks | User Story | Priority |
|-------|-------|------------|----------|
| Phase 1: Setup | 8 | - | - |
| Phase 2: Foundational | 15 | - | - |
| Phase 3: US1 | 29 | Brand Profile Management | P1 |
| Phase 4: US2 | 22 | Criteria & Rules | P1 |
| Phase 5: US3 | 22 | Questionnaire | P2 |
| Phase 6: US4 | 16 | Audit Generation | P2 |
| Phase 7: US5 | 19 | Evidence Management | P3 |
| Phase 8: Polish | 12 | Cross-cutting | - |
| **Total** | **143** | **5 stories** | - |

**MVP Scope (Phases 1-3)**: 52 tasks covering setup, database migration, and brand profile management

