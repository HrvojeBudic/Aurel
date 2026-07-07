# Track A / A8 — Live promotion wiring + durable fail-closed (Track A complete)

**Date:** 2026-07-07
**Branch:** `feat/track-a-memory` (unmerged, not pushed)
**Status:** DONE. The **final Track A phase**; first to wire into `build_runtime`/
`runtime`. Additive and flag-gated — default (flag OFF) behavior is byte-identical.

## Summary

A8 lands the two wirings that make the memory stack *live*:

- **A8a — durable factory + fail-closed fallback.** `build_runtime` now builds a
  `DurableMemoryFabric` (A3) when `AUREL_DURABLE_MEMORY` is ON, and **fails closed**
  to the in-RAM `MemoryFabric` when the durable backend is unavailable — never a
  silent claim of durability. Flag OFF ⇒ the exact pre-A8 in-RAM fabric.
- **A8b — live promotion driver.** `runtime._record_command_memory` feeds each
  *verified* command outcome to a governed promotion bridge that submits a
  procedure CANDIDATE and drives it up the P0.9 ladder on repeated success — all
  through the existing `request_write`/`promote` funnel, flag-gated so the flag-OFF
  path is byte-identical.

## Files changed

**Edit — `src/agentic_runtime/__init__.py` (A8a)**
- New `memory_backend` kwarg on `build_runtime` (additive, default `None`) and a
  `_build_memory_fabric(trace, trace_dir, memory_backend)` helper: flag OFF ⇒
  `MemoryFabric()`; flag ON ⇒ `DurableMemoryFabric` over a `FileMemoryBackend`
  (default path `<trace_dir>/memory/<run_id>.jsonl`, or the injected backend),
  **fail-closed to `MemoryFabric()`** if the backend is unavailable or anything
  raises. The fabric-construction line now calls the helper.

**Edit — `src/agentic_runtime/runtime.py` (A8b)**
- Snapshot `self._durable_memory_enabled = _flag_enabled()` once in
  `AgenticRuntime.__init__` (read via `memory_bitemporal._flag_enabled`); lazy
  `self._memory_promotion_bridge`.
- At the end of `_record_command_memory`, **when the flag is ON**, call
  `_observe_promotion(cmd, vres, rec)` (wrapped so promotion can never raise into
  the command path). Flag OFF ⇒ the branch is skipped and the method is
  byte-identical to today.

**New — `src/agentic_runtime/evaluation/memory_promotion_bridge.py` (A8b)**
- `MemoryCandidateBridge.observe(...)` — per command signature: on the first
  verified success, submit a governed CANDIDATE (one `charge_memory_write`, one
  `request_write`); accumulate distinct successful trace ids; drive
  `candidate → verified` (evidence) then `verified → procedural` (≥2 distinct
  successes) via `fabric.promote`. A failed run does nothing. `command_signature`
  = `tool | sha(canonical_json(args))[:16]` (deterministic).

## A8a — fail-closed-durability proof

Seal §2 (`test_durable_unavailable_fails_closed_in_ram`): with the flag ON and an
`ExternalMemoryBackend` (`available is False`), `build_runtime` still returns a
Kernel whose `memory` is a plain `MemoryFabric` (not `DurableMemoryFabric`,
`durable_enabled` False) and which still writes in RAM. No fabricated durability.
Seal §1: flag ON + a working `FileMemoryBackend` ⇒ `DurableMemoryFabric`,
`durable_enabled True`.

## Flag-OFF byte-identity

Seal §3: flag OFF ⇒ `type(kernel.memory) is MemoryFabric` (exactly the pre-A8
fabric), `runtime._durable_memory_enabled is False`, and the promotion bridge is
**never constructed**. `_build_memory_fabric`'s flag-OFF branch returns
`MemoryFabric().bind_trace(trace)` — identical to the code it replaced — and
`_record_command_memory`'s new branch is skipped. The shared-runtime regression
(state_machine_p07, budget_p08, hitl_p15 — all `build_runtime` users) passes
unchanged.

## A8b — governance-routed promotion + monotonicity proof

