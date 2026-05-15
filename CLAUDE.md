# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture

This project is a template for a production-grade, multi-tier agentic AI application based on the [Multi-Tier Agentic Workflow reference design](docs/Multi_Tier_Agentic_Workflow.md). The six tiers are strictly separated; a higher tier never reaches across an intermediate tier.

| Tier | Directory | Role |
|------|-----------|------|
| 1 — Interface | `src/tier1_interface/` | AuthN/AuthZ, request normalization into `TaskEnvelope`, PII stripping |
| 2 — Orchestrator | `src/tier2_orchestrator/` | Planner (DAG), Router (capability registry), Supervisor (budgets), State machine |
| 3 — Specialist Agents | `src/tier3_agents/` | Stateless domain workers; each declares a `CapabilityManifest` |
| 4 — Tools & Services | `src/tier4_tools/` | MCP/API adapters; all tool calls go through `gateway.py`, not directly |
| 5 — Data & Memory | `src/tier5_data/` | Short-term scratchpad, long-term store, append-only audit log |
| 6 — Observability | `src/tier6_observability/` | Distributed tracing, guardrails, evals |

### Shared contracts (`src/shared/`)

`contracts.py` defines the four canonical types used across every tier:
- `TaskEnvelope` — the normalized request that flows from Tier 1 downward
- `ToolCall` / `ToolResult` — typed tool invocations with idempotency keys
- `AgentResponse` — typed agent output including token/cost accounting

All inter-tier data transfer uses these types. Never pass raw dicts between tiers.

### Key invariants

- **Agents are stateless.** All state lives in the Orchestrator's state machine (`tier2_orchestrator/state_machine.py`) or in Tier 5.
- **Agents never call tools directly.** They go through `tier4_tools/gateway.py`, which enforces the agent's `allowed_tools` list at runtime.
- **The Orchestrator is the only component that mutates workflow state.**
- **New agents self-register** via `router.register_agent(capability, cls)` — no change to the Orchestrator is needed.
- **Prompts are external assets** in `config/prompts/`, fetched by name+version. Never inline prompts in code.
- **Workflows are declared** in `config/workflows/*.yaml` and interpreted by the Orchestrator. Changing a workflow requires only a config change.
- **Secrets never appear in prompts, logs, or environment variables loaded by agents.** Agents receive scoped, short-lived tokens from the vault.

## Setup

```bash
cp .env.example .env
# fill in .env values
pip install -r requirements.txt   # add when dependencies are locked
```

## Configuration

| Location | Purpose |
|----------|---------|
| `config/agents/*.yaml` | Capability manifests: allowed tools, budgets, cost/latency/safety class |
| `config/workflows/*.yaml` | Declared workflow DAGs (pattern + steps) |
| `config/prompts/*.txt` | Versioned system prompts, one file per agent role |
| `config/tools/*.yaml` | Tool schemas and policy gates |

## Adding a new specialist agent

1. Create `src/tier3_agents/specialists/<name>_agent.py` subclassing `BaseAgent`.
2. Declare a `CapabilityManifest` on the class.
3. Call `register_agent("<capability>", MyAgent)` at module import time.
4. Add a manifest file at `config/agents/<name>_agent.yaml`.
5. Add a system prompt at `config/prompts/<name>_system.txt`.
6. Add the agent to at least one eval in `tests/evals/`.

## Adding a new tool

1. Create `src/tier4_tools/adapters/<name>_tool.py` subclassing `BaseTool`.
2. Set `has_side_effects` and `requires_human_approval` explicitly.
3. Call `register_tool(MyTool())` and add a schema to `config/tools/`.

## Orchestration patterns

Choose the simplest pattern in `config/workflows/`:

| Pattern | When to use |
|---------|-------------|
| `linear` | Deterministic sequential steps |
| `router` | Classify then dispatch to one of N agents |
| `fan_out` | N independent subtasks run in parallel, results aggregated |
| `plan_execute` | Open-ended tasks where shape is data-dependent |
| `reflect_critique` | Quality-over-latency: generate → critique → refine |
| `event_driven` | Long-running async, multi-actor workflows |

## Error handling

Failure classes and their recovery strategies are in `src/shared/exceptions.py`. Every step must declare an explicit timeout, retry policy, and budget in its workflow YAML. Mutating workflows require saga compensations.
