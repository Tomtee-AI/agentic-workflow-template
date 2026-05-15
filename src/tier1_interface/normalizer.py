"""
Converts any raw request format into a canonical TaskEnvelope.
PII/secret stripping happens here before anything reaches the Orchestrator.
"""

import re
from src.shared.contracts import TaskEnvelope


_PII_PATTERNS = [
    r"\b\d{3}-\d{2}-\d{4}\b",   # SSN
    r"\b4[0-9]{12}(?:[0-9]{3})?\b",  # Visa card
]


def strip_pii(text: str) -> str:
    for pattern in _PII_PATTERNS:
        text = re.sub(pattern, "[REDACTED]", text)
    return text


def normalize(raw_request: dict, principal: str) -> TaskEnvelope:
    intent = strip_pii(raw_request.get("intent", ""))
    payload = {k: strip_pii(str(v)) if isinstance(v, str) else v
               for k, v in raw_request.get("payload", {}).items()}
    return TaskEnvelope(
        intent=intent,
        payload=payload,
        principal=principal,
        deadline=raw_request.get("deadline"),
    )
