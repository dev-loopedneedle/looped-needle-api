"""Audit runs domain service layer."""

import logging
import time
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.audit_engine.audit_runs.schemas import AuditInstanceCreate, AuditInstanceListQuery, AuditInstanceUpdate, AuditItemUpdate
from src.audit_engine.brands.service import BrandService, ProductService, SupplyChainNodeService
from src.audit_engine.engine.context_builder import capture_brand_context
from src.audit_engine.engine.evaluator import RuleEvaluator
from src.audit_engine.exceptions import (
    AuditInstanceNotFoundError,
    AuditItemNotFoundError,
    InferenceValidationError,
)
from src.audit_engine.models import AuditInstance, AuditItem, CriteriaRule, SustainabilityCriterion
from src.audit_engine.questionnaires.service import QuestionnaireService
from src.audit_engine.utils import can_transition_audit_item, validate_audit_instance_status_transition


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
        brand_context_snapshot = capture_brand_context(brand, products, supply_chain_nodes)

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
        from sqlalchemy import func

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
        self,
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
        self,
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
        self,
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
        audit_item = await self.get_audit_item(db, audit_item_id)

        update_dict = update_data.model_dump(exclude_unset=True)
        if update_dict:
            # Validate status transition if status is being updated
            if "status" in update_dict:
                if not can_transition_audit_item(audit_item.status, update_dict["status"]):
                    raise InferenceValidationError(
                        f"Invalid status transition from {audit_item.status} to {update_dict['status']}"
                    )

            update_dict["updated_at"] = datetime.utcnow()
            for key, value in update_dict.items():
                setattr(audit_item, key, value)

            await db.commit()
            await db.refresh(audit_item)

        return audit_item

