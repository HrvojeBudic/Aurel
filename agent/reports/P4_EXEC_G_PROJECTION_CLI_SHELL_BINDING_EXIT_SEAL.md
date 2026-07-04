# P4-EXEC-G — Exec Projection / CLI / Shell Binding / P4 Exit Seal (Full Pre-Seal Validation)

## 1. Purpose / Result Header

**SEAL VERDICT: SEALED**

P4-EXEC-G makes AurelExec operator-visible (one status read model over the whole P4-A…F stack), read-only bindable (a closed-world CLI/Shell binding contract), truth-audited, unavailable-audited, coverage-mapped over P4.0–P4.20, handoff-assigned to P5/P8/P9/P2/Rust-WASM, and evidence-sealed — with the seal verdict derived structurally from the large pre-seal validation gate, never declared. Date: 2026-07-04. Roadmap: Aurel Roadmap v5.5, P4.19–P4.20.

## 2. Roadmap Coverage P4.19–P4.20

| Range | Status | Evidence |
|---|---|---|
| P4.19 Exec Projection / CLI / Shell Binding | DONE | `exec_status.py`; 3 test files (16 tests) |
| P4.20 P4 Exit Seal / P5-P8-P9 Handoff | DONE — verdict SEALED | `exec_seal.py`; 2 test files (10 tests); this report + release evidence |

## 3. Preflight / P4-EXEC-F Prerequisite

Branch `master`, clean at start, HEAD `38e6514` (P4-EXEC-F hash record). All six prior P4 reports present (`P4_EXEC_A…F`). Canon read: ACTIVE_TASK (F complete, G next, full-suite obligation named), ROADMAP, STATE, ARCHITECTURE, DECISIONS, TESTS, REPORTS. No canon conflicts.

## 4. Runtime Substrate Boundary Proof

Python AurelExec v1 remains the governance/control plane, reference implementation, contract authority, and projection/evidence layer. This pack added read models and seal contracts only. Rust/WASM substrate: not implemented (no Cargo.toml/crates/rust/wasm paths — re-verified by the standing F test in the full suite). Deterministic replay / durable event log / exact copy: unavailable (structural on `TopologyProjection`; filename guards). Real worker pool / async dispatcher: unavailable (C/F structural guards). No Python-final-kernel claim: `P4ExitSeal.python_final_kernel_claim` is unconstructibly True. Projection/status/seal contracts use primitive serializable fields and stable hashes — future-extractable.

## 5. Projection Aggregator / ExecStatusReadModel Proof

`build_exec_status_read_model` (the ExecProjectionAggregator) is a pure function over optional P4-A…F objects producing an `ExecStatusReadModel` with **26 canonical state categories** (admission/lease/job/attempt/session, queue/worker/checkpoint/rollback/messages, mode + four profile states, submit/outcome/trace-binding, verification/failure/recovery/algedonic, topology/pressure/backpressure/telemetry). Structural guarantees: category totality in canonical order (truncated/extended models unconstructible); every UNAVAILABLE category must carry a reason; a category valued TRACE_VERIFIED is unconstructible; `mutates_runtime`/`executes`/`verifies_trace`/`enforces_policy`/`grants_authority`/`shell_ui_available` unconstructibly True; `read_only` locked. Behavioral proof: the aggregator over a real bridge execution shows ADMIT/SUCCEEDED/SUBMITTED_ONCE/RUNTIME_SUCCESS/TRACE_BOUND honestly; the fake kernel records zero additional calls during aggregation; empty aggregation is honestly all-UNAVAILABLE with the UNAVAILABLE truth label, never fake LIVE.

## 6. CLI / Shell Binding Proof

`ShellBindingContract`: closed-world read-only command vocabulary (STATUS/COVERAGE/HANDOFF/SEAL — no SUBMIT/RUN/RETRY/RECOVER/ROLLBACK/APPROVE/MUTATE/VERIFY/ENFORCE member; advertising an out-of-vocabulary command is unconstructible). `handle_exec_cli_status` renders deterministic JSON and mutates nothing (structural + tested). **Live CLI wiring: UNAVAILABLE with reason** — the binding contract is implemented and tested, but registration into the `agentic_runtime` CLI was deliberately not performed in the seal pack (follows the proven flow-CLI pattern as a follow-up or lands with P2 Shell binding); verified by test that `agentic_runtime/cli.py` contains no aurel_exec reference. **Shell UI: UNAVAILABLE** (P2 owns it; structural on contract and status model).

