"""Inference engine domain service layer."""

import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.inference.exceptions import (
    AuditInstanceNotFoundError,
    AuditItemNotFoundError,
    BrandNotFoundError,
    CriterionNotFoundError,
    QuestionnaireNotFoundError,
    ReferentialIntegrityError,
    RuleNotFoundError,
)
from src.inference.expression_evaluator import ExpressionEvaluator
from src.inference.models import (
    AuditInstance,
    AuditItem,
    Brand,
    CriteriaRule,
    Product,
    QuestionnaireDefinition,
    SupplyChainNode,
    SustainabilityCriterion,
)
from src.inference.schemas import (
    AuditInstanceCreate,
    AuditInstanceListQuery,
    AuditInstanceUpdate,
    AuditItemUpdate,
    BrandCreate,
    BrandListQuery,
    BrandUpdate,
    CriterionCreate,
    CriterionListQuery,
    ProductCreate,
    QuestionnaireDefinitionCreate,
    QuestionnaireListQuery,
    RuleCreate,
    RuleUpdate,
    SupplyChainNodeCreate,
)
from src.inference.utils import check_brand_references


class BrandService:
    """Service for brand operations."""

    @staticmethod
    async def create_brand(
        db: AsyncSession,
        brand_data: BrandCreate,
    ) -> Brand:
        """
        Create a new brand.

        Args:
            db: Database session
            brand_data: Brand data

        Returns:
            Created brand
        """
        brand = Brand(**brand_data.model_dump())
        db.add(brand)
        await db.commit()
        await db.refresh(brand)
        return brand

    @staticmethod
    async def get_brand(
        db: AsyncSession,
        brand_id: UUID,
    ) -> Brand:
        """
        Get brand by ID.

        Args:
            db: Database session
            brand_id: Brand ID

        Returns:
            Brand

        Raises:
            BrandNotFoundError: If brand not found
        """
        result = await db.execute(
            select(Brand).where(Brand.id == brand_id, Brand.deleted_at.is_(None))
        )
        brand = result.scalar_one_or_none()
        if not brand:
            raise BrandNotFoundError(str(brand_id))
        return brand

    @staticmethod
    async def list_brands(
        db: AsyncSession,
        query: BrandListQuery,
    ) -> tuple[list[Brand], int]:
        """
        List brands with pagination.

        Args:
            db: Database session
            query: Query parameters

        Returns:
            Tuple of (brands, total count)
        """
        stmt = select(Brand).where(Brand.deleted_at.is_(None))
        count_stmt = select(func.count()).select_from(Brand).where(Brand.deleted_at.is_(None))

        total_result = await db.execute(count_stmt)
        total = total_result.scalar_one()

        stmt = stmt.order_by(Brand.created_at.desc()).limit(query.limit).offset(query.offset)

        result = await db.execute(stmt)
        brands = result.scalars().all()

        return list(brands), total

    @staticmethod
    async def update_brand(
        db: AsyncSession,
        brand_id: UUID,
        update_data: BrandUpdate,
    ) -> Brand:
        """
        Update a brand.

        Args:
            db: Database session
            brand_id: Brand ID
            update_data: Update data

        Returns:
            Updated brand

        Raises:
            BrandNotFoundError: If brand not found
        """
        brand = await BrandService.get_brand(db, brand_id)

        update_dict = update_data.model_dump(exclude_unset=True)
        if update_dict:
            update_dict["updated_at"] = datetime.utcnow()
            for key, value in update_dict.items():
                setattr(brand, key, value)

            await db.commit()
            await db.refresh(brand)

        return brand

    @staticmethod
    async def delete_brand(
        db: AsyncSession,
        brand_id: UUID,
    ) -> None:
        """
        Soft delete a brand (if not referenced by audit instances).

        Args:
            db: Database session
            brand_id: Brand ID

        Raises:
            BrandNotFoundError: If brand not found
            ReferentialIntegrityError: If brand is referenced by audit instances
        """
        brand = await BrandService.get_brand(db, brand_id)

        # Check if brand is referenced
        is_referenced, reference_type = await check_brand_references(db, str(brand_id))
        if is_referenced:
            raise ReferentialIntegrityError("brand", str(brand_id), reference_type)

        # Soft delete
        brand.deleted_at = datetime.utcnow()
        await db.commit()


