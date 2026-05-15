class BudgetExceeded(Exception):
    """Raised when a run exceeds its token, cost, or wall-clock budget."""


class PolicyDenied(Exception):
    """Raised when a tool call is blocked by the policy gate."""


class SchemaValidationError(Exception):
    """Raised when an LLM response fails schema validation."""


class TransientError(Exception):
    """Retryable error (rate limit, upstream 502, etc.)."""


class CatastrophicError(Exception):
    """Non-retryable; triggers circuit-break and on-call alert."""
