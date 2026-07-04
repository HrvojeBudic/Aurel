# P4 AurelExec Exit Seal — Release Evidence

**Seal verdict: SEALED**
**Sealed domain:** P4 AurelExec execution kernel foundation
**Date:** 2026-07-04
**Next domain:** P5 — AurelTrace Spine

## P4 Scope Summary

P4 built the governed execution kernel foundation in seven packs. AurelExec can admit a P3 candidate through a deterministic eight-gate chain, issue a scoped/expiring/revocable execution lease, bind a job to a session, and submit **once** through the existing `AgenticRuntime.submit()` kernel on the safe read-only `read_file` path — then wrap that single proven submit in managed local runtime shape (queue entry, one in-process worker slot, deterministic claims, local causality log, checkpoint/rollback refs), a closed-world execution mode safety layer, a post-execution judgment layer (verification/failure/recovery/algedonic), a local pressure control plane (topology/concurrency/backpressure/ExecBench), and finally an operator-visible status read model, audits, handoff matrix, and this evidence-derived exit seal. Python AurelExec v1 is the governance/control/reference layer — explicitly not the final high-throughput deterministic durable execution substrate.

## Covered Packs

| Pack | Delivered | Commit |
|---|---|---|
| P4-EXEC-A | Doctrine, contracts, deterministic admission, execution lease foundation | c99c604 |
| P4-EXEC-B | First governed runtime submit bridge (real kernel, read-only path, trace-bound) | 57f39e2 |
| P4-EXEC-C | Managed runtime shape: queue, single worker slot, claims, local log, checkpoint/rollback refs | a6dc80b |
| P4-EXEC-D | Closed-world execution mode registry + tool/model/terminal/code profiles | 7229c6e |
| P4-EXEC-E | Verification, failure taxonomy, bounded recovery plans, algedonic signals; substrate boundary doctrine | d39d5ec |
| P4-EXEC-F | Topology, concurrency windows, pressure/backpressure, ExecBench telemetry | 70b9433 |
| P4-EXEC-G | Status read model, CLI/Shell binding contract, audits, handoff matrix, exit seal | 045b2a4 |

## Capability Coverage (P4.0–P4.20)

LIVE: P4.0 doctrine, P4.1 contract types, P4.2 admission bridge, P4.3 lease, P4.4 job/attempt lifecycle, P4.5 session, P4.6 runtime submit bridge, P4.7 worker slot/queue claim, P4.8 local message kernel, P4.9 checkpoint/rollback refs, P4.10 mode registry, P4.11 tool profile (read-only bridge path), P4.15 failure/recovery (plans only), P4.16 algedonic signals, P4.17 topology/backpressure, P4.18 ExecBench telemetry, P4.19 projection/binding, P4.20 exit seal.

PROFILE_ONLY: P4.12 model execution profile (model calls structurally unavailable), P4.14 verifier hook (no AVAILABLE member; evidence-producing verifier is future canon).

UNAVAILABLE: P4.13 terminal/code execution profiles (every execution boolean unconstructible; sandbox/verifier/P9 canon required first).

## Truth-Label Audit Summary

TRACE_VERIFIED: zero occurrences and structurally impossible (`ExecTruthLabel` has no such member; a status category or audit carrying it fails ERROR and blocks the seal). LIVE is used only for real tested local logic and the actual kernel-call results; TRACE_BOUND only for real captured `StateTransitionRecord` refs; DEV_FIXTURE for fixtures; UNAVAILABLE everywhere honesty requires it.

## Unavailable-State Summary (with owners)

Shell UI → P2 AurelShell · P5 trace verification → P5 AurelTrace · P8 routing → P8 Atlas/coordination · P9 enforcement → P9 Custos · Rust/WASM substrate → future extraction (operator-decided) · worker pool → future substrate/runtime hardening · deterministic replay → future substrate/P5+ · durable event log → P5/future substrate.

## Handoff Matrix

- **P5 AurelTrace:** trace verification, durable evidence spine, trace event canonicalization, replay/evidence binding, TRACE_VERIFIED truth.
- **P8 Atlas/coordination:** routing, model-worker coordination, topology-aware routing, later distributed coordination.
- **P9 Custos:** authority/enforcement, high-risk recovery approval, policy runtime hardening, backpressure override authority.
- **P2 AurelShell:** operator UI projection, Shell command surfaces, frontend visibility, non-mock AurelExec dashboards.
- **Future Rust/WASM substrate:** deterministic event log, deterministic replay, durable worker leases, real worker pool, high-throughput execution, WASM/sandbox boundary, exact-copy/fork substrate.

## Validation Summary

Focused G gate: compileall PASS · 26 focused tests PASS · ruff PASS.

Large pre-seal gate: full `tests/aurel_exec` **285 passed** (first complete A–G run since P4-EXEC-B) · runtime/tool/sandbox/trace subset **421 passed** · full repo pytest **8068 passed, 2 skipped** (standing subprocess-conditional skips) · full ruff PASS · mypy PASS (436 files) · coverage PASS (89.21% total coverage, threshold 75; 8068 passed, 2 skipped in 39:25) · bandit PASS (0 medium/high at canonical `-ll`) · pip-audit NOT_REQUIRED (not in the TESTS.md seal set) · final git status CLEAN.

## Remaining Risks

Verifier hook is profile-only until real evidence canon exists; CLI wiring is a tested-but-unregistered follow-up; wall-clock ownership and live queue aggregation pass to P5-era/substrate work; the seal is point-in-time — TESTS.md operator-seal commands remain the recurring standard.

## Seal Statement

This seal is evidence, not vibes: the `P4ExitSeal` contract makes a SEALED verdict unconstructible over failing or missing validation gates. Sealing P4 means the execution kernel foundation is bounded, visible, report-backed, validated, and handoff-ready — not that future execution features exist. Runtime submit success is not semantic success; trace-bound is not trace-verified; projection is not control; Python v1 is not the final durable kernel.

P3 proposes. P4 admits, leases, submits once, manages, judges, and pressures. P5 proves. P8 routes. P9 authorizes. Shell projects. Operator decides.