class ProductService:
    """Service for product operations."""

    @staticmethod
    async def create_product(
        db: AsyncSession,
        brand_id: UUID,
        product_data: ProductCreate,
    ) -> Product:
        """
        Create a new product.

        Args:
            db: Database session
            brand_id: Brand ID
            product_data: Product data

        Returns:
            Created product

        Raises:
            BrandNotFoundError: If brand not found
        """
        # Verify brand exists
        await BrandService.get_brand(db, brand_id)

        product = Product(brand_id=brand_id, **product_data.model_dump())
        db.add(product)
        await db.commit()
        await db.refresh(product)
        return product

    @staticmethod
    async def get_products_by_brand(
        db: AsyncSession,
        brand_id: UUID,
    ) -> list[Product]:
        """
        Get all products for a brand.

        Args:
            db: Database session
            brand_id: Brand ID

        Returns:
            List of products

        Raises:
            BrandNotFoundError: If brand not found
        """
        # Verify brand exists
        await BrandService.get_brand(db, brand_id)

        result = await db.execute(
            select(Product).where(Product.brand_id == brand_id, Product.deleted_at.is_(None))
        )
        products = result.scalars().all()
        return list(products)


class SupplyChainNodeService:
    """Service for supply chain node operations."""

    @staticmethod
    async def create_node(
        db: AsyncSession,
        brand_id: UUID,
        node_data: SupplyChainNodeCreate,
    ) -> SupplyChainNode:
        """
        Create a new supply chain node.

        Args:
            db: Database session
            brand_id: Brand ID
            node_data: Supply chain node data

        Returns:
            Created supply chain node

        Raises:
            BrandNotFoundError: If brand not found
        """
        # Verify brand exists
        await BrandService.get_brand(db, brand_id)

        node = SupplyChainNode(brand_id=brand_id, **node_data.model_dump())
        db.add(node)
        await db.commit()
        await db.refresh(node)
        return node

    @staticmethod
    async def get_nodes_by_brand(
        db: AsyncSession,
        brand_id: UUID,
    ) -> list[SupplyChainNode]:
        """
        Get all supply chain nodes for a brand.

        Args:
            db: Database session
            brand_id: Brand ID

        Returns:
            List of supply chain nodes

        Raises:
            BrandNotFoundError: If brand not found
        """
        # Verify brand exists
        await BrandService.get_brand(db, brand_id)

        result = await db.execute(
            select(SupplyChainNode).where(
                SupplyChainNode.brand_id == brand_id, SupplyChainNode.deleted_at.is_(None)
            )
        )
        nodes = result.scalars().all()
        return list(nodes)


class RuleEvaluator:
    """Service for evaluating rule expressions."""

    def __init__(self):
        """Initialize expression evaluator."""
        self.expression_evaluator = ExpressionEvaluator()
        self.logger = logging.getLogger(__name__)

    def evaluate(
        self, expression: str, context: dict[str, Any], scope: dict[str, Any]
    ) -> tuple[bool, str | None]:
        """
        Evaluate an expression against context and scope.

        Args:
            expression: Python-like expression string
            context: Brand context (products, supply chain, etc.)
            scope: Questionnaire responses (audit scope)

        Returns:
            Tuple of (result: bool, error: str | None)
            If evaluation succeeds, returns (result, None)
            If evaluation fails, returns (False, error_message)
        """
        try:
            result, error = self.expression_evaluator.evaluate(expression, context, scope)
            if error:
                return False, error
            return result, None
        except Exception as e:
            error_msg = f"Expression evaluation error: {str(e)}"
            self.logger.error(
                f"Rule evaluation failed: {error_msg}", extra={"expression": expression}
            )
            return False, error_msg


