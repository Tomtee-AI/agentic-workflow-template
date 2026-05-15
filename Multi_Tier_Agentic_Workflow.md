# Multi-Tier Agentic Workflow

**Reference Design & Implementation Guide**
Version 1.0 — May 2026
Prepared for: Tomtee

---

## Table of Contents

1. Executive Summary
2. Architecture at a Glance
3. Tier Definitions
4. Design Best Practices by Tier
5. Code Optimization and Reusability
6. Data Security
7. Modularity and Flexibility
8. Error Handling and Resilience
9. Orchestration Patterns
10. Scheduling
11. Implementation Checklist
12. Anti-Patterns to Avoid
13. Glossary

---

## 1. Executive Summary

This document specifies a generic, vendor-neutral architecture for production-grade agentic workflows. It is intended to be cloned, adapted, and extended for any domain in which one or more LLM-driven agents collaborate with tools, services, and human reviewers to complete multi-step tasks.

The architecture is organized into six tiers separated by stable contracts: Interface, Orchestrator, Specialist Agents, Tools & Services, Data & Memory, and Observability. Each tier can be replaced, scaled, or upgraded independently provided its contract is preserved. This separation is the central design lever for security, reusability, and resilience.

The remainder of this document defines each tier, articulates the cross-cutting concerns (best practices, optimization, security, modularity, error handling), and prescribes orchestration and scheduling patterns with concrete checklists.

---

## 2. Architecture at a Glance

The reference architecture below is the canonical mental model. Read top-down for request flow; bottom-up for trust and data lineage.

| Tier | Role |
|------|------|
| **Tier 1 — Interface** | User entry, API gateway, request normalization, AuthN/AuthZ. |
| **Tier 2 — Orchestrator** | Planner, router, state machine, supervisor agent, queueing. |
| **Tier 3 — Specialist Agents** | Domain-scoped agents (research, code, finance, ops). Stateless workers. |
| **Tier 4 — Tools & Services** | MCP servers, APIs, RPA scripts, vector search, code sandbox. |
| **Tier 5 — Data & Memory** | Short-term context, long-term store, audit log, secrets vault. |
| **Tier 6 — Observability** | Tracing, metrics, evals, cost tracking, guardrails. |

```
   ┌──────────────────────────────────────────────────────┐
   │  Tier 1   Interface (Auth, Gateway, Normalization)   │
   └──────────────────────────────────────────────────────┘
                          │ TaskEnvelope
   ┌──────────────────────▼───────────────────────────────┐
   │  Tier 2   Orchestrator (Planner • Router • State)    │
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
   │  Tier 6   Observability (Traces • Evals • Guards)    │
   └──────────────────────────────────────────────────────┘
```

Contracts between tiers are explicit, versioned, and machine-checkable. A higher tier never reaches across an intermediate tier; for example, the Orchestrator does not call vendor APIs directly — it dispatches to a Specialist Agent that calls a Tool that calls the API. This indirection is what makes the system swappable and testable.

---

## 3. Tier Definitions

### 3.1 Tier 1 — Interface

Responsibility: receive, authenticate, and normalize every request, whether it originates from a human (chat, web, CLI), a scheduler, an inbound webhook, or another system.

- Authentication: OAuth / OIDC / mTLS at the edge; never propagate raw credentials inward.
- Normalization: convert requests to a canonical `TaskEnvelope` (`id`, `intent`, `payload`, `principal`, `trace_id`, `deadline`).
- Rate limiting, idempotency keys, and request shaping live here — not in the agents.
- PII/secret stripping at the boundary: requests are scrubbed and redacted before being handed to the Orchestrator.

### 3.2 Tier 2 — Orchestrator

Responsibility: decide what happens, in what order, by whom, and under what budget. The Orchestrator is the only component allowed to mutate workflow state.

- Planner: decomposes an intent into a DAG (or graph) of steps. Can be LLM-driven, deterministic, or hybrid.
- Router: selects the right Specialist Agent per step based on capability registry and policy.
- Supervisor: monitors progress, enforces budgets (tokens, dollars, latency, retries), and triggers fallbacks.
- State machine: durable, idempotent transitions persisted to the Data tier.

### 3.3 Tier 3 — Specialist Agents

Responsibility: execute a bounded slice of cognitive work using a constrained toolset and a tightly scoped system prompt.

- Agents are stateless. All state lives in the Orchestrator's state machine or in Tier 5.
- Each agent declares a capability manifest: inputs, outputs, allowed tools, cost class, latency class, safety class.
- Agents are versioned. The router pins a version per workflow run.
- Prefer many small specialists over one super-agent: smaller prompts are cheaper, safer, and more testable.

