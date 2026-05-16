"""
Tier 6 — Observability: Eval Harness
Shared offline regression suite. New agents do not promote to production
without entries in this harness. See tests/replay/ for replay-based evals.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


@dataclass
class EvalCase:
    case_id: str
    agent_id: str
    input: dict
    expected_output: dict
    judge: Callable[[dict, dict], float] | None = None  # returns 0.0–1.0


@dataclass
class EvalResult:
    case_id: str
    agent_id: str
    score: float
    passed: bool
    reason: str = ""


class EvalHarness:
    def __init__(self, pass_threshold: float = 0.8):
        self._cases: list[EvalCase] = []
        self.pass_threshold = pass_threshold

    def register(self, case: EvalCase) -> None:
        self._cases.append(case)

    def run(self, invoke_fn: Callable[[str, dict], dict]) -> list[EvalResult]:
        """Run all registered cases. invoke_fn(agent_id, input) -> output dict."""
        results = []
        for case in self._cases:
            actual = invoke_fn(case.agent_id, case.input)
            judge = case.judge or _field_match_judge
            score = judge(case.expected_output, actual)
            results.append(EvalResult(
                case_id=case.case_id,
                agent_id=case.agent_id,
                score=score,
                passed=score >= self.pass_threshold,
            ))
        return results


def _field_match_judge(expected: dict, actual: dict) -> float:
    """Default: fraction of expected fields whose values match exactly."""
    if not expected:
        return 1.0
    matches = sum(1 for k, v in expected.items() if actual.get(k) == v)
    return matches / len(expected)
