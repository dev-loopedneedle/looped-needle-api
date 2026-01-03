"""Expression evaluator with Python-like syntax and helper functions."""

import logging
from typing import Any

try:
    from simpleeval import FunctionNotDefined, SimpleEval
except ImportError:
    SimpleEval = None
    FunctionNotDefined = Exception


class ExpressionEvaluator:
    """
    Evaluates expressions with Python-like syntax.

    Supports:
    - Nested object access: context.company_size, scope.season
    - Array operations via helper functions: has_material(context.products, 'Leather')
    - Boolean logic: and, or, not
    - Comparisons: ==, !=, <, >, <=, >=
    - In operator: 'EU' in context.target_markets
    """

    def __init__(self):
        """Initialize expression evaluator."""
        if SimpleEval is None:
            raise ImportError("simpleeval is required. Install with: pip install simpleeval")

        self.evaluator = SimpleEval()
        self.logger = logging.getLogger(__name__)

        # Add helper functions for common operations
        self._setup_functions()

    def _setup_functions(self):
        """Setup helper functions for expression evaluation."""

        # Check if any product has a specific material
        def has_material(products: list[dict], material_type: str) -> bool:
            """Check if any product contains the specified material."""
            if not products:
                return False
            for product in products:
                materials = product.get("materials_composition", [])
                for mat in materials:
                    if mat.get("material_type") == material_type:
                        return True
            return False

        # Check if value is in list/array
        def contains(items: list, value: Any) -> bool:
            """Check if value is in list."""
            return value in items if items else False

        # Check if any item in list matches condition
        def any_match(items: list, field: str, value: Any) -> bool:
            """Check if any item in list has field == value."""
            if not items:
                return False
            for item in items:
                if isinstance(item, dict) and item.get(field) == value:
                    return True
            return False

        # Check if all items in list match condition
        def all_match(items: list, field: str, value: Any) -> bool:
            """Check if all items in list have field == value."""
            if not items:
                return False
            for item in items:
                if not isinstance(item, dict) or item.get(field) != value:
                    return False
            return True

        # Check if supply chain has specific role
        def has_supply_chain_role(nodes: list[dict], role: str) -> bool:
            """Check if any supply chain node has the specified role."""
            if not nodes:
                return False
            for node in nodes:
                if node.get("role") == role:
                    return True
            return False

        # Check if supply chain has nodes in country
        def has_supply_chain_in_country(nodes: list[dict], country: str) -> bool:
            """Check if any supply chain node is in the specified country."""
            if not nodes:
                return False
            for node in nodes:
                if node.get("country") == country:
                    return True
            return False

        # Get count of items matching condition
        def count_match(items: list, field: str, value: Any) -> int:
            """Count items in list where field == value."""
            if not items:
                return 0
            count = 0
            for item in items:
                if isinstance(item, dict) and item.get(field) == value:
                    count += 1
            return count

        # Register functions
        self.evaluator.functions.update(
            {
                "has_material": has_material,
                "contains": contains,
                "any_match": any_match,
                "all_match": all_match,
                "has_supply_chain_role": has_supply_chain_role,
                "has_supply_chain_in_country": has_supply_chain_in_country,
                "count_match": count_match,
            }
        )

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
        """
        try:
            # Combine context and scope for evaluation
            evaluation_context = {"context": context, "scope": scope}
            self.evaluator.names = evaluation_context

            result = self.evaluator.eval(expression)
            return bool(result), None
        except FunctionNotDefined as e:
            error_msg = f"Unknown function in expression: {str(e)}"
            self.logger.error(
                f"Expression evaluation failed: {error_msg}",
                extra={"expression": expression, "error": str(e)},
            )
            return False, error_msg
        except Exception as e:
            error_msg = f"Expression evaluation error: {str(e)}"
            self.logger.error(
                f"Expression evaluation failed: {error_msg}",
                extra={"expression": expression, "error": str(e)},
            )
            return False, error_msg


# Example expressions:
#
# Array operations:
# has_material(context.products, 'Leather')
# 'EU' in context.target_markets
# contains(context.target_markets, 'EU')
#
# Boolean operators:
# context.company_size == 'Large' and scope.has_wet_processing == True
#
# Complex conditions:
# has_supply_chain_role(context.supply_chain_nodes, 'CutAndSew')
# has_supply_chain_in_country(context.supply_chain_nodes, 'CN')
#
# Nested access:
# context.brand.company_size == 'Large'
# context['brand']['company_size'] == 'Large'  (if nested)
# context.company_size == 'Large'  (if flat)
#
# Available helper functions:
# - has_material(products, material_type) - Check if any product has material
# - contains(items, value) - Check if value in list
# - any_match(items, field, value) - Check if any item matches
# - all_match(items, field, value) - Check if all items match
# - has_supply_chain_role(nodes, role) - Check supply chain role
# - has_supply_chain_in_country(nodes, country) - Check supply chain country
# - count_match(items, field, value) - Count matching items
