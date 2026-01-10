"""Service layer for rules domain."""

from collections.abc import Iterable
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.rules.constants import RuleState
from src.rules.exceptions import RuleNotFoundError, RuleStateError
from src.rules.models import EvidenceClaim, Rule, RuleEvidenceClaim
from src.rules.schemas import EvidenceClaimCreate, RuleCreate, RuleUpdate


async def _load_rule_with_claims(db: AsyncSession, rule: Rule) -> Rule:
    """Refresh rule with evidence claims and their required status."""
    await db.refresh(
        rule,
        attribute_names=[],
        with_for_update=False,
    )
    # Load claims with their required status from join table
    stmt = (
        select(EvidenceClaim, RuleEvidenceClaim.required)
        .join(RuleEvidenceClaim, RuleEvidenceClaim.evidence_claim_id == EvidenceClaim.id)
        .where(RuleEvidenceClaim.rule_id == rule.id)
        .order_by(RuleEvidenceClaim.sort_order, RuleEvidenceClaim.created_at)
    )
    result = await db.execute(stmt)
    rows = result.all()

    # Build claims with required field using a dict-based approach
    # This avoids mutating SQLModel objects and works with Pydantic's from_attributes
    claims_with_required: list[dict[str, Any]] = []
    for claim, required in rows:
        # Build a dict representation that includes the required field
        claim_dict = {
            "id": claim.id,
            "name": claim.name,
            "description": claim.description,
            "category": claim.category,
            "type": claim.type,
            "weight": float(claim.weight),
            "required": required,
            "created_at": claim.created_at,
            "updated_at": claim.updated_at,
        }
        claims_with_required.append(claim_dict)

    # Store claims as a dict list on the rule object for serialization
    # The router will use RuleResponse.model_validate which handles this properly
    rule.__dict__["evidence_claims"] = claims_with_required
    return rule


async def _get_next_version(db: AsyncSession, code: str) -> int:
    stmt = select(func.max(Rule.version)).where(Rule.code == code)
    result = await db.execute(stmt)
    max_version = result.scalar_one_or_none()
    return (max_version or 0) + 1


async def _upsert_claims(
    db: AsyncSession,
    rule_id: UUID,
    claim_creates: Iterable[EvidenceClaimCreate],
    claim_ids: Iterable[UUID],
) -> None:
    # Create new claims and track their required status
    created_claims: list[tuple[UUID, bool]] = []  # (claim_id, required)
    for payload in claim_creates:
        claim = EvidenceClaim(
            name=payload.name,
            description=payload.description,
            category=payload.category,
            type=payload.type,
            weight=payload.weight,
            created_at=datetime.now(timezone.utc),
        )
        db.add(claim)
        await db.flush()
        created_claims.append((claim.id, payload.required))

    # For existing claim IDs, default to required=True
    existing_claims: list[tuple[UUID, bool]] = [(cid, True) for cid in claim_ids]

    # Clear existing links
    await db.execute(
        RuleEvidenceClaim.__table__.delete().where(RuleEvidenceClaim.rule_id == rule_id)
    )
    # Insert links with required status and sort_order
    # Sort order is based on the position in the combined list
    now = datetime.now(timezone.utc)
    all_claims = list(created_claims) + list(existing_claims)
    for sort_order, (claim_id, required) in enumerate(all_claims, start=1):
        db.add(
            RuleEvidenceClaim(
                rule_id=rule_id,
                evidence_claim_id=claim_id,
                required=required,
                sort_order=sort_order,
                created_at=now,
            )
        )


