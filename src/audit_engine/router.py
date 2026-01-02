"""Audit engine domain router."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.audit_engine.dependencies import get_audit_engine_db
from src.audit_engine.schemas import (
    AuditInstanceCreate,
    AuditInstanceListQuery,
    AuditInstanceListResponse,
    AuditInstanceResponse,
    AuditInstanceUpdate,
    AuditItemGenerationResponse,
    AuditItemListResponse,
    AuditItemResponse,
    AuditItemUpdate,
    BrandCreate,
    BrandListQuery,
    BrandListResponse,
    BrandResponse,
    BrandUpdate,
    CriterionCreate,
    CriterionListQuery,
    CriterionListResponse,
    CriterionResponse,
    ProductCreate,
    ProductResponse,
    QuestionnaireDefinitionCreate,
    QuestionnaireDefinitionResponse,
    QuestionnaireListQuery,
    QuestionnaireListResponse,
    RuleCreate,
    RuleListResponse,
    RuleResponse,
    RuleUpdate,
    SupplyChainNodeCreate,
    SupplyChainNodeResponse,
)
from src.audit_engine.service import (
    AuditInstanceService,
    AuditItemService,
    BrandService,
    CriterionService,
    ProductService,
    QuestionnaireService,
    RuleService,
    SupplyChainNodeService,
)

router = APIRouter(prefix="/api/v1", tags=["audit-engine"])
logger = logging.getLogger(__name__)


def _get_request_id(request: Request) -> str | None:
    """Get request ID from request state."""
    return getattr(request.state, "request_id", None)


# Brand endpoints
@router.post(
    "/brands",
    response_model=BrandResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create brand",
    description="Create a new brand profile with company details",
)
async def create_brand(
    request: Request,
    brand_data: BrandCreate,
    db: AsyncSession = Depends(get_audit_engine_db),
) -> BrandResponse:
    """Create a new brand."""
    request_id = _get_request_id(request)
    logger.info(f"Creating brand: name={brand_data.name}", extra={"request_id": request_id})
    brand = await BrandService.create_brand(db, brand_data)
    return BrandResponse.model_validate(brand)


@router.get(
    "/brands",
    response_model=BrandListResponse,
    summary="List brands",
    description="Retrieve a paginated list of brands",
)
async def list_brands(
    request: Request,
    limit: int = Query(default=20, ge=1, le=50, description="Maximum number of records to return"),
    offset: int = Query(default=0, ge=0, description="Number of records to skip"),
    db: AsyncSession = Depends(get_audit_engine_db),
) -> BrandListResponse:
    """List brands with pagination."""
    request_id = _get_request_id(request)
    logger.info(f"Listing brands: limit={limit}, offset={offset}", extra={"request_id": request_id})
    query = BrandListQuery(limit=limit, offset=offset)
    brands, total = await BrandService.list_brands(db, query)
    return BrandListResponse(
        items=[BrandResponse.model_validate(brand) for brand in brands],
        total=total,
        limit=query.limit,
        offset=query.offset,
    )


@router.get(
    "/brands/{brand_id}",
    response_model=BrandResponse,
    summary="Get brand",
    description="Retrieve a specific brand by ID",
)
async def get_brand(
    request: Request,
    brand_id: UUID,
    db: AsyncSession = Depends(get_audit_engine_db),
) -> BrandResponse:
    """Get brand by ID."""
    request_id = _get_request_id(request)
    logger.info(f"Getting brand: id={brand_id}", extra={"request_id": request_id})
    brand = await BrandService.get_brand(db, brand_id)
    return BrandResponse.model_validate(brand)


@router.put(
    "/brands/{brand_id}",
    response_model=BrandResponse,
    summary="Update brand",
    description="Update an existing brand profile",
)
async def update_brand(
    request: Request,
    brand_id: UUID,
    brand_data: BrandUpdate,
    db: AsyncSession = Depends(get_audit_engine_db),
) -> BrandResponse:
    """Update brand."""
    request_id = _get_request_id(request)
    logger.info(f"Updating brand: id={brand_id}", extra={"request_id": request_id})
    brand = await BrandService.update_brand(db, brand_id, brand_data)
    return BrandResponse.model_validate(brand)


@router.delete(
    "/brands/{brand_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete brand",
    description="Soft delete a brand (if not referenced by audit instances)",
)
async def delete_brand(
    request: Request,
    brand_id: UUID,
    db: AsyncSession = Depends(get_audit_engine_db),
) -> None:
    """Delete brand (soft delete)."""
    request_id = _get_request_id(request)
    logger.info(f"Deleting brand: id={brand_id}", extra={"request_id": request_id})
    await BrandService.delete_brand(db, brand_id)


# Product endpoints
@router.post(
    "/brands/{brand_id}/products",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create product",
    description="Create a new product for a brand",
)
async def create_product(
    request: Request,
    brand_id: UUID,
    product_data: ProductCreate,
    db: AsyncSession = Depends(get_audit_engine_db),
) -> ProductResponse:
    """Create a new product."""
    request_id = _get_request_id(request)
    logger.info(
        f"Creating product for brand: brand_id={brand_id}", extra={"request_id": request_id}
    )
    product = await ProductService.create_product(db, brand_id, product_data)
    return ProductResponse.model_validate(product)


@router.get(
    "/brands/{brand_id}/products",
    response_model=list[ProductResponse],
    summary="List products",
    description="Retrieve all products for a brand",
)
async def list_products(
    request: Request,
    brand_id: UUID,
    db: AsyncSession = Depends(get_audit_engine_db),
) -> list[ProductResponse]:
    """List products for a brand."""
    request_id = _get_request_id(request)
    logger.info(
        f"Listing products for brand: brand_id={brand_id}", extra={"request_id": request_id}
    )
    products = await ProductService.get_products_by_brand(db, brand_id)
    return [ProductResponse.model_validate(product) for product in products]


# Supply Chain Node endpoints
@router.post(
    "/brands/{brand_id}/supply-chain-nodes",
    response_model=SupplyChainNodeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create supply chain node",
    description="Create a new supply chain node for a brand",
)
async def create_supply_chain_node(
    request: Request,
    brand_id: UUID,
    node_data: SupplyChainNodeCreate,
    db: AsyncSession = Depends(get_audit_engine_db),
) -> SupplyChainNodeResponse:
    """Create a new supply chain node."""
    request_id = _get_request_id(request)
    logger.info(
        f"Creating supply chain node for brand: brand_id={brand_id}",
        extra={"request_id": request_id},
    )
    node = await SupplyChainNodeService.create_node(db, brand_id, node_data)
    return SupplyChainNodeResponse.model_validate(node)


@router.get(
    "/brands/{brand_id}/supply-chain-nodes",
    response_model=list[SupplyChainNodeResponse],
    summary="List supply chain nodes",
    description="Retrieve all supply chain nodes for a brand",
)
async def list_supply_chain_nodes(
    request: Request,
    brand_id: UUID,
    db: AsyncSession = Depends(get_audit_engine_db),
) -> list[SupplyChainNodeResponse]:
    """List supply chain nodes for a brand."""
    request_id = _get_request_id(request)
    logger.info(
        f"Listing supply chain nodes for brand: brand_id={brand_id}",
        extra={"request_id": request_id},
    )
    nodes = await SupplyChainNodeService.get_nodes_by_brand(db, brand_id)
    return [SupplyChainNodeResponse.model_validate(node) for node in nodes]


# Criterion endpoints
@router.post(
    "/criteria",
    response_model=CriterionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create criterion",
    description="Create a new sustainability criterion",
)
async def create_criterion(
    request: Request,
    criterion_data: CriterionCreate,
    db: AsyncSession = Depends(get_audit_engine_db),
) -> CriterionResponse:
    """Create a new sustainability criterion."""
    request_id = _get_request_id(request)
    logger.info(f"Creating criterion: code={criterion_data.code}", extra={"request_id": request_id})
    criterion = await CriterionService.create_criterion(db, criterion_data)
    return CriterionResponse.model_validate(criterion)


@router.get(
    "/criteria",
    response_model=CriterionListResponse,
    summary="List criteria",
    description="Retrieve a paginated list of sustainability criteria",
)
async def list_criteria(
    request: Request,
    domain: str | None = Query(
        None, description="Filter by domain (Social, Environmental, Governance)"
    ),
    limit: int = Query(default=20, ge=1, le=50, description="Maximum number of records to return"),
    offset: int = Query(default=0, ge=0, description="Number of records to skip"),
    db: AsyncSession = Depends(get_audit_engine_db),
) -> CriterionListResponse:
    """List criteria with pagination."""
    request_id = _get_request_id(request)
    logger.info(
        f"Listing criteria: domain={domain}, limit={limit}, offset={offset}",
        extra={"request_id": request_id},
    )
    from src.audit_engine.constants import SustainabilityDomain

    query = CriterionListQuery(
        domain=SustainabilityDomain(domain) if domain else None,
        limit=limit,
        offset=offset,
    )
    criteria, total = await CriterionService.list_criteria(db, query)
    return CriterionListResponse(
        items=[CriterionResponse.model_validate(criterion) for criterion in criteria],
        total=total,
        limit=query.limit,
        offset=query.offset,
    )


@router.get(
    "/criteria/{criterion_id}",
    response_model=CriterionResponse,
    summary="Get criterion",
    description="Retrieve a specific criterion by ID",
)
async def get_criterion(
    request: Request,
    criterion_id: UUID,
    db: AsyncSession = Depends(get_audit_engine_db),
) -> CriterionResponse:
    """Get criterion by ID."""
    request_id = _get_request_id(request)
    logger.info(f"Getting criterion: id={criterion_id}", extra={"request_id": request_id})
    criterion = await CriterionService.get_criterion(db, criterion_id)
    return CriterionResponse.model_validate(criterion)


# Rule endpoints
@router.post(
    "/criteria/{criterion_id}/rules",
    response_model=RuleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create rule",
    description="Create a new rule for a criterion",
)
async def create_rule(
    request: Request,
    criterion_id: UUID,
    rule_data: RuleCreate,
    db: AsyncSession = Depends(get_audit_engine_db),
) -> RuleResponse:
    """Create a new rule for a criterion."""
    request_id = _get_request_id(request)
    logger.info(
        f"Creating rule for criterion: criterion_id={criterion_id}",
        extra={"request_id": request_id},
    )
    rule = await RuleService.create_rule(db, criterion_id, rule_data)
    return RuleResponse.model_validate(rule)


@router.get(
    "/criteria/{criterion_id}/rules",
    response_model=RuleListResponse,
    summary="List rules",
    description="Retrieve all rules for a criterion, ordered by priority",
)
async def list_rules(
    request: Request,
    criterion_id: UUID,
    db: AsyncSession = Depends(get_audit_engine_db),
) -> RuleListResponse:
    """List rules for a criterion."""
    request_id = _get_request_id(request)
    logger.info(
        f"Listing rules for criterion: criterion_id={criterion_id}",
        extra={"request_id": request_id},
    )
    rules = await RuleService.get_rules_by_criterion(db, criterion_id)
    return RuleListResponse(
        items=[RuleResponse.model_validate(rule) for rule in rules],
        total=len(rules),
    )


@router.get(
    "/rules/{rule_id}",
    response_model=RuleResponse,
    summary="Get rule",
    description="Retrieve a specific rule by ID",
)
async def get_rule(
    request: Request,
    rule_id: UUID,
    db: AsyncSession = Depends(get_audit_engine_db),
) -> RuleResponse:
    """Get rule by ID."""
    request_id = _get_request_id(request)
    logger.info(f"Getting rule: id={rule_id}", extra={"request_id": request_id})
    rule = await RuleService.get_rule(db, rule_id)
    return RuleResponse.model_validate(rule)


@router.put(
    "/rules/{rule_id}",
    response_model=RuleResponse,
    summary="Update rule",
    description="Update an existing rule",
)
async def update_rule(
    request: Request,
    rule_id: UUID,
    rule_data: RuleUpdate,
    db: AsyncSession = Depends(get_audit_engine_db),
) -> RuleResponse:
    """Update rule."""
    request_id = _get_request_id(request)
    logger.info(f"Updating rule: id={rule_id}", extra={"request_id": request_id})
    rule = await RuleService.update_rule(db, rule_id, rule_data)
    return RuleResponse.model_validate(rule)


# Questionnaire endpoints
@router.post(
    "/questionnaires",
    response_model=QuestionnaireDefinitionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create questionnaire",
    description="Create a new questionnaire definition",
)
async def create_questionnaire(
    request: Request,
    questionnaire_data: QuestionnaireDefinitionCreate,
    db: AsyncSession = Depends(get_audit_engine_db),
) -> QuestionnaireDefinitionResponse:
    """Create a new questionnaire definition."""
    request_id = _get_request_id(request)
    logger.info(
        f"Creating questionnaire: name={questionnaire_data.name}", extra={"request_id": request_id}
    )
    questionnaire = await QuestionnaireService.create_questionnaire(db, questionnaire_data)
    return QuestionnaireDefinitionResponse.model_validate(questionnaire)


@router.get(
    "/questionnaires",
    response_model=QuestionnaireListResponse,
    summary="List questionnaires",
    description="Retrieve a paginated list of questionnaire definitions",
)
async def list_questionnaires(
    request: Request,
    is_active: bool | None = Query(None, description="Filter by active status"),
    limit: int = Query(default=20, ge=1, le=50, description="Maximum number of records to return"),
    offset: int = Query(default=0, ge=0, description="Number of records to skip"),
    db: AsyncSession = Depends(get_audit_engine_db),
) -> QuestionnaireListResponse:
    """List questionnaires with pagination."""
    request_id = _get_request_id(request)
    logger.info(
        f"Listing questionnaires: is_active={is_active}, limit={limit}, offset={offset}",
        extra={"request_id": request_id},
    )
    query = QuestionnaireListQuery(is_active=is_active, limit=limit, offset=offset)
    questionnaires, total = await QuestionnaireService.list_active_questionnaires(db, query)
    return QuestionnaireListResponse(
        items=[QuestionnaireDefinitionResponse.model_validate(q) for q in questionnaires],
        total=total,
        limit=query.limit,
        offset=query.offset,
    )


@router.get(
    "/questionnaires/{questionnaire_id}",
    response_model=QuestionnaireDefinitionResponse,
    summary="Get questionnaire",
    description="Retrieve a specific questionnaire definition by ID",
)
async def get_questionnaire(
    request: Request,
    questionnaire_id: UUID,
    db: AsyncSession = Depends(get_audit_engine_db),
) -> QuestionnaireDefinitionResponse:
    """Get questionnaire by ID."""
    request_id = _get_request_id(request)
    logger.info(f"Getting questionnaire: id={questionnaire_id}", extra={"request_id": request_id})
    questionnaire = await QuestionnaireService.get_questionnaire(db, questionnaire_id)
    return QuestionnaireDefinitionResponse.model_validate(questionnaire)


# Audit Instance endpoints
@router.post(
    "/audit-instances",
    response_model=AuditInstanceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create audit instance",
    description="Create a new audit instance with brand context snapshot",
)
async def create_audit_instance(
    request: Request,
    audit_data: AuditInstanceCreate,
    db: AsyncSession = Depends(get_audit_engine_db),
) -> AuditInstanceResponse:
    """Create a new audit instance."""
    request_id = _get_request_id(request)
    logger.info(
        f"Creating audit instance: brand_id={audit_data.brand_id}",
        extra={"request_id": request_id},
    )
    audit_instance = await AuditInstanceService.create_audit_instance(db, audit_data)
    return AuditInstanceResponse.model_validate(audit_instance)


@router.get(
    "/audit-instances",
    response_model=AuditInstanceListResponse,
    summary="List audit instances",
    description="Retrieve a paginated list of audit instances",
)
async def list_audit_instances(
    request: Request,
    brand_id: UUID | None = Query(None, description="Filter by brand ID"),
    status: str | None = Query(None, description="Filter by status"),
    limit: int = Query(default=20, ge=1, le=50, description="Maximum number of records to return"),
    offset: int = Query(default=0, ge=0, description="Number of records to skip"),
    db: AsyncSession = Depends(get_audit_engine_db),
) -> AuditInstanceListResponse:
    """List audit instances with pagination."""
    request_id = _get_request_id(request)
    logger.info(
        f"Listing audit instances: brand_id={brand_id}, status={status}, limit={limit}, offset={offset}",
        extra={"request_id": request_id},
    )
    from src.audit_engine.constants import AuditInstanceStatus

    query = AuditInstanceListQuery(
        brand_id=brand_id,
        status=AuditInstanceStatus(status) if status else None,
        limit=limit,
        offset=offset,
    )
    audit_instances, total = await AuditInstanceService.list_audit_instances(db, query)
    return AuditInstanceListResponse(
        items=[AuditInstanceResponse.model_validate(ai) for ai in audit_instances],
        total=total,
        limit=query.limit,
        offset=query.offset,
    )


@router.get(
    "/audit-instances/{audit_instance_id}",
    response_model=AuditInstanceResponse,
    summary="Get audit instance",
    description="Retrieve a specific audit instance by ID",
)
async def get_audit_instance(
    request: Request,
    audit_instance_id: UUID,
    db: AsyncSession = Depends(get_audit_engine_db),
) -> AuditInstanceResponse:
    """Get audit instance by ID."""
    request_id = _get_request_id(request)
    logger.info(f"Getting audit instance: id={audit_instance_id}", extra={"request_id": request_id})
    audit_instance = await AuditInstanceService.get_audit_instance(db, audit_instance_id)
    return AuditInstanceResponse.model_validate(audit_instance)


@router.put(
    "/audit-instances/{audit_instance_id}",
    response_model=AuditInstanceResponse,
    summary="Update audit instance",
    description="Update an existing audit instance (status, score)",
)
async def update_audit_instance(
    request: Request,
    audit_instance_id: UUID,
    audit_data: AuditInstanceUpdate,
    db: AsyncSession = Depends(get_audit_engine_db),
) -> AuditInstanceResponse:
    """Update audit instance."""
    request_id = _get_request_id(request)
    logger.info(
        f"Updating audit instance: id={audit_instance_id}", extra={"request_id": request_id}
    )
    audit_instance = await AuditInstanceService.update_audit_instance_status(
        db, audit_instance_id, audit_data
    )
    return AuditInstanceResponse.model_validate(audit_instance)


# Audit Item endpoints
@router.post(
    "/audit-instances/{audit_instance_id}/generate-items",
    response_model=AuditItemGenerationResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate audit items",
    description="Generate audit items by evaluating rules against brand context and questionnaire responses",
)
async def generate_audit_items(
    request: Request,
    audit_instance_id: UUID,
    db: AsyncSession = Depends(get_audit_engine_db),
) -> AuditItemGenerationResponse:
    """Generate audit items for an audit instance."""
    request_id = _get_request_id(request)
    logger.info(
        f"Generating audit items for audit instance: id={audit_instance_id}",
        extra={"request_id": request_id},
    )
    service = AuditItemService()
    stats = await service.generate_audit_items(db, audit_instance_id)
    return AuditItemGenerationResponse(
        items_created=stats["items_created"],
        items_preserved=stats["items_preserved"],
        rules_evaluated=stats["rules_evaluated"],
        rules_failed=stats["rules_failed"],
        message=f"Generated {stats['items_created']} new items, preserved {stats['items_preserved']} existing items",
    )


@router.get(
    "/audit-instances/{audit_instance_id}/items",
    response_model=AuditItemListResponse,
    summary="List audit items",
    description="Retrieve all audit items for an audit instance",
)
async def list_audit_items(
    request: Request,
    audit_instance_id: UUID,
    db: AsyncSession = Depends(get_audit_engine_db),
) -> AuditItemListResponse:
    """List audit items for an audit instance."""
    request_id = _get_request_id(request)
    logger.info(
        f"Listing audit items for audit instance: id={audit_instance_id}",
        extra={"request_id": request_id},
    )
    service = AuditItemService()
    items = await service.get_audit_items_by_instance(db, audit_instance_id)
    return AuditItemListResponse(
        items=[AuditItemResponse.model_validate(item) for item in items],
        total=len(items),
    )


@router.get(
    "/audit-items/{audit_item_id}",
    response_model=AuditItemResponse,
    summary="Get audit item",
    description="Retrieve a specific audit item by ID",
)
async def get_audit_item(
    request: Request,
    audit_item_id: UUID,
    db: AsyncSession = Depends(get_audit_engine_db),
) -> AuditItemResponse:
    """Get audit item by ID."""
    request_id = _get_request_id(request)
    logger.info(f"Getting audit item: id={audit_item_id}", extra={"request_id": request_id})
    service = AuditItemService()
    audit_item = await service.get_audit_item(db, audit_item_id)
    return AuditItemResponse.model_validate(audit_item)


@router.put(
    "/audit-items/{audit_item_id}",
    response_model=AuditItemResponse,
    summary="Update audit item",
    description="Update an existing audit item (status, comments)",
)
async def update_audit_item(
    request: Request,
    audit_item_id: UUID,
    audit_item_data: AuditItemUpdate,
    db: AsyncSession = Depends(get_audit_engine_db),
) -> AuditItemResponse:
    """Update audit item."""
    request_id = _get_request_id(request)
    logger.info(f"Updating audit item: id={audit_item_id}", extra={"request_id": request_id})
    service = AuditItemService()
    audit_item = await service.update_audit_item(db, audit_item_id, audit_item_data)
    return AuditItemResponse.model_validate(audit_item)
