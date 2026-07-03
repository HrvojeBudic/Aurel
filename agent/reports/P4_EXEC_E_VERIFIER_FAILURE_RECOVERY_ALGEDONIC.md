# P4-EXEC-E — Verifier / Failure Classification / Bounded Recovery / Algedonic Signals (Lean Validation + Runtime Substrate Boundary)

## 1. Result Header

**DONE — RUNTIME_SUCCESS_IS_NOT_SEMANTIC_SUCCESS / VERIFIED_REQUIRES_EVIDENCE / DETERMINISTIC_FAILURE_TAXONOMY / PLAN_IS_NOT_RECOVERY_EXECUTION / NO_AUTOMATIC_RETRY / ALGEDONIC_IS_VISIBILITY_NOT_AUTHORITY / PYTHON_V1_IS_NOT_FINAL_KERNEL / NO_RUST_WASM / STALE_GUARDS_REPAIRED / P4_EXEC_F_NEXT**

Date: 2026-07-03. Roadmap: Aurel Roadmap v5.5, P4.14–P4.16. Lean validation edition: focused E-pack tests + compileall + ruff on touched paths (+ the two repaired boundary guards re-run); no full pytest, no regression globs, no full-project mypy, no coverage, no bandit — deliberate, per dispatch.

## 2. Pack Scope

P4-EXEC-E adds the post-execution judgment layer: `ExecutionVerificationRequest`/`ExecutionVerificationDecision`/`VerifierHook` (P4.14), deterministic `FailureClassification` over a total taxonomy table + `BoundedRecoveryPlan` (P4.15), `AlgedonicSignal` urgent visibility (P4.16), a read-only `JudgmentProjection`, eight boundary proofs, and the Runtime Substrate Boundary doctrine (§5).

## 3. Canon / Preflight

Branch `master`, HEAD `3fc801f` (P4-EXEC-D hash record) — but **not** a fully green tree: two boundary tests already failed on committed master (§below). Canon read: ACTIVE_TASK (P4-EXEC-D complete, E next), ROADMAP, STATE, ARCHITECTURE, DECISIONS, TESTS, REPORTS, the B/C/D reports, full aurel_exec source. No canon conflicts beyond the stale-guard finding.

**Stale-guard finding and repair (pre-existing repo inconsistency, verified by running the tests):** `test_exec_unsupported_modes_boundary.py::test_no_p5_p9_shell_ui_surface_exists` (B-era) failed on master because P4-EXEC-C legitimately created `exec_worker/queue/checkpoint.py`; it also forbade `exec_recovery.py`, which this dispatch orders created. `test_exec_no_raw_dispatch_boundary.py::test_worker_queue_checkpoint_recovery_remain_unavailable` (B-era) failed because C legitimately exported `WorkerSlot`/`QueueClaim` (and C/D lean mandates never re-ran the B suite). Both guards were repaired, not weakened: forbidden filenames now guard what is still genuinely forbidden (`exec_trace_verifier/custos/shell/api/bus.py` **plus the new E-doctrine substrate guards `exec_replay.py`/`exec_event_log.py`/`exec_self_healing.py`**); forbidden name fragments keep `workerpool`/`executionbus`/`checkpointmanager`/`recoveryengine` **plus new `selfhealing`/`replayengine`/`eventlog`**, with negating proof objects (e.g. `NoWorkerPoolProof`) excluded from the sweep. Both files pass after repair (12 passed).

## 4. P4-EXEC-D Prerequisite Confirmation

`agent/reports/P4_EXEC_D_EXECUTION_MODES_REGISTRY.md` exists; commits `7229c6e` + `3fc801f` in history. `ExecutionOutcome` consumed unchanged (no link field needed — verification requests derive all ids from the outcome); mode registry consumed unchanged (verification requests carry the requested mode/profile id; per-mode `requires_verifier`/`requires_p5_proof`/`requires_p9_authority` remain the D contract). `exec_outcome.py`, `exec_mode_profiles.py`, `exec_runtime_bridge.py`, and all B/C/D modules: **zero edits**.

## 5. Runtime Substrate Boundary Proof