class CriterionService:
    """Service for sustainability criterion operations."""

    @staticmethod
    async def create_criterion(
        db: AsyncSession,
        criterion_data: CriterionCreate,
    ) -> SustainabilityCriterion:
        """
        Create a new sustainability criterion.

        Args:
            db: Database session
            criterion_data: Criterion data

        Returns:
            Created criterion
        """
        criterion = SustainabilityCriterion(**criterion_data.model_dump())
        db.add(criterion)
        await db.commit()
        await db.refresh(criterion)
        return criterion

    @staticmethod
    async def get_criterion(
        db: AsyncSession,
        criterion_id: UUID,
    ) -> SustainabilityCriterion:
        """
        Get criterion by ID.

        Args:
            db: Database session
            criterion_id: Criterion ID

        Returns:
            Criterion

        Raises:
            CriterionNotFoundError: If criterion not found
        """
        result = await db.execute(
            select(SustainabilityCriterion).where(
                SustainabilityCriterion.id == criterion_id,
                SustainabilityCriterion.deleted_at.is_(None),
            )
        )
        criterion = result.scalar_one_or_none()
        if not criterion:
            raise CriterionNotFoundError(str(criterion_id))
        return criterion

    @staticmethod
    async def list_criteria(
        db: AsyncSession,
        query: CriterionListQuery,
    ) -> tuple[list[SustainabilityCriterion], int]:
        """
        List criteria with filtering and pagination.

        Args:
            db: Database session
            query: Query parameters

        Returns:
            Tuple of (criteria, total count)
        """
        stmt = select(SustainabilityCriterion).where(SustainabilityCriterion.deleted_at.is_(None))
        count_stmt = (
            select(func.count())
            .select_from(SustainabilityCriterion)
            .where(SustainabilityCriterion.deleted_at.is_(None))
        )

        if query.domain:
            stmt = stmt.where(SustainabilityCriterion.domain == query.domain)
            count_stmt = count_stmt.where(SustainabilityCriterion.domain == query.domain)

        total_result = await db.execute(count_stmt)
        total = total_result.scalar_one()

        stmt = stmt.order_by(SustainabilityCriterion.code).limit(query.limit).offset(query.offset)

        result = await db.execute(stmt)
        criteria = result.scalars().all()

        return list(criteria), total


class RuleService:
    """Service for criteria rule operations."""

    @staticmethod
    async def create_rule(
        db: AsyncSession,
        criterion_id: UUID,
        rule_data: RuleCreate,
    ) -> CriteriaRule:
        """
        Create a new rule for a criterion.

        Args:
            db: Database session
            criterion_id: Criterion ID
            rule_data: Rule data

        Returns:
            Created rule

        Raises:
            CriterionNotFoundError: If criterion not found
        """
        # Verify criterion exists
        await CriterionService.get_criterion(db, criterion_id)

        rule = CriteriaRule(criteria_id=criterion_id, **rule_data.model_dump())
        db.add(rule)
        await db.commit()
        await db.refresh(rule)
        return rule

    @staticmethod
    async def get_rule(
        db: AsyncSession,
        rule_id: UUID,
    ) -> CriteriaRule:
        """
        Get rule by ID.

        Args:
            db: Database session
            rule_id: Rule ID

        Returns:
            Rule

        Raises:
            RuleNotFoundError: If rule not found
        """
        result = await db.execute(
            select(CriteriaRule).where(
                CriteriaRule.id == rule_id, CriteriaRule.deleted_at.is_(None)
            )
        )
        rule = result.scalar_one_or_none()
        if not rule:
            raise RuleNotFoundError(str(rule_id))
        return rule

    @staticmethod
    async def get_rules_by_criterion(
        db: AsyncSession,
        criterion_id: UUID,
    ) -> list[CriteriaRule]:
        """
        Get all rules for a criterion, ordered by priority (highest first).

        Args:
            db: Database session
            criterion_id: Criterion ID

        Returns:
            List of rules ordered by priority

        Raises:
            CriterionNotFoundError: If criterion not found
        """
        # Verify criterion exists
        await CriterionService.get_criterion(db, criterion_id)

        result = await db.execute(
            select(CriteriaRule)
            .where(CriteriaRule.criteria_id == criterion_id, CriteriaRule.deleted_at.is_(None))
            .order_by(CriteriaRule.priority.desc())
        )
        rules = result.scalars().all()
        return list(rules)

    @staticmethod
    async def update_rule(
        db: AsyncSession,
        rule_id: UUID,
        update_data: RuleUpdate,
    ) -> CriteriaRule:
        """
        Update a rule.

        Args:
            db: Database session
            rule_id: Rule ID
            update_data: Update data

        Returns:
            Updated rule

        Raises:
            RuleNotFoundError: If rule not found
        """
        rule = await RuleService.get_rule(db, rule_id)

        update_dict = update_data.model_dump(exclude_unset=True)
        if update_dict:
            update_dict["updated_at"] = datetime.utcnow()
            for key, value in update_dict.items():
                setattr(rule, key, value)

            await db.commit()
            await db.refresh(rule)

        return rule


