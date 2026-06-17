# Architecture Map

## Core law

> **Entity proposes. Runtime disposes.**

The entity (`AgenticEntity`) plans and emits `CommandEnvelope` proposals.
The runtime (`AgenticRuntime`) alone decides whether a command is permitted,
how it executes, and how results are verified, traced, and remembered.

## Module map

| Module | Role |
|--------|------|
| `entity.py` | Cognitive organism: plan → execute loop, state machine outcomes |
| `runtime.py` | Governed command pipeline kernel |
| `policy.py` | Capability / permission / authority gates + risk re-score |
| `hitl.py` | Approval gates: auto, console, deny-all, preview-only |
| `approval.py` | Approval contracts, risk classes, policy resolver, previews (P0.15) |
| `budget.py` | Resource limits and budget ledger |
| `sandbox.py` | Workspace isolation backends (unsafe local, bwrap, docker) |
| `sandbox_policy.py` | Sandbox profiles, policy, path enforcement, diagnostics (P0.17) |
| `tools.py` | Tool Bus v1: registry/spec/metadata/context/result/error + dispatch |
| `tool_contracts.py` | Input/output schema contracts (P0.10) |
| `verifier.py` | Post-state verification + test integrity |
| `trace.py` | Hash-chained audit ledger (in-memory + persistent) |
| `memory.py` | Multi-tier memory fabric |
| `memory_governance.py` | Memory write governance + promotion (P0.9) |
| `skills.py` | Skill compilation and reflex promotion |
| `plan_validator.py` | Strict plan validation before execution |
| `model_router.py` | Swappable model client routing (mock default) |
| `model_providers/` | Optional structured-plan providers (mock/openai/anthropic/ollama) |
| `repo_agent.py` | Bounded repository task loop: context → deterministic/LLM plan → validation → patch → test → report |
| `demo_harness.py` | P0.20 demo harness: scenarios, factory, runner, honest reports, evidence writer (P0.19/P0.20) |
| `praxis.py` | Praxis memory metabolism seed: experience → candidates → promotion gates (P0.16) |
| `state_machine.py` | Execution status transitions |
| `status.py` | Lightweight runtime diagnostics |
| `cli.py` | Minimal CLI (`status`, `demo`, `verify`, `repo-task`, `approve-demo`, `praxis-*`, `sandbox-status`, `demo-harness`) |

## Command pipeline

```
Provider structured plan
  → Schema validation
  → PlanValidator
  → CommandEnvelope
  → Tool contract (input)     # registry + schema
  → Budget precheck
  → Policy                    # capability ≠ permission ≠ authority
  → Approval resolver         # risk class, preview, confirmation requirement
  → HITL / approver           # if required
  → Approval receipt trace
  → Sandbox profile check     # capability/path gate (P0.17)
  → Budget charge
  → Sandbox snapshot (writes)
  → Tool Bus execution        # registered tool handler inside sandbox
  → Tool contract (output)
  → State verifier
  → Rollback (failed writes)
  → Trace append
  → Governed memory update
  → ObservationEnvelope + VerifierResult
```

## Wiring

`build_runtime()` in `__init__.py` constructs a `Kernel` bundle:
sandbox, tools, policy, verifier, trace, memory, budget, router, skills, runtime.

Default sandbox: `UnsafeLocalSandbox` (demo/trusted only — not a security boundary).

## Repository Agent Loop

`RepositoryAgentLoop` is an application-level loop, not a new authority system.
It builds bounded repository context directly from the local repo, creates an
explicit `RepoTaskPlan` with deterministic, LLM, hybrid, or dry-run planning, then submits patch/test commands through
`AgenticRuntime.submit()` so policy, HITL, budget, sandbox, verifier, trace, and
memory governance still dispose execution.

```
RepoTaskRequest
  → RepoContextBuilder
  → CodeTaskPlanner / LLMRepoPlanner
  → RepoPlanValidator   # strict repository-plan schema + path/test constraints
  → PatchExecutor       # Runtime.submit(patch_file/write_file)
  → TestRunnerAdapter   # Runtime.submit(run_tests/run_shell)
  → TestFailureAnalyzer
  → RepairLoop          # bounded iterations
  → CodeTaskReport
  → PraxisMetabolism    # experience + memory candidates + PraxisReport (P0.16)
```

## Praxis memory metabolism (P0.16)

Trace is not memory. `PraxisMetabolism` captures `PraxisExperience` from command
results and repo reports, generates evidence-backed `MemoryCandidate` records,
evaluates conservative promotion to procedure/skill candidates, and submits
candidate-level writes through `memory_governance` — never auto-promoting canon.
Reflex eligibility checks document that runtime governance remains mandatory.

## Sandbox profiles (P0.17)

`SandboxPolicy` evaluates tools and paths against a declared `SandboxProfile`
before Tool Bus handlers run. `ProfiledSandbox` enforces filesystem boundaries
(traversal, secrets, workspace root). Docker/Bubblewrap profiles are honest
about availability — no silent downgrade to unsafe mode.

## LLM repository planning (P0.21)

`LLMRepoPlanner` uses `ModelRouter.complete_structured()` with a repository-plan schema. Providers return JSON only: objective summary, files to inspect/modify, proposed non-executing steps, risk, expected tests, approval flag, assumptions, and optional refusal. `RepoPlanValidator` rejects invalid JSON, missing fields, disallowed paths, excessive file counts, and test-file modifications unless explicitly allowed. Invalid LLM output becomes `planning_failed` in `llm` mode or a recorded deterministic fallback in `hybrid` mode.

The LLM never receives tool authority and never executes tools. Patch/test execution remains in `RepositoryAgentLoop → Runtime → Tool Bus → Approval → Sandbox → Verifier / Trace / Praxis`.
