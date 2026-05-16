"""Typed exceptions covering the v2 failure taxonomy.
Each class maps to a named failure class with defined retry and escalation behavior.
"""


class BudgetExceeded(Exception):
    """Raised when a run exceeds its token, cost, or wall-clock budget."""


class PolicyDenied(Exception):
    """Raised when a tool call is blocked by the policy gate (POLICY_DENIED)."""


class SchemaValidationError(Exception):
    """Raised when an LLM response fails schema validation (SCHEMA_VALIDATION_FAILED)."""


class TransientError(Exception):
    """Retryable upstream error — rate limit, 502, etc. (TRANSIENT_UPSTREAM)."""


class CatastrophicError(Exception):
    """Non-retryable; triggers circuit-break and on-call alert (CATASTROPHIC)."""


class QuorumFailure(Exception):
    """Raised when quasi-quorum consistency_score falls below threshold (LOW_CONFIDENCE)."""


class HumanApprovalTimeout(Exception):
    """Raised when a human approval request is not acknowledged within SLA."""


class CircuitOpen(Exception):
    """Raised when a circuit breaker is open for a degraded dependency."""


class ModelRefusal(Exception):
    """Raised when the model declines to respond due to content policy (MODEL_REFUSAL)."""