- Python AurelExec v1 is the governance/control plane, reference implementation, contract authority, and operator-visible read-model layer — stated in module doctrine (`exec_algedonic.py` RUNTIME_SUBSTRATE_BOUNDARY_REASON), this report, and DECISIONS.
- **No Python-final-kernel claim was introduced**: `NoFinalPythonKernelClaimProof.python_final_kernel_claim` is unconstructibly True and `python_is_v1_reference_and_control_layer` unconstructibly False; `JudgmentProjection.python_final_kernel_claim` is structurally False.
- **Rust/WASM substrate not implemented**: no Cargo.toml/crates/rust/wasm paths exist (tested at repo root); `NoRustRewriteProof` fail-closed; future owner named as an operator-decided extraction (e.g. P4-EXEC-RUST-BRIDGE-DOCTRINE).
- **Deterministic replay engine, durable append-only event log, and workflow exact-copy/fork are explicitly unavailable**: structurally False on the projection and both substrate proofs; `exec_replay.py`/`exec_event_log.py` filenames are now guard-forbidden.
- **Contracts are future-extractable where practical**: every judgment object uses primitive/serializable fields (str/bool/int/tuple, enums serializing to strings, stable sha256 hashes via the existing canonical-JSON canon), deterministic pure builder functions, and closed-world enums — a non-Python substrate can emit identical shapes without redefining governance semantics.

## 6. Operational Debt Guard Proof

Avoided: automatic retry/multi-retry loops (retry-shaped plans without operator approval are unconstructible; exhausted budgets deterministically downgrade to operator review — "no retry storm"), bridge re-submit (E modules sweep-forbid `.submit(`), rollback execution (C proof still holds; ROLLBACK_REF_ONLY recommendation requires P9), recovery/self-healing engines, model-judge verifier calls, terminal/code execution, replay/event-log/exact-copy substrates, Rust/WASM, failure-history stores (repeated-failure evidence is caller-supplied). Four small modules + one projection class, all pure functions over frozen contracts.

Why model/terminal/code stay out and profiles-only honesty holds: the verifier hook vocabulary has **no AVAILABLE member** — a concrete evidence-producing verifier cannot even be claimed until a future pack builds one.

How P4-EXEC-F ambiguity was reduced: Exec-F's topology/concurrency/backpressure can consume `FailureClassification` (deterministic class/severity), `BoundedRecoveryPlan` (bounded budgets), and `AlgedonicSignal` (urgency channel) as typed inputs; `FAILURE_METADATA` and `RECOVERY_RECOMMENDATIONS` are total tables Exec-F can extend rather than re-derive; the repaired guards now also protect Exec-F from bus/replay/event-log scope creep.

## 7. Verification Request / Decision Proof

`build_execution_verification_request(outcome, ...)` derives ids from the real outcome; requests are constructible only with non-empty scope and carry `executes`/`writes_p5_proof` locked False. `decide_verification` is a pure deterministic ladder: request/outcome mismatch → ERROR; failed runtime outcome → FAILED (failure text preserved); no hook → UNAVAILABLE with reason + missing `verifier_hook`; unavailable hook or unsupported mode → UNAVAILABLE; hook without evidence → INCONCLUSIVE with `requires_operator_review=True`; hook + evidence refs → PASSED with `verified=True`. Structural: `verified=True` requires PASSED + availability + non-empty `evidence_refs` (all three violations unconstructible); PASSED without verified unconstructible; UNAVAILABLE with availability=True unconstructible; `requires_p5_proof` locked True and `trace_verified` locked False on every decision.

## 8. Verifier Hook Proof

`VerifierHook`: `side_effect_free` unconstructibly False; `calls_model`/`calls_tools`/`executes_terminal_or_code`/`mutates_runtime_state`/`writes_trace_proof` unconstructibly True; `VerifierHookAvailability` has no AVAILABLE member (PROFILE_ONLY/UNAVAILABLE/ERROR only); unavailable hooks must explain themselves. The default hook is PROFILE_ONLY with the honest UNAVAILABLE truth label (PROFILE_ONLY posture carried by the availability status per DEC-P4EXECD-02).

## 9. Failure Classification Proof

Closed-world 12-member `FailureClass` + 5-member `FailureSeverity` (exact sets tested). `FAILURE_METADATA` is a total table (tested total over the enum) fixing severity/retryable/recoverable/operator per class — a classification contradicting the table is **unconstructible**. `classify_execution_failure` maps deterministically: policy_* → POLICY_BLOCKED (URGENT), tool_failure → TOOL_ERROR (or TIMEOUT on timeout text), verifier_failure → VERIFICATION_FAILED, unknown → UNKNOWN_ERROR (CRITICAL); success+PASSED → NONE; success+no-decision/UNAVAILABLE/INCONCLUSIVE/REQUIRES_OPERATOR_REVIEW → VERIFIER_UNAVAILABLE; success+FAILED → VERIFICATION_FAILED. `classify_pre_submit_block` covers the fail-closed pre-kernel guards (lease codes → LEASE_INVALID, mode codes → MODE_UNAVAILABLE). Same inputs ⇒ same classification/hash (tested). `executes_recovery`/`grants_authority` unconstructibly True.

