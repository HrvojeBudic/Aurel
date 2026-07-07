# AUREL-DUAL-KERNEL-TRACKB — Dual governance kernel + master-plan Phase 0 + Track B

**Date:** 2026-07-07
**Task ID:** AUREL-DUAL-KERNEL-TRACKB
**Type:** Feature block (additive, behind flags)
**Status:** DONE — full suite sealed, ready to merge to `master`
**Branch:** `feat/dual-kernel-sigma-merge-gate` (15 commits ahead of `master`)

---

## Purpose

Two things, delivered as one strictly-additive, flag-gated block over the sealed
P5 spine:

1. A **dual governance kernel** — a Custos (govern) / Praxis (execute) layer with
   a canon-faithful merge gate, so risky/"heretic" speculative work can run and be
   verified before it touches live state, without weakening any existing gate.
2. Adoption of the operator's **AUREL UPGRADE MASTER PLAN** — landing its whole
   **Phase 0 foundation** and its complete **Track B** (reasoning scheduler), then
   reconciling Track C with the dual kernel.

Everything is additive behind feature flags; every flag defaults OFF and the
disabled path is byte-identical to the pre-existing behavior.

## What landed (15 commits)

**Dual kernel (`src/agentic_runtime/dual_kernel/`, flag `AUREL_DUAL_KERNEL`):**
- Σ governance state-vector (O(1) monotone sufficient statistic; two-phase
  register/admit), autonomy-index routing (FAST / GOVERNED / HARD_GATED), hard/soft
  constraints with the ABC bounded-recovery bound.
- Merge gate: ABC compositionality C1–C4 + DSD Book 12 readiness verdict ladder;
  `commit()` is the only live-state mutation and merges only on a PASS verdict.
- Machine-readable NC firewall (`nc_merge_bindings.json` + `validate_coverage`) —
  every merge-gate check is bound to a DSD no-collapse law, enforced at construction.
- Praxis orchestrator (fork → execute → gate → commit); `DualKernelRuntime` facade;
  tamper-evident hash-chained decision ledger; `dual-kernel` read-only CLI.
- CAS materialize-to-live (`AUREL_DK_MATERIALIZE`): execute once in a CAS fork,
  then clear-then-materialize the post-state into the live workspace with a
  `state_hash()` self-verify guard and a faithful `_append_transition`.

**Master-plan Phase 0 (foundation):**
- P0-S.1 truthful token/cost accounting — killed the fictional flat
  `usd=0.01 / estimated_tokens=1200`; providers populate real `usage`; new
  `reasoning/` package with `TokenAccountingView` (`substantiated` unconstructible-
  True); `estimate_only` honesty flag; live wiring in `entity.plan` (precheck →
  `complete_with_usage` → charge real usage), numerically identical under the mock.
- P0-S.2 shared reasoning/simulation budget seam — `charge_reasoning`,
  `charge_simulation`, and caps (`max_thinking_tokens/-calls`,
  `max_reasoning_passes_per_run`, `max_simulation_execs`) through `_check()`. The
  dual-kernel speculative fork now charges `charge_simulation`.
- P0-S.3 `retain_states` gated default — writer classes (CORE/EXECUTION) retain
  state (and get an auto-provisioned StateStore) by default; every other class
  stays byte-identical (OFF, no store); explicit `retain_states` always wins.

**Track B — reasoning scheduler (`reasoning/`, flag `AUREL_REASONING_SCHEDULER`):**
B1 ThinkingBudget (deny-by-default clamp, per-class resolver, no AgentCard change),
B2 deterministic fail-closed difficulty estimator, B3 adaptive System-1/2 profile
allocation bound into `entity.plan` (fail-closed selection), B4 hash-chained
`reasoning_allocation` trace event (reused `PraxisEventRecord`), B5 heuristic PRM
step verifier + bounded LLM replan (`max_reasoning_passes_per_run` cap alive;
`model_judge_available` structurally False; PRM verdict never verified truth),
B6 read-only `WorkloadView` + `reasoning status`/`reasoning workload` CLI.

**Track C reconcile:** the dual kernel now emits a non-canonical
`simulation_decision` trace event (is_speculative / advisory; a `PraxisEventRecord`,
never a `StateTransitionRecord`) so the speculative verdict is auditable as evidence
in the single source of truth.

## Invariants preserved (checked)

- Entity proposes, runtime disposes; no second executor introduced. Nothing reaches
  LIVE source state without a PASS verdict over real (not claimed) evidence.
- Trace is the single source of truth; new records are hash-chained; speculative and
  PRM records are distinctly labeled and never canonical transitions / verified truth.
- Fail-closed everywhere (routing, profile selection, PRM escalation, budget caps).
- No-overclaim: `substantiated` and `model_judge_available` are structurally
  unconstructible-True; the flat-cost overclaim is removed.
- Additive-behind-flags: every flag defaults OFF and the disabled path is
  byte-identical (proven by dedicated flag-off tests + the full suite).

## Result (seal)

- **HEAD:** `7e294fac6ffe9cc32da71b252690620967936065`, clean tree.
- **Command:** `AGENTIC_SKIP_RECURSIVE_SMOKE=1 .venv/bin/python -m pytest -q -p no:cacheprovider`
  (canonical full suite), run to completion in the background.
- **Outcome:** **8535 passed, 11 skipped, 0 failed** — `PYTEST_EXIT=0`. Duration
  1828.74s (30:28). Baseline before this block was 8434 passed (AUREL-SEAL-01);
  the +101 net are this block's new tests.
- Each major phase was independently sealed on the full suite along the way
  (8477 → 8495 → 8516 → 8526 → 8535). `ruff` and `mypy` clean on all touched modules.
- **Environment:** local venv, Linux 6.17, functional bubblewrap hard sandbox.

## What was deliberately not run

- `--cov` and `bandit` — optional operator seal extras (each adds significant
  runtime); not required for the pass/fail seal. Last recorded coverage 89.21%.

## Remaining seams (documented, deferred)

- Materialize path budget/memory mirror (the preflight path already carries full
  budget/memory via the real submit; materialize trades that for single-execution).
- Track C C6/C7 (sim-gate wired into `runtime.submit` shadow→enforcing).
- Track A memory spine; DeepSeek/Ollama `usage` population; a dedicated
  `ReasoningAllocationRecord`/`SimulationDecisionRecord` type (currently reuse
  `PraxisEventRecord`).

## Next recommended task

- Merge `feat/dual-kernel-sigma-merge-gate` into `master` (this report is the seal).
  Then Track A (durable memory spine) or Track C C6/C7.
