"""Rules domain exceptions."""


class RuleNotFoundError(Exception):
    """Raised when a rule is not found."""

    def __init__(self, rule_id: str):
        super().__init__(f"Rule not found: {rule_id}")
        self.rule_id = rule_id


class RuleStateError(Exception):
    """Raised when an operation is invalid for the current rule state."""

    def __init__(self, message: str):
        super().__init__(message)


class ConditionTreeValidationError(Exception):
    """Raised when rule condition tree validation fails."""

    def __init__(self, message: str):
        super().__init__(message)


class EvidenceClaimNotFoundError(Exception):
    """Raised when an evidence claim is not found."""

    def __init__(self, claim_id: str):
        super().__init__(f"Evidence claim not found: {claim_id}")
        self.claim_id = claim_id