## 10. Bounded Recovery Plan Proof

`RECOVERY_RECOMMENDATIONS` is a total table over `FailureClass` (tested) fixing action + operator/P9/P5 requirements. E-local `BoundedRecoveryActionKind` (8 actions; named to avoid shadowing the A-pack `RecoveryActionKind`, per K-pack precedent). Structural: `recovery_executed`/`automatic_retry_available`/`rollback_execution_available`/`self_healing_available` unconstructibly True; a retry-shaped recommendation without operator approval is unconstructible (that would be automatic retry); a retry-shaped recommendation with zero remaining attempts is unconstructible — `create_bounded_recovery_plan` deterministically downgrades exhausted budgets to REQUEST_OPERATOR_REVIEW. High-risk classes (POLICY_BLOCKED, OUTPUT_CONTRACT_FAILED, RESOURCE_EXHAUSTED, UNKNOWN_ERROR) require P9 authority (tested).

## 11. Algedonic Signal Proof

`create_algedonic_signal_if_needed` emits only for URGENT/CRITICAL classifications (ERROR/WARNING/INFO produce None — tested per severity); kind mapping deterministic (POLICY_CONFLICT/VERIFICATION_FAILURE/RESOURCE_EXHAUSTION/UNSAFE_MODE_REQUEST/UNKNOWN_CRITICAL, REPEATED_FAILURE on caller-supplied evidence, RUNTIME_FAILURE fallback); same inputs ⇒ same signal. `grants_authority`/`bypasses_custos`/`executes_action` unconstructibly True; `operator_attention_required=True`; the message itself states that authority remains with the operator and P9.

## 12. Judgment Projection Proof

`JudgmentProjection` (read-only, frozen): verification status/availability/verified/reason, failure class/severity/retryable/recoverable/operator flags, recovery plan availability + recommended action + `recovery_executed=False`, algedonic presence/severity/attention, `p5_proof_required` locked True, and 15 structurally-False availability booleans (retry/rollback/recovery/self-healing, P5, P9, Shell/React/API, replay/event-log/exact-copy/Rust-WASM, python-final-kernel). Claiming `verified` without a PASSED status is unconstructible. Success-path honesty tested: runtime success + INCONCLUSIVE verification projects `verified=False` with VERIFIER_UNAVAILABLE.

## 13. No Automatic Retry Proof — §10; `NoAutomaticRetryProof` fail-closed (`bridge_resubmit_performed` locked False); E modules sweep-forbid `.submit(`.

## 14. No Rollback Execution Proof — C-era `NoRollbackExecutionProof` re-asserted in tests; ROLLBACK_REF_ONLY is a pointer recommendation requiring P9.

## 15. No Self-Healing Engine Proof — `NoSelfHealingProof` fail-closed; one plan per classification, no loop; `exec_self_healing.py` filename now guard-forbidden.

## 16. No Model Verifier Call Proof — `NoModelVerifierCallProof` fail-closed; hooks structurally cannot call models; E modules sweep-forbid model-router/providers imports.

## 17. No P5 Proof Proof — `NoP5ProofProof` fail-closed; every decision carries `requires_p5_proof=True` structurally; `trace_verified` unconstructible everywhere.

## 18. No P9 Authority Proof — `NoP9AuthorityProof` fail-closed (`authority_granted`/`custos_bypassed` locked False); high-risk recovery requires P9 in the recommendation table.

## 19. No Final Python Kernel Claim Proof — §5; structural on proof + projection.

## 20. No Rust/WASM Rewrite Proof — §5; no substrate paths exist (tested at repo root); proof fail-closed.

## 21. Roadmap Coverage Matrix

| Range | Status | Evidence |
|---|---|---|
| P4.14 Verifier Hook / Semantic Guard | DONE | `exec_verification.py`; test_exec_verification.py (7) |
| P4.15 Failure Classification / Bounded Recovery | DONE | `exec_failure.py` + `exec_recovery.py`; 12 tests |
| P4.16 Algedonic Signals / Escalation Kernel | DONE | `exec_algedonic.py`; test_exec_algedonic_signal.py (6) |
| Judgment projection + substrate boundary | DONE | `exec_projection.py` append; test_exec_judgment_projection.py (6) |

## 22. P4.14 Status — DONE (§7–§8). Truth labels: LIVE on decisions/requests (real tested judgment logic per dispatch posture); UNAVAILABLE on the profile-only hook.

## 23. P4.15 Status — DONE (§9–§10). Retryable is metadata only; automatic retry unavailable.

