# SPINE-LIVE — First Living Vertical Thread (P3→P4→P5→P2)

**Status:** PLAN — implementation authority for the SPINE-LIVE milestone series
**Date:** 2026-07-05
**Author:** Principal-architect analysis (operator-requested)
**Supersedes queue position:** proposed ahead of new P5+ contract-only packs (moratorium — see §6)

---

## 0. Reframe — two universes, one wormhole

The repository contains two disconnected universes:

- **Universe A (P0/P1) — LIVE.** `AgenticEntity.plan()` → `ModelRouter.complete()`
  (real Anthropic / OpenAI / Ollama / Mock providers) → `run()` → `_execute_step()`
  → `AgenticRuntime.submit()` → policy / HITL / budget / sandbox / verify / rollback
  / trace / memory. This is a **working agentic loop today.**
- **Universe B (P2–P5) — SEALED / contract-only.** Thousands of governance
  projection classes that *describe* Flow / Exec / Trace / Shell but never touch
  Universe A. The single wormhole between them is
  `ExecRuntimeBridge.submit_once()` (P4-EXEC-B), which calls `submit()` exactly
  once, today only on `read_file`.

**Goal of SPINE-LIVE:** route one real task through Universe B so it lands in
Universe A's real execution. We are **not building execution** — we are
**connecting** what already exists. Estimated ~80% wiring, ~20% new code.

## 0.1 The one invariant (the `LIVE-with-evidence` pattern)

Every phase flips from theater to live using the pattern P4-EXEC-B already
models — an availability boolean is `True` **only** when a real evidence ref
exists:

```python
# NOT: x_available = False                # eternal theater
# NOR: x_available = True                 # dishonest claim
# BUT: x_available = bool(evidence_ref)   # LIVE only with proof
```

This preserves fail-closed honesty (no evidence → honest `UNAVAILABLE`) while
letting real execution flip the bit to LIVE. It never grants
`authority_granted` / `permission_granted` — those remain P9's, always `False`.

## 1. Target thread (concrete)

Reuse the existing `demo-harness buggy_calculator` controlled repo:

```
Operator: "fix buggy_calculator"                         (via P2 Shell)
  → Entity drafts plan with a REAL model                 (mock in CI, live behind AUREL_LIVE=1)
    → P3 Flow: 2-node graph [patch → test], scheduler dispatches
      → P4 Exec: submit_once() for write_file, then run_tests, under one lease
        → P0 kernel: executes in a hard-isolated (Bubblewrap) sandbox, rolls back on failure
          → P5 Trace: persisted hash chain, replayable, TRACE_VERIFIED from recomputation
            → P2 Shell: operator sees the live run, not a read-model
```

## 2. Guardrails that are NOT touched

- "Entity proposes, Runtime disposes." Flow / Exec only *route* toward
  `runtime.submit`; they never execute themselves.
- All `authority_granted` / `permission_granted` stay `False`. Only
  `execution_available` / `runtime_submit_wired` / `trace_verified` become
  evidence-gated.
- No protected test is weakened (`TestIntegrityVerifier`).
- Any tool that writes runs under a hard-isolated sandbox
  (`is_hard_isolated=True`); `UnsafeLocalSandbox` is never the write path.

## 3. Milestones (commit order)

| # | Pack | Goal | Effort |
|---|------|------|--------|
| **S0** | SPINE-LIVE-0 | Live model evidence primitive (`LIVE-with-evidence`) | S |
| **S1** | SPINE-LIVE-1 | P4 bridge: `read_file` → `write_file` + `run_tests` under lease | M |
| **S2** | SPINE-LIVE-2 | P3 Flow dispatch loop (2-node graph) | M |
| **S3** | SPINE-LIVE-3 | P5 Trace persistent + replay verifier | M |
| **S4** | SPINE-LIVE-4 | P2 Shell live run view | M |
| **S5** | SPINE-LIVE-5 | End-to-end spine harness + honest seal | S |

Critical path: **S0 → S1 → S2**. S3 and S4 may proceed in parallel after S2.
S5 last.

---

### S0 — Live model evidence primitive

- **Goal:** introduce the reusable `LIVE-with-evidence` primitive that S1–S5
  depend on. The live model already works via `ModelRouter`; what is missing is
  a first-class **evidence ref** proving a real model call happened.
- **Files:** new `src/agentic_runtime/spine/` package
  (`live_evidence.py`, `__init__.py`); additive `ModelRouter.complete_with_evidence`.
- **Sealed→Live flip:** `model_call_available = bool(response_hash) and not refusal`.
- **Evidence invariant:** `ModelCallEvidenceRef` (profile, model, prompt_hash,
  response_hash, char counts, label) — `available` is `True` only for a real,
  non-refusal response.
- **Tests:** `tests/spine/test_live_evidence.py` — mock gives a deterministic
  plan with `available=True`; refusal gives `available=False`; determinism of
  content hash; the invariant cannot be bypassed.
- **Deliberately not done:** entity-loop rewiring (deferred to S2, where flow
  dispatch needs it); no live provider call in CI.

### S1 — P4 bridge: extend to write + test

- **Goal:** turn the key a second and third time — `write_file` and `run_tests`
  under one lease.