### 3.4 Tier 4 — Tools & Services

Responsibility: do the world-affecting work — read data, write data, call APIs, run code, search the web, send messages.

- Tools must be pure functions of their declared inputs whenever possible. Side effects are explicit in the tool manifest.
- Use a tool gateway (e.g., MCP) to standardize discovery, schema, auth, and audit.
- Destructive operations (delete, send, charge, deploy) require an explicit policy gate and — by default — a human-in-the-loop confirmation.

### 3.5 Tier 5 — Data & Memory

Responsibility: durable state, working memory, long-term knowledge, and the audit record.

- Short-term memory: per-run scratchpad, bounded and discarded at run end.
- Long-term memory: vector store + relational store, with explicit write paths and TTLs.
- Secrets vault: dedicated KMS/secret manager. Agents receive scoped, time-bound tokens, never raw secrets.
- Audit log: append-only, immutable, contains every decision, tool call, prompt, and response.

### 3.6 Tier 6 — Observability

Responsibility: make the system understandable in production. If you cannot see it, you cannot ship it.

- Distributed tracing: every span tagged with `trace_id`, `run_id`, `agent`, `tool`, `model`, `tokens`, `cost`, `latency`.
- Metrics: success rate, p50/p95 latency, retry rate, cost per task, eval scores.
- Evaluations: offline regression suite plus live shadow evals on a sampled fraction of traffic.
- Guardrails: prompt-injection detection, output content filters, schema validators on every LLM response.

---

## 4. Design Best Practices by Tier

The matrix below summarizes the canonical "do/avoid" pattern for each tier. Treat it as a code-review checklist.

| Tier | Do | Avoid |
|------|----|-------|
| Interface | Normalize to TaskEnvelope; strip PII; enforce idempotency keys. | Letting raw requests reach agents; trusting client-supplied trace IDs. |
| Orchestrator | Persist state on every transition; budget every step. | Hidden state in agent prompts; unbounded loops. |
| Specialist Agents | Small prompts; explicit output schema; deterministic temperature where possible. | Generalist mega-agents; free-form output the orchestrator must parse heuristically. |
| Tools & Services | Typed schemas; idempotent writes; least privilege. | Tools with hidden side effects; shared service accounts. |
| Data & Memory | TTLs; tenant isolation; encryption at rest and in transit. | Mixed-tenant vector indexes; secrets in prompts or logs. |
| Observability | Trace every call; sample evals; alert on drift. | Logging full prompts without redaction; per-team siloed dashboards. |

---

## 5. Code Optimization and Reusability

Reusability comes from disciplined separation of stable contracts (slow-changing) from implementations (fast-changing). The recurring pattern: define the contract as a schema, ship an interface, swap implementations behind it.

### 5.1 Shared Primitives

- `TaskEnvelope`, `AgentResponse`, `ToolCall`, `ToolResult`: a single library, versioned with semver, consumed by every tier.
- Prompt library: prompts are code. Store them in source control, lint them, unit test them, version them.
- Tool adapter SDK: one base class handles auth, retries, schema validation, tracing. Concrete tools subclass it.
- Eval harness: shared across teams. New agents do not ship without entries in the shared eval suite.

### 5.2 Caching Strategy

- Prompt-response cache keyed by `(model, prompt_hash, tool_set_hash, retrieval_hash)`. Honors invalidation on prompt or tool change.
- Tool-result cache for idempotent reads (search, fetch, lookup) with TTLs aligned to data freshness needs.
- Embedding cache: never re-embed the same document chunk; key by content hash + model version.
- Negative cache: remember known-failed inputs to avoid re-trying poisoned data.

### 5.3 Cost and Latency Levers

- Model cascading: try the smallest model first; escalate on low confidence or failed schema validation.
- Parallel fan-out: independent subtasks dispatched concurrently; the Orchestrator waits on the join.
- Streaming: stream agent output where the consumer can act incrementally (UX, downstream pipelines).
- Prompt compression: summarize long histories; pin only what the next step provably needs.

---

## 6. Data Security

Treat the agent layer as untrusted code reading untrusted data. Every security control assumes the LLM can be coerced via prompt injection — because it can.

### 6.1 Identity and Access

- Principal propagation: the end user's identity flows in the TaskEnvelope; tools authorize against it, not the agent's identity.
- Scoped, short-lived credentials: agents request a token per tool call from the vault; tokens expire in minutes.
- Least privilege: each agent's tool manifest is the maximum it can do, enforced at the gateway, not in the prompt.

### 6.2 Data Handling

