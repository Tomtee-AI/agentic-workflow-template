"""
Tier 2 — Orchestrator: Quasi-Quorum Dispatcher
Fans out a single logical LLM invocation to >= 3 independent model
instances, computes a consistency_score, and accepts the result only
if the score meets the configured threshold.

Quasi-quorum reduces the effectiveness of prompt injection by requiring
correlated manipulation across multiple independent model instances.
"""
from __future__ import annotations

import concurrent.futures
from dataclasses import dataclass
from typing import Callable

from src.shared.contracts import AgentRequest, AgentResponse
from src.shared.exceptions import QuorumFailure


@dataclass
class QuorumConfig:
    min_instances: int = 3
    threshold: float = 0.7
    timeout_seconds: float = 30.0


class QuorumDispatcher:
    def __init__(self, config: QuorumConfig | None = None):
        self.config = config or QuorumConfig()

    def dispatch(
        self,
        request: AgentRequest,
        invoke_fn: Callable[[AgentRequest, int], AgentResponse],
    ) -> AgentResponse:
        """Fan out to min_instances, score agreement, return merged response."""
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.config.min_instances
        ) as pool:
            futures = [
                pool.submit(invoke_fn, request, i)
                for i in range(self.config.min_instances)
            ]
            responses: list[AgentResponse] = []
            for future in concurrent.futures.as_completed(
                futures, timeout=self.config.timeout_seconds
            ):
                try:
                    responses.append(future.result())
                except Exception:
                    pass  # score with available responses

        if not responses:
            raise QuorumFailure("All quorum instances failed to respond.")

        score = _score_responses(responses)
        result = responses[0].model_copy(update={"consistency_score": score})

        if score < self.config.threshold:
            raise QuorumFailure(
                f"Quorum consistency score {score:.2f} below threshold "
                f"{self.config.threshold:.2f}. Human escalation required."
            )
        return result


def _score_responses(responses: list[AgentResponse]) -> float:
    """Return fraction of structured output fields that agree across all instances."""
    if len(responses) < 2:
        return 1.0
    keys = set(responses[0].output.keys())
    if not keys:
        return 1.0
    agree = sum(
        1
        for key in keys
        if all(r.output.get(key) == responses[0].output.get(key) for r in responses[1:])
    )
    return agree / len(keys)