class QuestionnaireService:
    """Service for questionnaire definition operations."""

    @staticmethod
    async def create_questionnaire(
        db: AsyncSession,
        questionnaire_data: QuestionnaireDefinitionCreate,
    ) -> QuestionnaireDefinition:
        """
        Create a new questionnaire definition.

        Args:
            db: Database session
            questionnaire_data: Questionnaire data

        Returns:
            Created questionnaire
        """
        questionnaire = QuestionnaireDefinition(**questionnaire_data.model_dump())
        db.add(questionnaire)
        await db.commit()
        await db.refresh(questionnaire)
        return questionnaire

    @staticmethod
    async def get_questionnaire(
        db: AsyncSession,
        questionnaire_id: UUID,
    ) -> QuestionnaireDefinition:
        """
        Get questionnaire by ID.

        Args:
            db: Database session
            questionnaire_id: Questionnaire ID

        Returns:
            Questionnaire

        Raises:
            QuestionnaireNotFoundError: If questionnaire not found
        """
        result = await db.execute(
            select(QuestionnaireDefinition).where(
                QuestionnaireDefinition.id == questionnaire_id,
                QuestionnaireDefinition.deleted_at.is_(None),
            )
        )
        questionnaire = result.scalar_one_or_none()
        if not questionnaire:
            raise QuestionnaireNotFoundError(str(questionnaire_id))
        return questionnaire

    @staticmethod
    async def list_active_questionnaires(
        db: AsyncSession,
        query: QuestionnaireListQuery,
    ) -> tuple[list[QuestionnaireDefinition], int]:
        """
        List questionnaires with filtering and pagination.

        Args:
            db: Database session
            query: Query parameters

        Returns:
            Tuple of (questionnaires, total count)
        """
        stmt = select(QuestionnaireDefinition).where(QuestionnaireDefinition.deleted_at.is_(None))
        count_stmt = (
            select(func.count())
            .select_from(QuestionnaireDefinition)
            .where(QuestionnaireDefinition.deleted_at.is_(None))
        )

        if query.is_active is not None:
            stmt = stmt.where(QuestionnaireDefinition.is_active == query.is_active)
            count_stmt = count_stmt.where(QuestionnaireDefinition.is_active == query.is_active)

        total_result = await db.execute(count_stmt)
        total = total_result.scalar_one()

        stmt = (
            stmt.order_by(QuestionnaireDefinition.created_at.desc())
            .limit(query.limit)
            .offset(query.offset)
        )

        result = await db.execute(stmt)
        questionnaires = result.scalars().all()

        return list(questionnaires), total