- Classify data on ingest (public, internal, confidential, restricted). Classification follows the data through every tier.
- Encrypt in transit (TLS 1.3) and at rest (envelope encryption with KMS-managed keys).
- Tenant isolation in vector and relational stores: separate indexes/schemas, never row-level only.
- PII minimization: redact at ingress, re-hydrate at egress only for authorized principals.

### 6.3 Prompt-Injection Defense

- Separate trusted instructions from untrusted content using structured templates (system vs. retrieved-context channels).
- Sanitize retrieved content: strip imperatives, URLs, and tool-call syntax before injection.
- Output guardrails: validate every tool call against a policy engine before execution; reject calls that would exfiltrate data, escalate scope, or violate user consent.
- Treat the LLM as a confused deputy: never let its output, alone, authorize a destructive action.

### 6.4 Auditability

- Every prompt, every tool call, every model output, every decision is captured in an immutable, queryable log.
- Logs are redacted at write time, not read time; raw PII never lands in the warehouse.
- Retention is data-class-aware and aligned with applicable regulation (GDPR, HIPAA, SOC 2, etc.).

---

## 7. Modularity and Flexibility

The system is modular if you can replace any one component over a weekend without a coordinated multi-team release. Achieve this by treating every boundary as a contract, not a courtesy.

### 7.1 Plugin Model for Agents and Tools

- Capability registry: a single source of truth that lists every agent and tool, its version, its schema, and its policy.
- Hot-swap: routing decisions consult the registry at run time; new agents register themselves, no code change in the Orchestrator.
- Feature flags: per-tenant, per-workflow flags toggle new agents/tools in shadow, canary, then general availability.

### 7.2 Configuration over Code

- Workflows are declared (YAML/JSON) and interpreted by the Orchestrator. The code path doesn't change when the workflow does.
- Model selection, retry policy, budgets, and tool allowlists are config, not constants.
- Prompts are external assets, fetched by ID + version, never inlined in code that's hard to diff.

### 7.3 Multi-Model and Multi-Vendor

- A model gateway abstracts vendor APIs (Anthropic, OpenAI, on-prem, etc.) behind a common request/response shape.
- Per-step model choice driven by routing policy: capability + cost + latency + data residency.
- Fallback chains: if vendor A is degraded, the gateway transparently re-issues to vendor B with the same prompt.

---

## 8. Error Handling and Resilience

Agentic systems fail in more shapes than traditional systems: timeouts, rate limits, malformed JSON, hallucinated tool calls, schema drift, policy denials, partial success, and cascading retries. Design for them explicitly.

### 8.1 Failure Taxonomy

| Class | Example | Recovery |
|-------|---------|----------|
| Transient | 429 rate limit; 502 from upstream. | Exponential backoff + jitter; retry up to budget. |
| Schema | LLM returned invalid JSON; missing field. | Re-prompt with the validator error; fall back to stricter model. |
| Policy | Tool call denied by guardrail. | Surface to supervisor; halt or escalate to human. |
| Semantic | Plausible but wrong answer. | Caught by evals or downstream verification; flag and retry with a different strategy. |
| Catastrophic | Vendor outage; data corruption. | Circuit-break, fail closed, alert on-call, replay from durable state. |

### 8.2 Retry, Timeout, Budget

- Every step has an explicit timeout, an explicit retry policy, and an explicit budget (tokens + dollars + wall-clock).
- Budgets are cumulative across the run; the Supervisor halts the run when any budget is exhausted.
- Retries are idempotent by construction: tool calls carry a client-generated idempotency key.

### 8.3 Compensating Actions and Sagas

- Multi-step workflows that mutate external state use the saga pattern: each forward step has a compensating undo.
- On failure, the Orchestrator runs compensations in reverse order until the system is in a known-good state.
- Compensations are first-class, tested, and themselves versioned.

### 8.4 Human-in-the-Loop Escalation

- Define the exact triggers for human escalation: confidence < threshold, policy denial, repeated failure, ambiguous intent, high-blast-radius action.
- Pause the workflow durably (state persisted) and notify the right human via the right channel (UI, email, paging).
- On resume, re-validate context — the world may have changed while paused.

---

## 9. Orchestration Patterns

Pick the simplest pattern that handles your workload. Composability comes from nesting them, not from one mega-orchestrator that does everything.

### 9.1 Linear Pipeline
A → B → C, each step's output is the next step's input. Best for deterministic, well-understood flows (e.g., ingest → enrich → store).

### 9.2 Router / Dispatcher
A classifier (LLM or rules) routes the request to one of N specialists. Best for triage problems (support, intake, classification).

### 9.3 Parallel Fan-out / Aggregator
Dispatch N independent subtasks concurrently, then aggregate results. Best for research, comparison, multi-source synthesis.

