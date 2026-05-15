"""
Tier 1 — Interface
Entry point for all requests: human chat, webhooks, schedulers, other systems.
Handles AuthN/AuthZ, rate limiting, idempotency, and PII stripping before
handing a clean TaskEnvelope to the Orchestrator.
"""

from src.shared.contracts import TaskEnvelope
from src.tier1_interface.auth import authenticate
from src.tier1_interface.normalizer import normalize


def handle_request(raw_request: dict) -> TaskEnvelope:
    principal = authenticate(raw_request)
    return normalize(raw_request, principal)
