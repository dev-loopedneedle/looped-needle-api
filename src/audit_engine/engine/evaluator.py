"""Rule evaluation engine."""

import logging
from typing import Any

from src.audit_engine.engine.expression_evaluator import ExpressionEvaluator


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