- **Files:** `aurel_exec/exec_mode_profiles.py` (`SUPPORTED_BRIDGE_TOOLS`,
  `ToolExecutionProfile.allowed_tool_names`, `CodeExecutionProfile`),
  `exec_runtime_bridge.py` (`submit_once`, `RuntimeBridgeSubmitRequest`),
  `exec_lease.py`.
- **Sealed→Live flip:** `CodeExecutionProfile` moves from `UNAVAILABLE` to
  available **only** for `{write_file, run_tests}` and **only** with a
  hard-isolated sandbox. Lease scope binds tool + args-hash.
- **Evidence invariant:** multi-step session, one lease, two submits, each with
  its own `runtime_submit_ref`.
- **Tests:** `test_exec_bridge_write_test_live.py` — write without hard
  isolation is fail-closed blocked; successful patch passes; failing test →
  rollback.

### S2 — P3 Flow dispatch loop

- **Goal:** the scheduler actually dispatches instead of only computing a ready
  queue.
- **Files:** `aurel_flow/scheduler.py` (`calculate_ready_queue`,
  `make_scheduler_decision`), new `flow_dispatch.py`, `workflow_graph.py`,
  `flow_checkpoint.py`, `pause_resume.py`.
- **Sealed→Live flip:** a thin `FlowDispatcher` that, per `SchedulableNode`,
  calls `ExecRuntimeBridge.submit_once()` (S1), writes a checkpoint before/after,
  and honors pause/resume. The dispatcher **executes nothing** — it forwards to
  the bridge.
- **Evidence invariant:** `node_dispatched = bool(exec_attempt_ref)`; the run
  advances only with a real outcome ref.
- **Tests:** `test_flow_dispatch_live.py` — 2-node graph advances; node-1 failure
  halts node-2; pause on node-1 really pauses; resume continues from checkpoint.

### S3 — P5 Trace persistent + replay

- **Goal:** the trace survives the process and replays; `TRACE_VERIFIED` becomes
  constructible from real evidence.
- **Files:** `trace.py` (`PersistentTraceLedger` already exists — activate it;
  `InMemoryTraceLedger` stays for tests), `aurel_flow/flow_replay.py`, new
  `trace_verify.py`.
- **Sealed→Live flip:** the runtime uses `PersistentTraceLedger` (jsonl on disk)
  for the spine run. A new verifier **recomputes the hash chain** from disk and
  compares to the head — that is the real `TRACE_VERIFIED`.
- **Evidence invariant:** `trace_verified = recomputed_head_hash ==
  persisted_head_hash` (the only place in the repo where `trace_verified=True`
  may originate).
- **Tests:** `test_trace_persist_replay.py` — write a run, read from disk,
  recompute (PASS), corrupt one record → tamper detected (FAIL), replay
  reproduces the same transition sequence.

### S4 — P2 Shell live run view

- **Goal:** the operator sees the real run, not a read-model.
- **Files:** `aurel_shell/terminal_shell_client.py`,
  `cli_modules/shell_commands.py`, new `shell_run_view.py`, CLI `shell`
  subcommand.
- **Sealed→Live flip:** a new read-only `shell run-view <run_id>` that reads the
  persisted P5 trace (S3) and shows live transitions / checkpoints / outcome.
  This is the real "binding" from the Integration-First law (previously always
  `UNAVAILABLE`).
- **Evidence invariant:** `shell_binding_live = bool(persisted_trace_ref)`; no
  trace → honest `UNAVAILABLE`.
- **Tests:** `test_shell_run_view_live.py` — after a spine run, `run-view` shows
  2 nodes, 2 submits, a verified trace; without a run → `UNAVAILABLE`.

### S5 — End-to-end spine harness + seal

- **Goal:** one test drives the whole thread; an honest seal.
- **Files:** `demo_harness.py`, new scenario `spine_buggy_calculator`, CLI
  `demo-harness --spine`.
- **Sealed→Live flip:** `demo-harness spine_buggy_calculator` drives
  Entity(mock) → Flow → Exec → Trace → Shell and returns JSON with
  `execution_available=True`, `trace_verified=True`, `shell_binding_live=True`,
  each backed by a ref.
- **Tests:** `test_spine_live_e2e.py` — full thread green with the mock model in
  CI; live variant behind `AUREL_LIVE=1`.

## 4. Definition of Done ("live like P0")

In a single process, with the **mock model in CI**:

1. Entity drafts a plan (model-call evidence ref).
2. Flow dispatches 2 nodes through the bridge (exec-attempt ref per node).
3. Exec runs write + test in a hard-isolated sandbox; rolls back on failure.
4. Trace is persisted and **recomputation-verified** (`trace_verified=True` from proof).
5. Shell `run-view` shows the real thread.
6. No `authority/permission_granted` is `True`; no protected test weakened.

## 5. Sequencing, effort, risk

- Critical path S0 → S1 → S2. S3/S4 parallel after S2. S5 last.
- Effort: ~2–3 weeks focused (mostly wiring existing modules).
- Top risk: S1 sandbox gate — writes through Bubblewrap must be truly isolated;
  a security review is scheduled before anything writes to disk.

## 6. Moratorium

Freeze all new contract-only P5+ packs until S5 is green. When the spine
breathes, we have *proof* the architecture works — and only then does P5/P6
breadth earn its place.