## 7. Truth Label Audit

`TruthLabelAudit` censuses real labels; any TRACE_VERIFIED appearance (only possible as corrupted raw string data — the enum has no such member) forces `audit_status=ERROR`, and an audit hiding TRACE_VERIFIED items behind PASS is unconstructible. Audit over the real bridge-execution labels: PASS with LIVE/DEV_FIXTURE/TRACE_BOUND counted honestly and zero trace-verified items. An ERROR truth audit structurally blocks the seal (tested).

## 8. Unavailable State Audit

`UnavailableStateAudit` is total over the eight required absent systems with owners enforced structurally (wrong owner or truncated audit unconstructible): Shell UI → P2 AurelShell; P5 trace verification → P5 AurelTrace; P8 routing → P8 Atlas/coordination; P9 enforcement → P9 Custos; Rust/WASM substrate → future extraction (operator-decided); worker pool → future Rust/WASM substrate / runtime hardening; deterministic replay → future substrate / P5+; durable event log → P5 / future substrate.

## 9. P4 Capability Coverage Matrix

`ExecCapabilityCoverageMatrix` is total over P4.0–P4.20 (21 rows; missing/reordered rows unconstructible; every row carries evidence). Repo-truth statuses: **LIVE** for P4.0–P4.11, P4.15–P4.20 (eighteen rows — real, tested, committed contracts and the proven read-only bridge path); **PROFILE_ONLY** for P4.12 (model execution profile; calls structurally unavailable) and P4.14 (verifier hook; no AVAILABLE member — evidence-producing verifier is future canon); **UNAVAILABLE** for P4.13 (terminal/code execution; every execution boolean unconstructible until sandbox/verifier/P9 canon exists).

## 10. P5/P8/P9/P2/Rust-WASM Handoff Matrix

`P4HandoffMatrix` (owner totality structural; `handoff_is_implementation` unconstructibly True): P5 AurelTrace owns trace verification, the durable evidence spine, trace event canonicalization, replay/evidence binding, and TRACE_VERIFIED truth. P8 Atlas/coordination owns routing, model-worker coordination, and topology-aware routing. P9 Custos owns authority/enforcement, high-risk recovery approval, policy runtime hardening, and backpressure override authority. P2 AurelShell owns operator UI projection, Shell command surfaces, and non-mock dashboards. The future Rust/WASM substrate owns the deterministic event log, replay, durable worker leases, real worker pools, high-throughput execution, WASM/sandbox boundary, and exact-copy/fork substrate.

## 11. P4 Exit Seal Proof

`P4ExitSeal`: SEALED is **unconstructible** unless both the focused and large `ValidationSummary` objects pass — and a summary claiming pass over failing required gates is itself unconstructible (verdicts derived, never declared; tested including the fake-seal promotion attempt). The builder additionally blocks the seal on a truth-audit ERROR. `future_features_implemented`/`python_final_kernel_claim`/`trace_verified`/`seal_is_runtime_mutation` unconstructibly True. Covered packs: A–G. Next domain: P5 AurelTrace Spine.

## 12. Focused Validation (Phase 10)

```
compileall src/agentic_runtime/aurel_exec tests/aurel_exec → PASS
pytest (5 focused G files) → 26 passed
ruff (touched paths) → All checks passed (after removing one unused test variable)
```

## 13. Large Pre-Seal Validation Gate (Phase 11)