### 9.4 Plan-and-Execute
A planner produces a DAG; executors run nodes; a supervisor checks invariants after each node. Best for open-ended tasks where the shape is data-dependent.

### 9.5 Reflect-and-Critique Loop
Generator → Critic → Refiner, bounded by max iterations and quality threshold. Best for writing, code, design tasks where quality > latency.

### 9.6 Supervisor / Worker Hierarchy
A supervisor agent decomposes, delegates to workers, validates results, and recomposes. Best for complex tasks needing dynamic decomposition.

### 9.7 Event-Driven / Reactive
Agents subscribe to events on a bus and react. Best for long-running, asynchronous, multi-actor workflows (operations, monitoring).

---

## 10. Scheduling

Scheduling spans two distinct concerns: when work is initiated, and how it is queued, prioritized, and dispatched.

### 10.1 Trigger Modalities

- On-demand: human or system request through the Interface tier.
- Time-based: cron-style schedules for periodic batch (digests, reports, syncs).
- Event-driven: webhooks, message buses, change-data-capture from databases.
- Condition-based: poll-and-trigger when a watched metric or threshold flips.
- Chained: workflow completion triggers downstream workflows.

### 10.2 Queueing and Prioritization

- Durable queues between tiers: a crashed worker never loses a task.
- Priority lanes: interactive (low-latency), batch (cost-optimized), background (best-effort).
- Fair scheduling across tenants and per-user concurrency caps.
- Backpressure: when downstream is saturated, slow ingestion at the Interface, do not silently drop.

### 10.3 Concurrency and Resource Governance

- Token-bucket rate limits per tenant, per model, per tool.
- Worker pools sized to the slowest dependency — not the fastest.
- Cost ceilings per workflow, per tenant, per day; alert before they bind, halt when they do.

### 10.4 Long-Running and Recurring Workflows

- Durable execution engine (e.g., Temporal-style) makes a multi-day workflow look like a function call.
- Checkpoints at every step; resume from the last successful checkpoint after restarts.
- Idempotency at every external side effect; replays must not double-charge, double-send, double-deploy.

---

## 11. Implementation Checklist

Use this as a launch readiness gate. A workflow is not production-ready until every box is checked or has a documented, time-bound exception.

1. Each tier has an owner, an on-call rotation, and a runbook.
2. TaskEnvelope schema is versioned and consumed end to end.
3. Every agent has a capability manifest, a system prompt under version control, and a row in the eval suite.
4. Every tool has a typed schema, an idempotency strategy, and a policy gate.
5. Secrets never appear in prompts, logs, traces, or environment variables loaded by agents.
6. Tenants are isolated in every data store; isolation is tested, not assumed.
7. Prompt-injection guardrails are active on every retrieval path.
8. Distributed tracing covers every span; cost and tokens are tagged.
9. Budgets, timeouts, and retry policies are explicit per step and tested under load.
10. Saga compensations exist for every mutating workflow and are exercised in chaos drills.
11. Human-in-the-loop triggers are defined, routed, and acknowledged within SLA.
12. A shadow eval runs against live traffic on a continuous, sampled basis.
13. Disaster recovery: state can be replayed from the audit log to reconstruct any run.

---

## 12. Anti-Patterns to Avoid

- "One mega-agent" with hundreds of tools and a 50-page prompt. It will be slow, expensive, and unsafe.
- State stored in agent context only. Crashes lose work; you cannot resume or audit.
- Trusting LLM output to authorize an action. Always validate against a policy engine independent of the model.
- Prompts inlined in code, copy-pasted across services. They will drift, and quality regressions will be invisible.
- Retries without idempotency keys. You will eventually double-charge a customer.
- Logging full prompts and responses to a shared warehouse. You will eventually leak PII or secrets.
- Treating evals as a launch milestone instead of a continuous control.

---

## 13. Glossary

| Term | Definition |
|------|------------|
| Agent | An LLM-driven component with a bounded role, a scoped toolset, and a versioned prompt. |
| Capability Manifest | Declarative description of an agent's inputs, outputs, allowed tools, and policy class. |
| Guardrail | A pre- or post-call check (policy, schema, content) that gates LLM output. |
| Idempotency Key | Client-generated identifier that lets a tool deduplicate repeated calls safely. |
| MCP | Model Context Protocol — a standardized interface for tools and resources consumed by agents. |
| Orchestrator | The component that owns workflow state and decides which agent runs next. |
| Saga | A pattern of compensating actions used to undo partial work on failure. |
| TaskEnvelope | The canonical request shape carrying intent, payload, principal, and trace metadata. |
| Tier | A horizontally separated layer of the architecture with a stable contract to its neighbors. |
