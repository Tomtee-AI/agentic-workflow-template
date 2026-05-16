# Agentic Workflow Template

A production-grade, multi-tier agentic AI application template. Clone it, fill in your domain logic, and ship a system that is secure, observable, and maintainable from day one.

**Version**: 2.0 · based on `Multi_Tier_Agentic_Workflow_v2.md`

---

## Architecture

Seven tiers: Tier 0 is a cross-cutting governance plane; Tiers 1–6 handle request flow top-down and data lineage bottom-up.

```
┌──────────────────────────────────────────────────────────────┐
│  Tier 0   Governance & Policy                                │
│           Policy-as-Code · Capability Registry · Flags       │
└──────────────────────────────────────────────────────────────┘
          ↓ enforces              ↑ feedback
┌──────────────────────────────────────────────────────────────┐
│  Tier 1   Interface  (Auth · Normalization · API versioning) │
└──────────────────────────────────────────────────────────────┘
                         │ TaskEnvelope
┌────────────────────────▼─────────────────────────────────────┐
│  Tier 2   Orchestrator                                        │
│           Planner · Router · Supervisor · Quorum Dispatcher  │
└──────────────────────────────────────────────────────────────┘
           │              │              │
           ▼              ▼              ▼
┌─────────────────┐ ┌───────────┐ ┌─────────────────┐
│  Specialist A   │ │ Spec. B   │ │  Specialist N   │  ← Tier 3
└─────────────────┘ └───────────┘ └─────────────────┘
           │              │              │
           ▼              ▼              ▼
┌──────────────────────────────────────────────────────────────┐
│  Tier 4   Tools & Services  (Gateway · Policy Gate · APIs)   │
└──────────────────────────────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────┐
│  Tier 5   Data & Memory  (Audit · Vector · Vault · Lineage)  │
└──────────────────────────────────────────────────────────────┘
           ▲              ▲              ▲
┌──────────────────────────────────────────────────────────────┐
│  Tier 6   Observability  (OTel · Evals · Metrics · Guards)   │
└──────────────────────────────────────────────────────────────┘
```

| Tier | Directory | Role |
|------|-----------|------|
| 0 — Governance | `src/tier0_policy/` | Policy engine, capability registry, feature flags |
| 1 — Interface | `src/tier1_interface/` | AuthN/Z, `TaskEnvelope` normalization, PII stripping |
| 2 — Orchestrator | `src/tier2_orchestrator/` | Planner, router, supervisor, quorum dispatcher, durable state |
| 3 — Specialist Agents | `src/tier3_agents/` | Stateless domain workers; each declares a `CapabilityManifest` |
| 4 — Tools & Services | `src/tier4_tools/` | Tool gateway + policy gate; all calls enforced here |
| 5 — Data & Memory | `src/tier5_data/` | Short-term scratchpad, long-term store, audit log, vault, lineage |
| 6 — Observability | `src/tier6_observability/` | OTel tracing, metrics, guardrails, eval harness |

---

## Key Invariants

- **Agents are stateless.** All state lives in the Orchestrator's `WorkflowRun` or Tier 5.
- **Agents never call tools directly.** Every call goes through `tier4_tools/gateway.py`, which runs a policy check before execution.
- **The Orchestrator is the only component that mutates workflow state.**
- **Policy is enforced by code, not prompts.** `tier0_policy/engine.py` evaluates every tool call independent of the LLM.
- **Quorum before consequential decisions.** Agents with `quorum_required: true` fan out to ≥3 independent model instances; the result is accepted only when `consistency_score ≥ threshold`.
- **New agents self-register** via `register_agent(capability, cls, manifest)` — no Orchestrator change needed.
- **Prompts are external assets** in `config/prompts/`, referenced by ID and version. Never inline prompts in code.
- **Workflows are declared** in `config/workflows/*.yaml`. Changing a workflow is a config change only.
- **Secrets never appear in prompts, logs, or environment variables.** Agents receive scoped, JIT tokens from `tier5_data/vault.py`.

---

## Shared Contracts

`src/shared/contracts.py` defines all canonical types (Pydantic v2). Never pass raw dicts between tiers.

| Type | Purpose |
|------|---------|
| `TaskEnvelope` | Normalized request produced by Tier 1 |
| `AgentRequest` | Typed input to a specialist, including prompt provenance |
| `AgentResponse` | Agent output with cost accounting and `consistency_score` |
| `ToolCall` | Typed tool invocation with idempotency key and `operation` class |
| `ToolResult` | Typed tool output including success/error state |
| `PolicyDecision` | Result of a policy engine evaluation |
| `HumanApproval` | Record of a HITL approval request and response |
| `AuditEvent` | Immutable, redacted audit record |

---

## Project Structure

