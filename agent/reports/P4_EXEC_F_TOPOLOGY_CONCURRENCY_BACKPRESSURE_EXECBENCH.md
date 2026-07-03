# P4-EXEC-F — Topology / Concurrency / Backpressure / ExecBench (Lean Validation + Runtime Substrate Boundary)

## 1. Result Header

**DONE — CONTROL_BEFORE_CONCURRENCY / TOPOLOGY_IS_NOT_DISTRIBUTED_RUNTIME / WINDOW_IS_NOT_A_WORKER_POOL / BACKPRESSURE_IS_FEEDBACK_NOT_RECOVERY / EXECBENCH_IS_TELEMETRY_NOT_THEATER / PYTHON_V1_IS_NOT_FINAL_KERNEL / NO_RUST_WASM / P4_EXEC_G_NEXT**

Date: 2026-07-03. Roadmap: Aurel Roadmap v5.5, P4.17–P4.18. Lean validation edition: focused F-pack tests + compileall + ruff on touched paths only; no full pytest, no regression globs, no full-project mypy, no coverage, no bandit — deliberate, per dispatch.

## 2. Pack Scope

P4-EXEC-F adds the local topology/pressure control plane: `ExecutionTopologyProfile` (P4.17 topology), `ConcurrencyWindow` + `ConcurrencyLimitDecision` (local capacity arithmetic and admission verdicts), `ExecutionPressureSnapshot`/`BackpressureSignal`/`BackpressureDecision` (deterministic pressure derivation and safety feedback), and `ExecBenchSample`/`ExecBenchSnapshot`/`HarnessTelemetrySnapshot` (P4.18 honest local telemetry), plus a read-only `TopologyProjection` and the reused/new boundary proofs.

## 3. Canon / Preflight

Branch `master`, clean at start, HEAD `e1fd30e` (P4-EXEC-E hash record). Canon read: ACTIVE_TASK (E complete, F next), ROADMAP, STATE, ARCHITECTURE, DECISIONS, TESTS, REPORTS, C/D/E reports, full aurel_exec source. No canon conflicts. Naming note (F-local vocabulary per the established precedent, recorded in DECISIONS): the A-pack `ExecutionTopologyKind` (structural vocabulary: SINGLE_IN_PROCESS/LINEAR/CASCADE/…) is untouched; F's profile vocabulary ships as `TopologyProfileKind`.

## 4. P4-EXEC-E Prerequisite Confirmation

`agent/reports/P4_EXEC_E_VERIFIER_FAILURE_RECOVERY_ALGEDONIC.md` exists; commits `d39d5ec` + `e1fd30e` in history. The E judgment layer is consumed as pressure input **without any E-module edits**: `build_execution_pressure_snapshot` accepts real `FailureClassification` tuples (failures counted where class ≠ NONE) and real `AlgedonicSignal` tuples (urgency counted), attribute-typed to avoid import churn. The two guards E repaired remain green in this run's touched-path posture (not re-run per lean mandate; F touched neither guard file).

## 5. Runtime Substrate Boundary Proof

- Python AurelExec v1 remains the governance/control plane, reference implementation, contract authority, and projection layer — stated in module doctrine and here.
- **Real worker pool not implemented**: the window is capacity arithmetic (`spawns_workers`/`is_worker_pool` unconstructibly True); no F module imports asyncio/threading/multiprocessing/concurrent/subprocess (source-swept in tests); the C `NoWorkerPoolProof` is re-asserted.
- **Async dispatcher not implemented**: `supports_async_dispatch` unconstructible on the profile; new `NoAsyncDispatcherProof` (dispatcher/thread-pool/task-scheduler all locked False).
- **Remote/distributed runtime not implemented**: non-local `TopologyProfileKind`s are not constructible as active profiles; the C `NoRemoteWorkerProof` (covers remote + distributed availability) is re-asserted — this is the dispatch's NoRemoteDistributedRuntimeProof, satisfied by reuse.
- **Deterministic replay / durable event log / exact copy not implemented**: structurally False on `TopologyProjection`; `exec_replay.py`/`exec_event_log.py` filenames remain guard-forbidden (E guards).
- **Rust/WASM not implemented**: no Cargo.toml/crates/rust/wasm paths (re-tested at repo root); the E `NoRustRewriteProof` re-asserted — this is the dispatch's NoRustWasmSubstrateProof, satisfied by reuse.
- **No Python-final-kernel claim**: `python_final_kernel_claim` structurally False on the projection; the E kernel-claim proof stands.
- **Future-extractable contracts**: primitive int/str/bool/tuple fields, string enums, stable hashes, pure deterministic derivations (`derive_pressure_level` is documented integer arithmetic) — a future substrate can enforce real concurrency against these shapes without redefining governance semantics.