class RuleService:
    """Rule operations."""

    @staticmethod
    async def create_rule(db: AsyncSession, payload: RuleCreate, created_by: UUID | None) -> Rule:
        version = await _get_next_version(db, payload.code)

        rule = Rule(
            code=payload.code,
            version=version,
            name=payload.name,
            description=payload.description,
            condition_tree=payload.conditionTree,
            state=RuleState.DRAFT,
            created_by_user_profile_id=created_by,
        )
        db.add(rule)
        await db.flush()

        await _upsert_claims(db, rule.id, payload.evidence_claims, payload.evidence_claim_ids)

        await db.commit()
        await db.refresh(rule)
        return await _load_rule_with_claims(db, rule)

    @staticmethod
    async def list_rules(
        db: AsyncSession,
        state: RuleState | None = None,
        code: str | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Rule], int]:
        stmt = select(Rule)
        count_stmt = select(func.count()).select_from(Rule)

        if state:
            stmt = stmt.where(Rule.state == state)
            count_stmt = count_stmt.where(Rule.state == state)
        if code:
            stmt = stmt.where(Rule.code == code)
            count_stmt = count_stmt.where(Rule.code == code)
        if search:
            # Search in both name and code (case-insensitive partial match)
            search_pattern = f"%{search}%"
            search_condition = (Rule.name.ilike(search_pattern)) | (Rule.code.ilike(search_pattern))
            stmt = stmt.where(search_condition)
            count_stmt = count_stmt.where(search_condition)

        total = (await db.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(Rule.created_at.desc()).limit(limit).offset(offset)
        result = await db.execute(stmt)
        rules: list[Rule] = result.scalars().all()

        # Load claims for each
        items: list[Rule] = []
        for r in rules:
            items.append(await _load_rule_with_claims(db, r))
        return items, total

    @staticmethod
    async def get_rule(db: AsyncSession, rule_id: UUID) -> Rule:
        result = await db.execute(select(Rule).where(Rule.id == rule_id))
        rule = result.scalar_one_or_none()
        if not rule:
            raise RuleNotFoundError(str(rule_id))
        return await _load_rule_with_claims(db, rule)

    @staticmethod
    async def update_rule(db: AsyncSession, rule_id: UUID, payload: RuleUpdate) -> Rule:
        rule = await RuleService.get_rule(db, rule_id)
        if rule.state != RuleState.DRAFT:
            raise RuleStateError("Only draft rules can be updated")

        if payload.name is not None:
            rule.name = payload.name
        if payload.description is not None:
            rule.description = payload.description
        if payload.conditionTree is not None:
            rule.condition_tree = payload.conditionTree

        if payload.evidence_claims is not None or payload.evidence_claim_ids is not None:
            claim_creates = payload.evidence_claims or []
            claim_ids = payload.evidence_claim_ids or []
            await _upsert_claims(db, rule.id, claim_creates, claim_ids)

        rule.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(rule)
        return await _load_rule_with_claims(db, rule)

    @staticmethod
    async def publish_rule(db: AsyncSession, rule_id: UUID) -> Rule:
        rule = await RuleService.get_rule(db, rule_id)
        if rule.state != RuleState.DRAFT:
            raise RuleStateError("Only draft rules can be published")
        rule.state = RuleState.PUBLISHED
        rule.published_at = datetime.now(timezone.utc)
        rule.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(rule)
        return await _load_rule_with_claims(db, rule)

    @staticmethod
    async def disable_rule(db: AsyncSession, rule_id: UUID) -> Rule:
        rule = await RuleService.get_rule(db, rule_id)
        if rule.state == RuleState.DISABLED:
            return rule
        rule.state = RuleState.DISABLED
        rule.disabled_at = datetime.now(timezone.utc)
        rule.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(rule)
        return await _load_rule_with_claims(db, rule)

    @staticmethod
    async def clone_rule(db: AsyncSession, rule_id: UUID) -> Rule:
        rule = await RuleService.get_rule(db, rule_id)
        next_version = await _get_next_version(db, rule.code)

        clone = Rule(
            code=rule.code,
            version=next_version,
            name=rule.name,
            description=rule.description,
            condition_tree=rule.condition_tree,
            state=RuleState.DRAFT,
            created_by_user_profile_id=rule.created_by_user_profile_id,
            replaces_rule_id=rule.id,
        )
        db.add(clone)
        await db.flush()

        # Copy claims with their required status
        claims_stmt = select(RuleEvidenceClaim).where(RuleEvidenceClaim.rule_id == rule.id)
        claims_result = await db.execute(claims_stmt)
        rule_claims = claims_result.scalars().all()

        # Recreate the join records with preserved required status
        now = datetime.now(timezone.utc)
        for rule_claim in rule_claims:
            db.add(
                RuleEvidenceClaim(
                    rule_id=clone.id,
                    evidence_claim_id=rule_claim.evidence_claim_id,
                    required=rule_claim.required,
                    sort_order=rule_claim.sort_order,
                    created_at=now,
                )
            )

        await db.commit()
        await db.refresh(clone)
        return await _load_rule_with_claims(db, clone)

    @staticmethod
    async def delete_rule(db: AsyncSession, rule_id: UUID) -> None:
        """
        Delete a rule. Only non-published rules (DRAFT or DISABLED) can be deleted.

        Args:
            db: Database session
            rule_id: Rule ID to delete

        Raises:
            RuleNotFoundError: If rule not found
            RuleStateError: If rule is PUBLISHED (cannot delete published rules)
        """
        result = await db.execute(select(Rule).where(Rule.id == rule_id))
        rule = result.scalar_one_or_none()
        if not rule:
            raise RuleNotFoundError(str(rule_id))

        # Only allow deletion of non-published rules
        if rule.state == RuleState.PUBLISHED:
            raise RuleStateError(
                "Cannot delete published rules. Disable the rule instead, or create a new version."
            )

        # Delete the rule (RuleEvidenceClaim entries will cascade delete)
        try:
            db.delete(rule)
            await db.commit()
        except IntegrityError as err:
            await db.rollback()
            # Rule is referenced elsewhere (e.g., by another rule's replaces_rule_id or in workflows)
            raise RuleStateError(
                f"Cannot delete rule: it is referenced by other records. Original error: {str(err)}"
            ) from err

    @staticmethod
    async def create_evidence_claim(
        db: AsyncSession,
        payload: EvidenceClaimCreate,
        created_by: UUID | None = None,
    ) -> EvidenceClaim:
        """Create a new evidence claim."""
        claim = EvidenceClaim(
            name=payload.name,
            description=payload.description,
            category=payload.category,
            type=payload.type,
            weight=payload.weight,
            created_by_user_profile_id=created_by,
        )
        db.add(claim)
        await db.commit()
        await db.refresh(claim)
        return claim

    @staticmethod
    async def list_evidence_claims(
        db: AsyncSession,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[EvidenceClaim], int]:
        """List evidence claims with pagination."""
        count_stmt = select(func.count()).select_from(EvidenceClaim)
        total = (await db.execute(count_stmt)).scalar_one()

        stmt = select(EvidenceClaim).order_by(EvidenceClaim.name).limit(limit).offset(offset)
        result = await db.execute(stmt)
        claims = list(result.scalars().all())
        return claims, total

    @staticmethod
    async def get_evidence_claim(db: AsyncSession, claim_id: UUID) -> EvidenceClaim:
        """Get evidence claim by ID."""
        from src.rules.exceptions import EvidenceClaimNotFoundError

        result = await db.execute(select(EvidenceClaim).where(EvidenceClaim.id == claim_id))
        claim = result.scalar_one_or_none()
        if not claim:
            raise EvidenceClaimNotFoundError(str(claim_id))
        return claim