Seal §4/§5 (`test_a8b_promotion_monotonicity_and_governance`):
- **Routed through governance, no bypass:** one `charge_memory_write` for the
  candidate (`budget.memory_writes == 1`), one `action="write"` governance row for
  the candidate id, and two `action="promote"` rows (verified, procedural) — every
  op is a governed funnel call.
- **Monotonicity:** 1 verified success ⇒ `candidate → verified` (evidence);
  a 2nd *distinct* successful trace ⇒ `verified → procedural`.
- **Failed run ⇒ no promotion:** a `run_succeeded=False` observe returns
  `failed_run_no_promotion` and leaves the state at `procedural` (P0.9 — failed
  runs can't mint success memory).
- **Runtime-authored, not agent:** the candidate's `created_by == "runtime"`; the
  bridge is driven only by the runtime, so an agent cannot self-elevate through it
  (and agent `mem_*` tools remain governed as in A1a–A4).

Seal §6: the driver is flag-gated on the runtime (`_durable_memory_enabled` True
under the flag, False without).

## Spec-vs-code drift + decisions

- **D1 (main) — the spec's `evaluation/memory_candidate_bridge.py` file already
  exists.** It is the P1.5.18 evaluation→candidate *contract-derivation* bridge (a
  different concern, with its own tests). Overwriting it would clobber shipped
  functionality. Smallest correct honest path: the A8b driver lives in a new,
  clearly-named `evaluation/memory_promotion_bridge.py` beside it. Noted here.
- **D2 — durable backend injectable via `memory_backend`.** Rather than making the
  default `FileMemoryBackend` fail (it is always `available`), the fail-closed path
  is exercised by injecting an unavailable backend. This keeps the default
  production path real and makes the seam testable/deterministic.
- **D3 — promotions don't charge a `memory_write`.** Only the CANDIDATE write
  charges (matching the existing `fabric.promote`, which never charged); promotions
  are governed state transitions (one row each), not budgeted writes. "One charge
  per write" holds for the write; promotions are traced but free — consistent with
  the pre-existing promote semantics.
- **D4 — bridge gated on `AUREL_DURABLE_MEMORY`, no new flag.** The task allows no
  flag beyond the Track-A umbrella; A8b rides it. Flag OFF ⇒ byte-identical.
- **D5 — promotion is advisory / never blocks a command.** `_observe_promotion` is
  wrapped in a `try/except pass`: a promotion hiccup can never fail a command that
  already succeeded and verified.

## Validation (focused-first)

- `compileall` OK; `ruff` clean; `python -m mypy` — no issues, on the 3 source files.
- Seal `test_p6a8_live_promotion.py` — **5 passed**.
- Directly-affected regression (timeout-wrapped): memory_p09, **state_machine_p07,
  budget_p08, hitl_p15** (build_runtime users), praxis_p16, tool_contract_p10,
  tool_registry_p133, builtin_tool_manifests_p138, trace_persistence_p06,
  p6a0–p6a8 → **219 passed, 0 failed**.
- **Full suite (Track A pre-merge seal):** `AGENTIC_SKIP_RECURSIVE_SMOKE=1
  .venv/bin/python -m pytest -q -p no:cacheprovider` → **8594 passed, 11 skipped,
  0 failed in 33:58 (2038.67s)** — baseline 8545/11, so +49 new Track A seal tests
  with **zero regressions**.

## Track A — feature-complete

A0 bi-temporal stamps → A1a memory-as-tools → A2 typed graph → A3 durable
projection → A4 belief revision → A5 consolidation → A6 hybrid retrieval → A7
memory explorer (+ D2 replay seam closed) → **A8 live promotion**. All additive,
governed, and flag-gated (`AUREL_DURABLE_MEMORY`, byte-identical when OFF). Track A
is now feature-complete on `feat/track-a-memory`, pending merge to `master`.

**Recommended next step:** merge Track A to `master` (the branch is a clean,
flag-gated, additive stack with every phase sealed and a green full suite), then
proceed to **Track C** remainder (simulation-gated action: C6 shadow-wire into
`runtime.submit` → C7 → C8 → C9) per the master-plan sequencing.