## 24. P4.16 Status — DONE (§11). Signal is local urgent visibility; Shell projection remains a future pack.

## 25. Lean Tests / Validation

```
.venv/bin/python -m compileall src/agentic_runtime/aurel_exec tests/aurel_exec → PASS
.venv/bin/python -m pytest tests/aurel_exec/test_exec_verification.py
  tests/aurel_exec/test_exec_failure_classification.py
  tests/aurel_exec/test_exec_bounded_recovery.py
  tests/aurel_exec/test_exec_algedonic_signal.py
  tests/aurel_exec/test_exec_judgment_projection.py -q → 31 passed
  (verification 7 · failure classification 6 · bounded recovery 6 ·
   algedonic 6 · judgment projection 6)
.venv/bin/python -m pytest tests/aurel_exec/test_exec_unsupported_modes_boundary.py
  tests/aurel_exec/test_exec_no_raw_dispatch_boundary.py -q → 12 passed
  (repaired stale guards — both FAILED on master before this pack; §3)
.venv/bin/python -m ruff check src/agentic_runtime/aurel_exec tests/aurel_exec → All checks passed
git status --short → only in-scope changes; clean after commit
```

Deliberately not run (lean mandate): full pytest, full `tests/aurel_exec`, runtime/tool/sandbox/trace regression globs, full-project mypy, coverage, bandit. Shared-file changes were additive (`__init__` exports, `exec_projection.py` new class) plus the two stale-guard repairs. The standing next-non-lean-pack full-suite note is now three packs old — the P4 exit-seal pack (or Exec-F if non-lean) should re-run the full aurel_exec suite as a priority.

## 26. Files Created / Modified

Created: `src/agentic_runtime/aurel_exec/{exec_verification,exec_failure,exec_recovery,exec_algedonic}.py`; `tests/aurel_exec/{test_exec_verification,test_exec_failure_classification,test_exec_bounded_recovery,test_exec_algedonic_signal,test_exec_judgment_projection}.py`; this report.

Modified: `aurel_exec/{__init__,exec_projection}.py` (additive); `tests/aurel_exec/{test_exec_unsupported_modes_boundary,test_exec_no_raw_dispatch_boundary}.py` (stale-guard repair, §3); `agent/{REPORTS,STATE,ACTIVE_TASK,ROADMAP,ARCHITECTURE,DECISIONS,TESTS}.md`.

Untouched: `exec_runtime_bridge.py`, `exec_outcome.py`, all A/B/C/D contract modules, all runtime/kernel sources, all web/frontend paths, no Rust/WASM paths.

## 27. What Was Deliberately Not Implemented

Automatic retry / multi-retry loops; bridge re-submit; rollback execution; recovery/self-healing engines; model verifier API calls; terminal/code execution; new sandbox execution; direct tool dispatch; deterministic replay engine; durable append-only event log; workflow exact-copy/fork; Rust crate/WASM runtime; failure-history persistence; P4.17–P4.20 (topology/concurrency/backpressure, telemetry, Shell binding, exit seal); P5 trace verification; P9 enforcement; Shell UI/React/API server.

## 28. Remaining Risks

- The verifier hook has no concrete evidence source yet — PASSED verification is reachable only with caller-supplied evidence refs; a real evidence-producing verifier (and its canon) is future work, and until then INCONCLUSIVE/UNAVAILABLE are the honest steady states.
- `repeated_failure` is caller-supplied — no failure-history store exists; Exec-F telemetry may build one honestly.
- TIMEOUT detection is text-heuristic over tool stderr; a structured timeout field from the runtime would be better and belongs to a future outcome refinement.
- The stale-guard episode shows lean packs can silently break unexecuted suites: three consecutive lean packs accumulated two failing tests. The P4 exit-seal pack must run the full aurel_exec suite and should consider a guard-freshness rule.
- Judgment objects are per-outcome values; aggregation (failure rates, storm detection) belongs to Exec-F/ExecBench.

## 29. Next Pack: P4-EXEC-F

Topology / Concurrency / Backpressure / ExecBench — consume failure classes, recovery budgets, and algedonic urgency as typed inputs to concurrency/backpressure decisions, add harness telemetry, and re-run the full aurel_exec suite (standing note). Optional future architecture task: P4-EXEC-RUST-BRIDGE-DOCTRINE for the substrate extraction contract.

## 30. Commit Hash

Recorded post-commit: see `git log` — `feat(aurel-exec): add execution judgment layer`.

## 31. Final Git Status

Clean after commit (`git status --short` empty); verified in the run that produced this report.