```
config/
  agents/          # Capability manifests (tools, budgets, quorum config)
  models/          # Model registry (approval status, fallback chains)
  policy/          # Policy rules evaluated at runtime
  prompts/         # Versioned system prompts, one file per agent role
  workflows/       # Declared workflow DAGs (pattern, steps, budgets)
src/
  shared/          # contracts.py (Pydantic), exceptions.py, cache.py
  tier0_policy/    # engine.py, registry.py, feature_flags.py
  tier1_interface/ # auth.py, gateway.py, normalizer.py
  tier2_orchestrator/ # planner.py, router.py, supervisor.py,
                   #   state_machine.py, workflow_run.py, quorum_dispatcher.py
  tier3_agents/    # base_agent.py, specialists/
  tier4_tools/     # base_tool.py, gateway.py, policy_gate.py, adapters/
  tier5_data/      # audit_log.py, vault.py, lineage.py, memory/
  tier6_observability/ # tracing.py, guardrails.py, metrics.py, evals/
tests/
  unit/            # Tools with mocked dependencies; pure functions
  integration/     # Agent + tools with simulation harness
  replay/          # Deterministic replay from captured run bundles
  chaos/           # Fault injection: budget exhaustion, quorum failure, corrupt responses
docs/
  Multi_Tier_Agentic_Workflow_v2.md  # Full v2 reference design
```

---

## Setup

```bash
cp .env.example .env
# Fill in API keys, data store URLs, vault config, OTLP endpoint

pip install -e ".[dev]"
# or: pip install pydantic tenacity structlog opentelemetry-api opentelemetry-sdk pyyaml
```

---

## Quasi-Quorum Execution

For any agent invocation where the output drives a consequential action, use the quorum dispatcher:

```python
from src.tier2_orchestrator.quorum_dispatcher import QuorumDispatcher, QuorumConfig

dispatcher = QuorumDispatcher(QuorumConfig(min_instances=3, threshold=0.7))
response = dispatcher.dispatch(request, invoke_fn=my_invoke)
# response.consistency_score is set; QuorumFailure raised if below threshold
```

Set `quorum_required: true` in the agent's `config/agents/*.yaml` to signal to the router that this agent always requires quorum dispatch.

---

## Workflow State Machine

`WorkflowRun` in `tier2_orchestrator/workflow_run.py` tracks the 10-state durable lifecycle:

```
RECEIVED → VALIDATED → PLANNED → RUNNING → COMPLETED
                                 ↓
                         WAITING_FOR_TOOL
                         WAITING_FOR_HUMAN
                         RETRYING
                         FAILED
                         CANCELLED
```

Every transition is recorded with: previous state, next state, timestamp, actor, reason, input hash, output hash, policy result, trace ID.

---

## Orchestration Patterns

| Pattern | When to use |
|---------|-------------|
| `linear` | Deterministic sequential steps |
| `router` | Classify then dispatch to one of N agents |
| `fan_out` | N independent subtasks run in parallel, results aggregated |
| `plan_execute` | Open-ended tasks where the shape is data-dependent |
| `reflect_critique` | Quality over latency: generate → critique → refine |
| `event_driven` | Long-running async, multi-actor workflows |

---

## Adding a Specialist Agent

1. Create `src/tier3_agents/specialists/<name>_agent.py` subclassing `BaseAgent`.
2. Declare a `CapabilityManifest` on the class and call `register_agent()` at import time.
3. Add `config/agents/<name>_agent.yaml` with tools, budget, and quorum config.
4. Add `config/prompts/<name>_system.txt` with the versioned system prompt.
5. Add at least one `EvalCase` for this agent to `tests/unit/` or `tests/integration/`.

## Adding a Tool

1. Create `src/tier4_tools/adapters/<name>_tool.py` subclassing `BaseTool`.
2. Set `tool_id`, `operation_class`, and `requires_human_approval` explicitly.
3. Call `register_tool(MyTool())` at startup.
4. Add the tool to the allowlist in the relevant agent manifests.

---

## Error Handling

Failure classes in `src/shared/exceptions.py`:

| Exception | Failure class | Default recovery |
|-----------|--------------|-----------------|
| `TransientError` | `TRANSIENT_UPSTREAM` | Exponential backoff, retry up to budget |
| `SchemaValidationError` | `SCHEMA_VALIDATION_FAILED` | Re-prompt with error; escalate model |
| `PolicyDenied` | `POLICY_DENIED` | Halt or escalate to human |
| `QuorumFailure` | `LOW_CONFIDENCE` | Human escalation; do not auto-proceed |
| `HumanApprovalTimeout` | `HUMAN_APPROVAL_TIMEOUT` | Fail closed; alert on-call |
| `CircuitOpen` | `TOOL_TIMEOUT` | Circuit-break; use cached result if available |
| `CatastrophicError` | `CATASTROPHIC` | Circuit-break, alert, replay from checkpoint |

Mutating workflows use the saga pattern — each forward step must have a compensating undo registered.

---

## Reference Design

See [`Multi_Tier_Agentic_Workflow_v2.md`](Multi_Tier_Agentic_Workflow_v2.md) (root) or `docs/` for the full architecture guide including security model, quasi-quorum details, testing pyramid, sustainability, ethical AI, and a production launch checklist.