def _capture_brand_context(
    brand: Brand, products: list[Product], supply_chain_nodes: list[SupplyChainNode]
) -> dict[str, Any]:
    """
    Capture brand context snapshot for audit instance.

    Args:
        brand: Brand model
        products: List of products
        supply_chain_nodes: List of supply chain nodes

    Returns:
        Brand context dictionary
    """
    return {
        "brand": {
            "id": str(brand.id),
            "name": brand.name,
            "registration_country": brand.registration_country,
            "company_size": brand.company_size,
            "target_markets": brand.target_markets,
        },
        "products": [
            {
                "id": str(product.id),
                "name": product.name,
                "category": product.category,
                "materials_composition": product.materials_composition,
                "manufacturing_processes": product.manufacturing_processes,
            }
            for product in products
        ],
        "supply_chain_nodes": [
            {
                "id": str(node.id),
                "role": node.role,
                "country": node.country,
                "tier_level": node.tier_level,
            }
            for node in supply_chain_nodes
        ],
    }


class AuditInstanceService:
    """Service for audit instance operations."""

    @staticmethod
    async def create_audit_instance(
        db: AsyncSession,
        audit_data: AuditInstanceCreate,
    ) -> AuditInstance:
        """
        Create a new audit instance with brand context snapshot.

        Args:
            db: Database session
            audit_data: Audit instance data

        Returns:
            Created audit instance

        Raises:
            BrandNotFoundError: If brand not found
            QuestionnaireNotFoundError: If questionnaire not found
        """
        # Verify brand exists
        brand = await BrandService.get_brand(db, audit_data.brand_id)

        # Verify questionnaire exists
        await QuestionnaireService.get_questionnaire(db, audit_data.questionnaire_definition_id)

        # Capture brand context snapshot
        products = await ProductService.get_products_by_brand(db, audit_data.brand_id)
        supply_chain_nodes = await SupplyChainNodeService.get_nodes_by_brand(
            db, audit_data.brand_id
        )
        brand_context_snapshot = _capture_brand_context(brand, products, supply_chain_nodes)

        audit_instance = AuditInstance(
            brand_id=audit_data.brand_id,
            questionnaire_definition_id=audit_data.questionnaire_definition_id,
            scoping_responses=audit_data.scoping_responses,
            brand_context_snapshot=brand_context_snapshot,
        )
        db.add(audit_instance)
        await db.commit()
        await db.refresh(audit_instance)
        return audit_instance

    @staticmethod
    async def get_audit_instance(
        db: AsyncSession,
        audit_instance_id: UUID,
    ) -> AuditInstance:
        """
        Get audit instance by ID.

        Args:
            db: Database session
            audit_instance_id: Audit instance ID

        Returns:
            Audit instance

        Raises:
            AuditInstanceNotFoundError: If audit instance not found
        """
        result = await db.execute(
            select(AuditInstance).where(
                AuditInstance.id == audit_instance_id, AuditInstance.deleted_at.is_(None)
            )
        )
        audit_instance = result.scalar_one_or_none()
        if not audit_instance:
            raise AuditInstanceNotFoundError(str(audit_instance_id))
        return audit_instance

    @staticmethod
    async def list_audit_instances(
        db: AsyncSession,
        query: AuditInstanceListQuery,
    ) -> tuple[list[AuditInstance], int]:
        """
        List audit instances with filtering and pagination.

        Args:
            db: Database session
            query: Query parameters

        Returns:
            Tuple of (audit instances, total count)
        """
        stmt = select(AuditInstance).where(AuditInstance.deleted_at.is_(None))
        count_stmt = (
            select(func.count())
            .select_from(AuditInstance)
            .where(AuditInstance.deleted_at.is_(None))
        )

        if query.brand_id:
            stmt = stmt.where(AuditInstance.brand_id == query.brand_id)
            count_stmt = count_stmt.where(AuditInstance.brand_id == query.brand_id)

        if query.status:
            stmt = stmt.where(AuditInstance.status == query.status)
            count_stmt = count_stmt.where(AuditInstance.status == query.status)

        total_result = await db.execute(count_stmt)
        total = total_result.scalar_one()

        stmt = (
            stmt.order_by(AuditInstance.created_at.desc()).limit(query.limit).offset(query.offset)
        )

        result = await db.execute(stmt)
        audit_instances = result.scalars().all()

        return list(audit_instances), total

    @staticmethod
    async def update_audit_instance_status(
        db: AsyncSession,
        audit_instance_id: UUID,
        update_data: AuditInstanceUpdate,
    ) -> AuditInstance:
        """
        Update audit instance status with state transition validation.

        Args:
            db: Database session
            audit_instance_id: Audit instance ID
            update_data: Update data

        Returns:
            Updated audit instance

        Raises:
            AuditInstanceNotFoundError: If audit instance not found
        """
        from src.inference.utils import validate_audit_instance_status_transition

        audit_instance = await AuditInstanceService.get_audit_instance(db, audit_instance_id)

        update_dict = update_data.model_dump(exclude_unset=True)
        if update_dict:
            # Validate status transition if status is being updated
            if "status" in update_dict:
                validate_audit_instance_status_transition(
                    audit_instance.status, update_dict["status"]
                )

            update_dict["updated_at"] = datetime.utcnow()
            for key, value in update_dict.items():
                setattr(audit_instance, key, value)

            await db.commit()
            await db.refresh(audit_instance)

        return audit_instance