## 6. Operational Debt Guard Proof

Avoided: worker/thread pools, async dispatch, remote/distributed scheduling, queue partitioning, load balancing, P8 routing, event log/replay/copy substrates, Rust/WASM, retry/recovery/rollback execution (backpressure decisions carry `executes_retry`/`executes_recovery`/`executes_rollback`/`grants_authority` unconstructibly True), fake throughput (no throughput/qps vocabulary exists on bench objects at all — tested). Three modules + one projection class, all pure functions over frozen contracts.

Fake throughput avoided structurally: a sample's `duration_ms` without both measurement points is unconstructible; a snapshot inventing counts beyond its provided samples is unconstructible; durations without samples are unconstructible; `is_synthetic_benchmark`/`is_distributed_metric`/`is_production_claim` locked False on samples and snapshots; `NoFakeThroughputProof` fail-closed.

How P4-EXEC-G ambiguity was reduced: Exec-G's projection/CLI/Shell binding gets ready read models (`TopologyProjection`, `HarnessTelemetrySnapshot`) with every unavailable substrate named; the P4 exit seal gets the standing full-suite obligation (now four lean packs old — escalated again) plus a complete set of structurally-False availability booleans to audit.

## 7. Topology Profile Proof

`TopologyProfileKind` closed-world (6 members); only LOCAL_SINGLE_SLOT/LOCAL_BOUNDED_WINDOW constructible as active profiles (REMOTE/DISTRIBUTED/FUTURE_RUST_WASM/ERROR profiles unconstructible — tested per kind). Default from repo truth: LOCAL_SINGLE_SLOT with `max_local_slots=1` and the worker model naming the P4-EXEC-C single-slot canon. LOCAL_SINGLE_SLOT with ≠1 slots unconstructible; zero slots rejected; empty unavailable-reasons rejected; all five `supports_*` capability claims plus `spawns_workers`/`distributes_work` unconstructibly True. Deterministic ids.

## 8. Concurrency Window Proof

`available_slots = max(max_in_flight − current_in_flight, 0)` computed by the builder and **enforced structurally** (a window claiming different arithmetic is unconstructible); negative inputs rejected; over-commitment clamps to zero, never negative; `spawns_workers`/`is_worker_pool` unconstructible; no spawn/acquire/schedule surface (tested).

## 9. Concurrency Limit Decision Proof

Deterministic ladder: ERROR pressure → ERROR(blocked); CRITICAL → BLOCK; no slots → HOLD; HIGH with slots → DELAY(250ms); else ALLOW — with the ALLOW reason stating that allowing admission is not execution (the full A–D guard chain still applies). `allowed`/`held`/`blocked` flags must agree with the kind structurally; `executes`/`spawns_workers` unconstructible; same window ⇒ same decision id.

## 10. Execution Pressure Snapshot Proof

`derive_pressure_level` is pure integer scoring over queue depth, slot occupancy, recent failures, algedonic count, and declared 0–3 resource pressure (LOW/NORMAL/ELEVATED/HIGH/CRITICAL, ERROR on invalid inputs including zero capacity) — every band tested. A snapshot whose `pressure_level` contradicts the derivation is **unconstructible** (E-style table enforcement). Real P4-E objects feed the counts (tested with an actual UNKNOWN_ERROR classification + its algedonic signal driving CRITICAL).

## 11. Backpressure Signal Proof