| Gate | Command | Result | Notes |
|---|---|---|---|
| Focused compileall | `.venv/bin/python -m compileall src/agentic_runtime/aurel_exec tests/aurel_exec` | PASS | clean |
| Focused G tests | `.venv/bin/python -m pytest <5 G files> -q` | PASS | 26 passed |
| Focused ruff | `.venv/bin/python -m ruff check src/agentic_runtime/aurel_exec tests/aurel_exec` | PASS | all checks passed |
| Full P4 tests | `.venv/bin/python -m pytest tests/aurel_exec -q` | PASS | **285 passed** — first full A–G run since B; the E guard repairs held |
| Runtime/tool/sandbox/trace | `.venv/bin/python -m pytest tests/test_runtime*.py tests/test_tool*.py tests/test_sandbox*.py tests/test_trace*.py -q` | PASS | 421 passed |
| Full pytest | `.venv/bin/python -m pytest -q` | PASS | **8068 passed, 2 skipped** in 23:15 (skips are the standing subprocess-conditional tests) |
| Full ruff | `.venv/bin/python -m ruff check src tests` | PASS | all checks passed |
| Mypy | `.venv/bin/python -m mypy src/agentic_runtime` | PASS | Success: no issues in 436 source files |
| Coverage | `.venv/bin/python -m pytest tests/ --cov=src/agentic_runtime --cov-report=term --cov-fail-under=75 -q` | PASS | 89.21% total coverage, threshold 75; 8068 passed, 2 skipped in 39:25 |
| Security (bandit) | `.venv/bin/python -m bandit -r src/agentic_runtime -ll` | PASS | 0 medium, 0 high severity (canonical TESTS.md flags) |
| Security (pip-audit) | — | NOT_REQUIRED | not in the TESTS.md seal set; requires network |
| Final git status | `git status --short` | CLEAN | only in-scope changes; clean after commit |

## 14. No-Mutation / No-Claim Proofs

No runtime mutation from projection or CLI (structural booleans + behavioral fake-kernel call-count test + rendering determinism). No TRACE_VERIFIED (no enum member; status-category and audit guards). No P5 proof (E proof re-asserted; audit owner P5). No P8 routing (nothing routes; owner assigned in handoff). No P9 authority (E proof re-asserted; owner assigned). No Rust/WASM substrate (F path checks in the full suite). ExecRuntimeBridge untouched — still the single kernel reference (sweep in full suite).

## 15. Files Created / Modified

Created: `src/agentic_runtime/aurel_exec/{exec_status,exec_seal}.py`; `tests/aurel_exec/{test_exec_status_projection,test_exec_projection_truth_labels,test_exec_cli_status_binding,test_exec_p4_handoff_matrix,test_exec_p4_exit_seal}.py`; this report; `agent/releases/P4_AURELEXEC_EXIT_SEAL.md`.

Modified: `aurel_exec/__init__.py` (exports); `agent/{REPORTS,STATE,ACTIVE_TASK,ROADMAP,ARCHITECTURE,DECISIONS,TESTS}.md`.

Untouched: `exec_projection.py` (this pack added no class there — status lives in exec_status.py), `cli.py`, the bridge, all A–F contract modules, all runtime/kernel sources, all web/frontend paths, no Rust/WASM paths.

## 16. Remaining Risks

- The verifier hook (P4.14) remains PROFILE_ONLY: PASSED verification requires caller-supplied evidence until a real evidence-producing verifier pack exists — the honest steady states stay INCONCLUSIVE/UNAVAILABLE.
- CLI wiring is a deliberate follow-up: the binding contract is tested but no `exec status` command is registered; P2 Shell binding or a small surface pack should wire it.
- Wall-clock ownership (standing note since B) and live queue aggregation (F note) pass to the P5-era/substrate work.
- The lean-pack guard-drift lesson stands: this seal ran everything; future domains should schedule full-suite gates explicitly rather than accumulating obligations.
- Coverage/threshold and security posture are point-in-time; the operator seal commands in TESTS.md remain the recurring standard.

## 17. Next Domain

**P5 — AurelTrace Spine** (if SEALED). The handoff matrix and release evidence define what P5/P8/P9/P2 and the future substrate own. Optional architecture task: P4-EXEC-RUST-BRIDGE-DOCTRINE.

## 18. Commit Hash / Final Git Status

`045b2a4` — `feat(aurel-exec): add projection status and p4 exit seal` (17 files, +1904/−6). Final `git status --short` clean.
