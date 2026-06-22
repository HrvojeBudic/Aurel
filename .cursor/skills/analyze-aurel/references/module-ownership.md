# Module Ownership Map

Use this map to keep analysis and fixes local. Each module owns one decision domain.

## Core law

```text
Entity proposes. Runtime disposes.
```

`AgenticEntity` emits `CommandEnvelope` proposals. `AgenticRuntime` alone decides permission, execution, verification, trace, and memory.

## Runtime kernel

| Module | Owns |
|--------|------|
| `core_types.py` | Shared vocabulary, envelope/result types |
| `entity.py` | Planning loop, entity-side proposal behavior |
| `runtime.py` | Governed command pipeline kernel |
| `state_machine.py` | Execution status transitions |
| `status.py` | Lightweight runtime diagnostics |
| `plan_validator.py` | Strict plan validation before execution |

## Authority and gates

| Module | Owns |
|--------|------|
| `policy.py` | Capability / permission / authority gates, risk re-score |
| `approval.py` | Approval contracts, risk classes R0–R5, policy resolver, previews |
| `hitl.py` | Approval gates: auto, console, deny-all, preview-only |
| `budget.py` | Resource limits and budget ledger |

## Isolation and paths

| Module | Owns |
|--------|------|
| `canonical_path.py` | Path truth, normalization |
| `sandbox.py` | Workspace isolation backends (unsafe local, bwrap, docker) |
| `sandbox_policy.py` | Sandbox profiles, path enforcement, diagnostics |

## Tools and contracts

| Module | Owns |
|--------|------|
| `tools.py` | Tool Bus v1: registry, dispatch, handlers (**ExecutionToolRegistry**) |
| `tool_contracts.py` | Input/output schema contracts |
| `tool_manifest/` | Declarative manifest layer (**ManifestToolCatalog**) — validation, loader, registry, quarantine, drafts, events |

**Naming:** `tools.py` `ToolRegistry` = execution handlers. `tool_manifest/registry.py` `ToolRegistry` = capability metadata catalog. These are separate layers sealed at P1.3.9.

## Verification, trace, memory

| Module | Owns |
|--------|------|
| `verifier.py` | Post-state verification, protected test integrity |
| `trace.py` | Hash-chained audit ledger (in-memory + persistent) |
| `memory.py` | Multi-tier memory fabric |
| `memory_governance.py` | Memory write governance, promotion gates |
| `praxis.py` | Experience capture, memory candidates, promotion gates |
| `skills.py` | Skill compilation, reflex promotion |

## Model, prompts, secrets

| Module | Owns |
|--------|------|
| `model_config.py` | Provider/model profiles, runtime policy |
| `model_router.py` | Swappable model client routing |
| `model_providers/` | Structured-plan providers (mock/openai/anthropic/ollama) |
| `secrets.py` | Env-only secret resolution and redaction |
| `prompt_system.py` | Prompt manifests, registry, rendering, trace-safe summaries |

## Identity (P1.4)

| Module | Owns |
|--------|------|
| `identity/` | Identity Kernel, Persona Manifest, Operator Contract, Communication Modes, Self-Model, Agent Identity Card — loaders, validators, hashes |
| `config/aurel/` | Canonical YAML configs for identity layers |
| `autonomy/`, `governance/`, `heretic/`, `metacognition/`, `compliance/` | P1.4 placeholders — no runtime integration yet |

## Application loops

| Module | Owns |
|--------|------|
| `repo_agent.py` | Bounded repository task loop — still submits through Runtime |
| `demo_harness.py` | Demo scenarios, factory, runner, evidence writer |
| `demo.py`, `cli.py` | Public demonstrations and command entrypoints |

## Ownership rules

1. Policy decisions stay in `policy.py`, `approval.py`, `hitl.py` — not in tools or entity.
2. Execution stays in sandbox + Tool Bus — not in manifest or prompt layers.
3. Verification stays in `verifier.py` — not in runtime orchestration.
4. Manifest/registry visibility does not grant execution — policy and sandbox still dispose.
5. Repository-agent planning proposes work; mutation and tests go through `Runtime.submit()`.
6. Identity/persona layers are read/validate only until wired into runtime boot.

## Wiring entrypoint

`build_runtime()` in `__init__.py` constructs the `Kernel` bundle: sandbox, tools, policy, verifier, trace, memory, budget, router, skills, runtime.

Default sandbox: `UnsafeLocalSandbox` (demo/trusted only — not a production security boundary).