Emitted only for HIGH/CRITICAL/ERROR; deterministic kind priority (ALGEDONIC_ACTIVE > NO_AVAILABLE_SLOTS > FAILURE_RATE_HIGH > QUEUE_DEPTH_HIGH > RESOURCE_PRESSURE_HIGH > UNSAFE_TO_ADMIT; UNKNOWN_PRESSURE for ERROR); message embeds the authority boundary text; `grants_authority`/`bypasses_custos`/`executes_recovery` unconstructible.

## 12. Backpressure Decision Proof

Deterministic ladder: ERROR → ERROR(fail-closed block); CRITICAL → ESCALATE (block + operator attention — escalation is visibility, not authority); HIGH+no-slots → BLOCK; HIGH+slots → DELAY(300ms); ELEVATED+no-slots → HOLD; else ALLOW. Hold/delay/block flags must agree with the kind structurally; `executes_retry`/`executes_recovery`/`executes_rollback`/`grants_authority` unconstructible; no retry/recover/rollback/authorize surface (tested).

## 13. ExecBench Sample Proof — §6 structural measurement rules; tests cover unmeasured-duration, negative-duration, and theater-claim unconstructibility.

## 14. ExecBench Snapshot Proof — aggregates exactly the provided samples (counts/avg/max/window derived; invented counts and sample-less durations unconstructible; unknown outcomes counted as neither success nor failure); deterministic hashes; DEV_FIXTURE labeling honored for fixture samples.

## 15. Harness Telemetry Snapshot Proof

Binds real topology/window/pressure ids (+ optional backpressure decision and bench snapshot ids); `worker_pool`/`remote`/`distributed`/`async_dispatcher`/`rust_wasm` availability and `executes` unconstructibly True; carries the five named unavailable reasons.

## 16. Projection Proof

`TopologyProjection` (read-only, frozen): topology kind/node/worker-model, window numbers, pressure level, backpressure signal/decision + recommended delay + operator attention, bench snapshot summary, telemetry id, unavailable reasons — and **15 structurally-False availability booleans** (pool, remote, distributed, async dispatcher, load balancer, event log, replay, exact copy, Rust/WASM, python-final-kernel, P5, P9, Shell/React/API). Calm and saturated states project honestly (ALLOW-no-signal vs BLOCK-with-signal, tested); the full chain is deterministic end to end (rebuild-and-compare test).

## 17. No Worker Pool Proof — §5/§8; C proof re-asserted; window/profile claims unconstructible; no spawn primitives in F modules (swept).

## 18. No Remote / Distributed Runtime Proof — §5/§7; C `NoRemoteWorkerProof` re-asserted (covers both booleans); non-local profiles unconstructible.

## 19. No Async Dispatcher Proof — §5; new proof fail-closed; source sweep for asyncio/threading/multiprocessing/concurrent.

## 20. No Fake Throughput Proof — §6/§13–14; new proof fail-closed; no throughput vocabulary exists.

## 21. No Rust/WASM Substrate Proof — §5; E `NoRustRewriteProof` re-asserted; repo-root path check re-run in F tests.

## 22. No P5 Proof Proof — E proof stands; `p5_proof_available` structurally False on the projection; no trace imports in F modules.

## 23. No P9 Authority Proof — E proof stands; `p9_authority_available` structurally False; backpressure/signals grant nothing and bypass nothing (structural).

## 24. Roadmap Coverage Matrix

| Range | Status | Evidence |
|---|---|---|
| P4.17 Topology / Concurrency / Backpressure | DONE | `exec_topology.py` + `exec_pressure.py`; 16 tests |
| P4.18 Harness Telemetry / ExecBench | DONE | `exec_bench.py`; 5 tests |
| Projection | DONE | `exec_projection.py` append; 5 tests |
| Substrate boundary | HELD | §5; structural + path checks |

## 25. P4.17 Status — DONE (§7–§12). Truth labels: LIVE on real local contracts/derivations per dispatch posture; DEV_FIXTURE honored for synthetic inputs.

