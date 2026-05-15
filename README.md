# Agentic Workflow Template

A production-grade, multi-tier agentic AI application template. Clone it, fill in your domain logic, and ship a system that is secure, observable, and maintainable from day one.

## Architecture

Six tiers with strict separation — a higher tier never reaches across an intermediate one.

```
┌──────────────────────────────────────────────────────┐
│  Tier 1   Interface (Auth, Gateway, Normalization)   │
└──────────────────────────────────────────────────────┘
                       │ TaskEnvelope
┌──────────────────────▼───────────────────────────────┐
│  Tier 2   Orchestrator (Planner · Router · State)    │
└──────────────────────────────────────────────────────┘
           │            │             │
           ▼            ▼             ▼
┌────────────────┐ ┌────────────┐ ┌────────────────┐
│ Specialist A   │ │ Specialist │ │ Specialist N   │   ← Tier 3
└────────────────┘ └────────────┘ └────────────────┘
           │            │             │
           ▼            ▼             ▼
┌──────────────────────────────────────────────────────┐
│  Tier 4   Tools & Services (MCP, APIs, Sandboxes)    │
└──────────────────────────────────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────────┐
│  Tier 5   Data & Memory (Vector, Relational, Vault)  │
└──────────────────────────────────────────────────────┘
           ▲            ▲             ▲
           │            │             │
┌──────────────────────────────────────────────────────┐
│  Tier 6   Observability (Traces · Evals · Guards)    │
└──────────────────────────────────────────────────────┘
```

| Tier | Directory | Role |
|------|-----------|------|
| 1 — Interface | `src/tier1_interface/` | AuthN/AuthZ, request normalization into `TaskEnvelope`, PII stripping |
| 2 — Orchestrator | `src/tier2_orchestrator/` | Planner (DAG), Router (capability registry), Supervisor (budgets), State machine |
| 3 — Specialist Agents | `src/tier3_agents/` | Stateless domain workers; each declares a `CapabilityManifest` |
| 4 — Tools & Services | `src/tier4_tools/` | MCP/API adapters; all calls go through `gateway.py` |
| 5 — Data & Memory | `src/tier5_data/` | Short-term scratchpad, long-term store, append-only audit log |
| 6 — Observability | `src/tier6_observability/` | Distributed tracing, guardrails, evals |

## Key Invariants

- **Agents are stateless.** All state lives in the Orchestrator's state machine or Tier 5.
- **Agents never call tools directly.** Every tool call goes through `tier4_tools/gateway.py`, which enforces each agent's `allowed_tools` list at runtime.
- **The Orchestrator is the only component that mutates workflow state.**
- **New agents self-register** via `router.register_agent(capability, cls)` — no change to the Orchestrator needed.
- **Prompts are external assets** in `config/prompts/`, fetched by name and version. Never inline prompts in code.
- **Workflows are declared** in `config/workflows/*.yaml`. Changing a workflow requires only a config change.
- **Secrets never appear in prompts, logs, or environment variables loaded by agents.** Agents receive scoped, short-lived tokens from the vault.

## Shared Contracts

`src/shared/contracts.py` defines the four canonical types used across every tier:

| Type | Purpose |
|------|---------|
| `TaskEnvelope` | Normalized request produced by Tier 1 and consumed downward |
| `ToolCall` | Typed tool invocation with an idempotency key |
| `ToolResult` | Typed tool output including success/error state |
| `AgentResponse` | Agent output with token and cost accounting |

Never pass raw dicts between tiers.

## Project Structure

```
config/
  agents/          # Capability manifests (allowed tools, budgets, safety class)
  prompts/         # Versioned system prompts, one file per agent role
  tools/           # Tool schemas and policy gates
  workflows/       # Declared workflow DAGs
src/
  shared/          # contracts.py, exceptions.py, cache.py
  tier1_interface/ # auth.py, gateway.py, normalizer.py
  tier2_orchestrator/ # planner.py, router.py, supervisor.py, state_machine.py
  tier3_agents/    # base_agent.py, specialists/
  tier4_tools/     # base_tool.py, gateway.py, adapters/
  tier5_data/      # audit_log.py, memory/
  tier6_observability/ # tracing.py, guardrails.py, evals/
tests/
docs/
  Multi_Tier_Agentic_Workflow.md  # Full reference design
```

## Setup

```bash
cp .env.example .env
# Fill in API keys, data store URLs, vault config, and OTLP endpoint
pip install -r requirements.txt
```

## Orchestration Patterns

Choose the simplest pattern that fits your workload. Compose them by nesting, not by building a mega-orchestrator.

| Pattern | When to use |
|---------|-------------|
| `linear` | Deterministic sequential steps |
| `router` | Classify then dispatch to one of N agents |
| `fan_out` | N independent subtasks run in parallel, results aggregated |
| `plan_execute` | Open-ended tasks where the shape is data-dependent |
| `reflect_critique` | Quality over latency: generate → critique → refine |
| `event_driven` | Long-running async, multi-actor workflows |

## Adding a Specialist Agent

1. Create `src/tier3_agents/specialists/<name>_agent.py` subclassing `BaseAgent`.
2. Declare a `CapabilityManifest` on the class.
3. Call `register_agent("<capability>", MyAgent)` at module import time.
4. Add a manifest at `config/agents/<name>_agent.yaml`.
5. Add a system prompt at `config/prompts/<name>_system.txt`.
6. Add the agent to at least one eval in `tests/evals/`.

## Adding a Tool

1. Create `src/tier4_tools/adapters/<name>_tool.py` subclassing `BaseTool`.
2. Set `has_side_effects` and `requires_human_approval` explicitly.
3. Call `register_tool(MyTool())` and add a schema to `config/tools/`.

## Error Handling

Failure classes and recovery strategies are defined in `src/shared/exceptions.py`. Every workflow step must declare an explicit timeout, retry policy, and budget in its YAML. Mutating workflows use the saga pattern — each forward step has a compensating undo.

## Reference Design

See [`docs/Multi_Tier_Agentic_Workflow.md`](docs/Multi_Tier_Agentic_Workflow.md) for the full architecture guide, including security model, caching strategy, anti-patterns, and a production launch checklist.
