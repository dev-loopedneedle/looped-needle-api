"""Standards domain service layer."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.audit_engine.exceptions import CriterionNotFoundError, RuleNotFoundError
from src.audit_engine.models import CriteriaRule, SustainabilityCriterion
from src.audit_engine.standards.schemas import (
    CriterionCreate,
    CriterionListQuery,
    RuleCreate,
    RuleUpdate,
)


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