## 26. P4.18 Status — DONE (§13–§15). Telemetry measured-local-only; all substrate availabilities honestly False.

## 27. Lean Tests / Validation

```
.venv/bin/python -m compileall src/agentic_runtime/aurel_exec tests/aurel_exec → PASS
.venv/bin/python -m pytest tests/aurel_exec/test_exec_topology.py
  tests/aurel_exec/test_exec_concurrency_window.py
  tests/aurel_exec/test_exec_backpressure.py
  tests/aurel_exec/test_exec_bench.py
  tests/aurel_exec/test_exec_topology_projection.py -q → 27 passed
  (topology 5 · concurrency window 6 · backpressure 6 · bench 5 · projection 5)
.venv/bin/python -m ruff check src/agentic_runtime/aurel_exec tests/aurel_exec → All checks passed
git status --short → only in-scope changes; clean after commit
```

Deliberately not run (lean mandate): full pytest, full `tests/aurel_exec`, regression globs, full-project mypy, coverage, bandit. Shared-file changes additive only (`__init__` exports, `exec_projection.py` new class). **Standing full-suite note, now four lean packs old: P4-EXEC-G (the exit-seal pack) must run the full aurel_exec suite** — G is the natural place since sealing P4 without it would be a fake seal.

## 28. Files Created / Modified

Created: `src/agentic_runtime/aurel_exec/{exec_topology,exec_pressure,exec_bench}.py`; `tests/aurel_exec/{test_exec_topology,test_exec_concurrency_window,test_exec_backpressure,test_exec_bench,test_exec_topology_projection}.py`; this report.

Modified: `aurel_exec/{__init__,exec_projection}.py` (additive); `agent/{REPORTS,STATE,ACTIVE_TASK,ROADMAP,ARCHITECTURE,DECISIONS,TESTS}.md`.

Untouched: `exec_queue.py`, `exec_worker.py`, `exec_algedonic.py` (allowed for tiny hooks; none needed), the bridge, all A–E contract modules, all runtime/kernel sources, all web/frontend paths, no Rust/WASM paths.

## 29. What Was Deliberately Not Implemented

Real worker pool; thread pool; async dispatcher; worker/thread/task spawning; remote workers; distributed scheduler; queue partitioning; load balancer; P8 router; durable append-only event log; deterministic replay engine; workflow exact-copy/fork; Rust/WASM substrate; automatic retry; rollback execution; recovery/self-healing engines; failure-history store; P4.19–P4.20 (Shell binding, exit seal); P5 trace verification; P9 enforcement; Shell UI/React/API server.

## 30. Remaining Risks

- Pressure scoring weights are a first calibration (documented integer arithmetic); real telemetry from operation should tune them — deliberately easy to adjust in one function.
- `resource_pressure` is a declared 0–3 input; no actual resource probe exists (honest: declared, not measured).
- Bench ticks are logical; wall-clock duration capture belongs to whoever owns the clock (an open note since B).
- Snapshot inputs (queue depth, in-flight) are caller-supplied from the C shape; a live aggregator that walks actual queue entries belongs to Exec-G's projection work or the future substrate.
- The full aurel_exec suite remains unexecuted since B (guard-drift risk demonstrated in E); G must run it before sealing.

## 31. Next Pack: P4-EXEC-G

Exec Projection / CLI / Shell Binding / P4 Exit Seal — bind the accumulated read models (Exec/Managed/Mode/Judgment/Topology projections + telemetry) to a safe read-only CLI/Shell surface, run the **full aurel_exec suite** as part of the seal evidence, and perform the P4 exit seal honestly over all pack boundaries.

## 32. Optional Future: P4-EXEC-RUST-BRIDGE-DOCTRINE

Runtime Substrate Boundary / Rust-WASM Future Extraction Contract — formalize the extraction surface (these serializable contracts as schema reference and test oracle) when the operator decides substrate work should begin.

## 33. Commit Hash

Recorded post-commit: see `git log` — `feat(aurel-exec): add topology backpressure and execbench telemetry`.

## 34. Final Git Status

Clean after commit (`git status --short` empty); verified in the run that produced this report.