class AuditItemService:
    """Service for audit item operations."""

    def __init__(self):
        """Initialize audit item service with rule evaluator."""
        self.rule_evaluator = RuleEvaluator()
        self.logger = logging.getLogger(__name__)

    async def generate_audit_items(
        self,
        db: AsyncSession,
        audit_instance_id: UUID,
    ) -> dict[str, int]:
        """
        Generate audit items by evaluating rules against brand context and questionnaire responses.

        Args:
            db: Database session
            audit_instance_id: Audit instance ID

        Returns:
            Dictionary with generation statistics

        Raises:
            AuditInstanceNotFoundError: If audit instance not found
        """
        # Get audit instance with context
        audit_instance = await AuditInstanceService.get_audit_instance(db, audit_instance_id)

        # Get existing audit items to preserve those with evidence
        existing_items_result = await db.execute(
            select(AuditItem).where(
                AuditItem.audit_instance_id == audit_instance_id, AuditItem.deleted_at.is_(None)
            )
        )
        existing_items = existing_items_result.scalars().all()
        existing_criteria_ids = {item.criteria_id for item in existing_items}

        # Get all active rules ordered by priority
        rules_result = await db.execute(
            select(CriteriaRule)
            .join(SustainabilityCriterion)
            .where(
                CriteriaRule.deleted_at.is_(None),
                SustainabilityCriterion.deleted_at.is_(None),
            )
            .order_by(CriteriaRule.priority.desc())
        )
        all_rules = rules_result.scalars().all()

        # Prepare evaluation context
        brand_context = audit_instance.brand_context_snapshot
        scope = audit_instance.scoping_responses

        # Log generation start
        import time

        start_time = time.time()
        self.logger.info(
            f"Starting audit item generation for audit instance {audit_instance_id}",
            extra={
                "audit_instance_id": str(audit_instance_id),
                "rules_count": len(all_rules),
                "existing_items_count": len(existing_items),
            },
        )

        # Evaluate rules and collect matches
        matching_rules_by_criterion: dict[UUID, CriteriaRule] = {}
        rules_evaluated = 0
        rules_failed = 0

        for rule in all_rules:
            rules_evaluated += 1
            result, error = self.rule_evaluator.evaluate(
                rule.condition_expression, brand_context, scope
            )

            if error:
                rules_failed += 1
                self.logger.warning(
                    f"Rule evaluation failed for rule {rule.id}: {error}",
                    extra={
                        "rule_id": str(rule.id),
                        "criterion_id": str(rule.criteria_id),
                        "error": error,
                    },
                )
                continue

            if result:
                # Rule matched - use highest priority rule per criterion
                if (
                    rule.criteria_id not in matching_rules_by_criterion
                    or rule.priority > matching_rules_by_criterion[rule.criteria_id].priority
                ):
                    matching_rules_by_criterion[rule.criteria_id] = rule

        # Create audit items for matching criteria (preserve existing items)
        items_created = 0
        items_preserved = 0

        for criterion_id, rule in matching_rules_by_criterion.items():
            # Skip if item already exists for this criterion
            if criterion_id in existing_criteria_ids:
                items_preserved += 1
                continue

            # Create new audit item
            audit_item = AuditItem(
                audit_instance_id=audit_instance_id,
                criteria_id=criterion_id,
                triggered_by_rule_id=rule.id,
            )
            db.add(audit_item)
            items_created += 1

        await db.commit()

        # Log generation completion with performance metrics
        elapsed_time = time.time() - start_time
        self.logger.info(
            f"Completed audit item generation for audit instance {audit_instance_id}",
            extra={
                "audit_instance_id": str(audit_instance_id),
                "items_created": items_created,
                "items_preserved": items_preserved,
                "rules_evaluated": rules_evaluated,
                "rules_failed": rules_failed,
                "elapsed_time_seconds": elapsed_time,
            },
        )

        return {
            "items_created": items_created,
            "items_preserved": items_preserved,
            "rules_evaluated": rules_evaluated,
            "rules_failed": rules_failed,
        }

    async def get_audit_items_by_instance(
        db: AsyncSession,
        audit_instance_id: UUID,
    ) -> list[AuditItem]:
        """
        Get all audit items for an audit instance.

        Args:
            db: Database session
            audit_instance_id: Audit instance ID

        Returns:
            List of audit items

        Raises:
            AuditInstanceNotFoundError: If audit instance not found
        """
        # Verify audit instance exists
        await AuditInstanceService.get_audit_instance(db, audit_instance_id)

        result = await db.execute(
            select(AuditItem).where(
                AuditItem.audit_instance_id == audit_instance_id, AuditItem.deleted_at.is_(None)
            )
        )
        items = result.scalars().all()
        return list(items)

    async def get_audit_item(
        db: AsyncSession,
        audit_item_id: UUID,
    ) -> AuditItem:
        """
        Get audit item by ID.

        Args:
            db: Database session
            audit_item_id: Audit item ID

        Returns:
            Audit item

        Raises:
            AuditItemNotFoundError: If audit item not found
        """
        result = await db.execute(
            select(AuditItem).where(AuditItem.id == audit_item_id, AuditItem.deleted_at.is_(None))
        )
        audit_item = result.scalar_one_or_none()
        if not audit_item:
            raise AuditItemNotFoundError(str(audit_item_id))
        return audit_item

    async def update_audit_item(
        db: AsyncSession,
        audit_item_id: UUID,
        update_data: AuditItemUpdate,
    ) -> AuditItem:
        """
        Update audit item with status transition validation.

        Args:
            db: Database session
            audit_item_id: Audit item ID
            update_data: Update data

        Returns:
            Updated audit item

        Raises:
            AuditItemNotFoundError: If audit item not found
        """
        from src.inference.utils import can_transition_audit_item

        audit_item = await AuditItemService.get_audit_item(db, audit_item_id)

        update_dict = update_data.model_dump(exclude_unset=True)
        if update_dict:
            # Validate status transition if status is being updated
            if "status" in update_dict:
                if not can_transition_audit_item(audit_item.status, update_dict["status"]):
                    from src.inference.exceptions import InferenceValidationError

                    raise InferenceValidationError(
                        f"Invalid status transition from {audit_item.status} to {update_dict['status']}"
                    )

            update_dict["updated_at"] = datetime.utcnow()
            for key, value in update_dict.items():
                setattr(audit_item, key, value)

            await db.commit()
            await db.refresh(audit_item)

        return audit_item
