"""Questionnaires domain service layer."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.audit_engine.exceptions import QuestionnaireNotFoundError
from src.audit_engine.models import QuestionnaireDefinition
from src.audit_engine.questionnaires.schemas import (
    QuestionnaireDefinitionCreate,
    QuestionnaireListQuery,
)


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
