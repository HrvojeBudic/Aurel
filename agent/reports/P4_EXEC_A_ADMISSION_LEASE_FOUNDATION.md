# P4-EXEC-A — AurelExec Doctrine / Contracts / Admission / Lease Foundation

## 1. Result Header

**DONE — GATE_AND_KEY_NOT_TURNED / P3_READINESS_IS_NOT_P4_ADMISSION / ADMISSION_IS_NOT_AUTHORIZATION / LEASE_IS_NOT_EXECUTION / NO_ATTEMPT_WITHOUT_VALID_LEASE / RUNTIME_SUBMIT_UNAVAILABLE_UNTIL_P4_EXEC_B / TRACE_VERIFIED_UNCONSTRUCTIBLE / CUSTOS_ENFORCEMENT_UNAVAILABLE_POLICY_SHADOW_ONLY / P4_EXEC_B_NEXT**

Date: 2026-07-03. Roadmap: Aurel Roadmap v5.5, P4.0–P4.3. Truth posture: backend admission/lease logic implemented and locally tested; test candidates are DEV_FIXTURE; runtime.submit, trace verification, Custos/P9 enforcement, Shell/React projection, and persistence are UNAVAILABLE. No LIVE claim, no TRACE_VERIFIED claim (the P4 truth-label vocabulary has no TRACE_VERIFIED member — the claim is unconstructible).

## 2. Pack Scope

P4-EXEC-A creates the first AurelExec foundation: the `agentic_runtime.aurel_exec` package with P4 truth labels and core enums, deterministic closed-world admission (request → NCF-style eight-gate chain → decision), the execution lease kernel (scoped, expiring, revocable capability token issued only from ADMIT), a minimal ExecJob and an ExecutionAttempt skeleton that exists only to prove lease-before-attempt, a read-only ExecProjection, four boundary proof objects, and a P4-EXEC-B handoff frame. Covered roadmap range: P4.0 Doctrine / Kernel Boundary Lock, P4.1 Execution Contract Types / Truth Labels, P4.2 P3 → P4 Admission Bridge, P4.3 Execution Lease Kernel.

## 3. Canon / Preflight

- Branch `master`, clean worktree at start (`git status --short` empty), HEAD `00d3475`.
- Canon read: `agent/AGENT.md` context, `agent/ACTIVE_TASK.md`, `agent/ROADMAP.md` pointer table, `agent/STATE.md`, `agent/ARCHITECTURE.md`, `agent/DECISIONS.md`, `agent/TESTS.md`, `agent/REPORTS.md`.
- Repo style adopted: frozen dataclasses with fail-closed `__post_init__` validation, closed-world `str` enums, canonical serialization / `stable_hash` reused from `aurel_flow.types` (no serialization canon fork), structured error codes (`AurelExecErrorCode` mirrors `AurelFlowErrorCode` shape).
- No canon conflicts found. The prompt's task title ("Doctrine / Contracts / Admission / Lease Foundation") refines the ROADMAP pointer's older placeholder title ("Minimal Execution Bridge / runtime.submit Boundary"); the bridge itself is explicitly P4-EXEC-B, consistent with the L handoff's `RuntimeSubmitBoundaryMap` (NOT_WIRED_FUTURE_P4).

## 4. P3 Seal / P4 Handoff Prerequisite Confirmation

- `agent/reports/P3_FLOW_L_EXTENDED_AURELFLOW_DOMAIN_SEAL_P4_HANDOFF.md` exists; ACTIVE_TASK records **P3 CONTROL-PLANE SEALED** and names P4-EXEC-A as the next task.
- The L handoff surfaces consumed conceptually here: `ExecutionRequestCandidateSurface` (candidate-only) → `ExecAdmissionRequest`; `DispatchabilityFrame` READY_BUT_NO_P4 marker → the P3 readiness gate (`P3_READY_MARKER`); `RuntimeSubmitBoundaryMap` NOT_WIRED_FUTURE_P4 → `RuntimeSubmitUnavailableReason` / `NoRuntimeSubmitProof`.
- Full P3 A–L regression suite re-run this session: **737 passed**.

## 5. Operational Debt Guard Proof

Complexity intentionally avoided: no worker registry, no queue, no execution bus, no checkpoint/rollback engine, no recovery engine, no algedonic routing (the `AlgedonicSignalKind` vocabulary exists for future packs; nothing routes it), no topology/concurrency system (`ExecutionTopologyKind` is vocabulary only), no session management, no runtime.submit bridge, no CLI binding, no Shell/React/API surface, no persistence, no model router. Six small modules, one builder fixture, deterministic pure functions only.

Why minimal remains useful: every object either (1) converts a P3-like candidate into an admission request, (2) decides admission deterministically, (3) issues/validates a scoped lease, (4) proves lease-before-attempt, (5) exposes honest unavailable status, or (6) names exactly what P4-EXEC-B consumes. Nothing else was added.

How P4-EXEC-B ambiguity was reduced: `P4ExecAHandoffFrame` names the consumable decision/lease/job/attempt IDs and the bound scope, `FUTURE_RUNTIME_BRIDGE_STEPS` pins the minimal bridge chain (ExecJob → ExecutionLease → ExecutionAttempt → CommandEnvelope → AgenticRuntime.submit() → ExecutionOutcome), and `STANDARD_BRIDGE_REQUIREMENTS` assigns each remaining requirement a future owner (P4-EXEC-B / P5 / P9 / P2 Shell).

## 6. No Runtime Execution Proof

- Source-level: `tests/aurel_exec/test_exec_no_runtime_submit_boundary.py` sweeps every `aurel_exec/*.py` file for forbidden imports (`subprocess`, `socket`, `requests`, `httpx`, `urllib`, `runtime`, `tool_runtime`, `entity`, `ToolRuntime`, `AgenticEntity`) — none exist. Trace and Custos/policy/memory/identity module imports are swept likewise in the other two boundary test files.
- Object-level: no pack object exposes a `submit`/`dispatch`/`execute`/`run`/`invoke`/`spawn` attribute; `ExecutionAttempt.runtime_submit_called=True` is unconstructible; `ExecProjection.runtime_submit_available=True` is unconstructible.
- Invariants held: runtime_submit_available/called/wired=false, tool_dispatched=false, model_invoked=false, verifier_executed=false, sandbox_executed=false, network_called=false, subprocess_called=false, trace_written=false, ledger_written=false, memory_written=false, policy_enforced=false, custos_enforced=false, execution_performed=false. Filesystem mutation in this task = in-scope repo source/test/report edits only.

## 7. Roadmap Coverage Matrix

| Range | Status | Evidence |
|---|---|---|
| P4.0 Doctrine / Kernel Boundary Lock | DONE | `exec_types.py` module doctrine + this report §8; boundary tests |
| P4.1 Execution Contract Types / Truth Labels | DONE | `exec_types.py`; `tests/aurel_exec/test_exec_types.py` (13 tests) |
| P4.2 P3 → P4 Admission Bridge | DONE | `exec_admission.py`; `tests/aurel_exec/test_exec_admission.py` (17 tests) |
| P4.3 Execution Lease Kernel | DONE | `exec_lease.py` + `exec_job.py`; lease/job-guard tests (19 tests) |

## 8. P4.0 Doctrine / Kernel Boundary Lock — DONE

The doctrine is recorded in `exec_types.py` (module docstring), the package `__init__.py`, and here: *P4-EXEC-A creates the execution gate and the execution key; it does not turn the key.* Laws preserved structurally: No Raw Execution (no side-effect surface exists), Lease Before Attempt (`create_execution_attempt` fail-closes without a currently valid lease), Admission Is Not Authorization (`ExecCustosStatus` has no ENFORCED/AUTHORIZED member), Runtime Success ≠ Semantic Success (no success vocabulary exists at all in this pack), Trace-Bound ≠ Trace-Verified (`TraceBindingStatus`/`ExecTraceStatus` have no BOUND/VERIFIED members; `ExecTruthLabel` has no TRACE_VERIFIED member). runtime.submit and P5/P9 are not implemented. Truth labels: contracts locally tested; unavailability honest. 

## 9. P4.1 Execution Contract Types / Truth Labels — DONE

`AUREL_EXEC_CONTRACT_VERSION = "aurel_exec.v1"` plus per-object versions. Enums implemented exactly as dispatched: `ExecTruthLabel` (10 members, LIVE present but unassignable — `FORBIDDEN_EXEC_TRUTH_LABELS` fail-closes it at construction; no TRACE_VERIFIED member), `ExecAdmissionState` (8), `ExecLifecycleState` (6 — no RUNNING/EXECUTED/COMPLETED member), `ExecutionMode` (8), `ExecutionTopologyKind` (8), `ExecutionPlasticityLevel` (6), `ExecutionFailureClass` (12), `RecoveryActionKind` (10), `AlgedonicSignalKind` (10), `TraceBindingStatus` (4 — no BOUND/VERIFIED). Support vocabularies: `ExecPolicyStatus`/`ExecCustosStatus` (no ENFORCED/AUTHORIZED), `ExecTraceStatus` (no VERIFIED), `ExecUnavailableSystem`, `ExecMissingRequirementKind`, `ExecAdmissionGateKind` + `ADMISSION_GATE_ORDER`. Deterministic serialization and stable hashes reuse `aurel_flow.types` canon; unknown constructor fields raise `TypeError` (closed-world dataclasses). Truth labels: LIVE unassignable, DEV_FIXTURE for fixtures, UNAVAILABLE reasons named per system.

## 10. P4.2 P3 → P4 Admission Bridge — DONE

`ExecAdmissionRequest` (P3 candidate ref + readiness marker + mode/tool/args-hash/sandbox/budget/authority/policy/verifier/trace-binding refs, DEV_FIXTURE-safe, hashable, constructible-with-gaps so gates can reject deterministically). `decide_admission` is a pure function over the eight-gate NCF chain — source validity → P3 readiness marker → authority ref → sandbox profile → budget ref → verifier requirement → trace binding availability → policy/Custos availability — where the first non-ADMIT gate locks the outcome. Outcomes: ADMIT / HOLD / REJECT / REQUIRE_OPERATOR / REQUIRE_POLICY / REQUIRE_VERIFIER / REQUIRE_CONTEXT_REFRESH (vocabulary) / ERROR. Every non-ADMIT decision explains itself with `ExecMissingRequirement`s; every decision carries `STANDARD_UNAVAILABLE_REASONS` naming runtime.submit (P4-EXEC-B), trace verification (P5 AurelTrace), Custos enforcement (P9 Custos), and policy shadow-only (P9). Proven: **P3 readiness does not imply P4 admission** (a READY_BUT_NO_P4 candidate is still held by the sandbox gate) and **P4 admission does not imply P9 authorization** (`custos_status` is structurally ENFORCEMENT_UNAVAILABLE; no `authorized` attribute exists). The gate chain calls no runtime, Custos, Trace, tool, model, or sandbox. Unavailable: nothing in the bridge is P4-EXEC-B dispatch.

## 11. P4.3 Execution Lease Kernel — DONE

`ExecutionLease` binds `LeaseScope` (allowed mode / tool / args hash / sandbox profile / budget scope / authority scope / policy snapshot refs), `max_attempts ≥ 1`, logical-tick issuance/expiry (deterministic — no wall clock), and a `revoked`/`LeaseRevocationState` pair that must agree. `issue_execution_lease` denies (with `ExecLeaseDenied` + `LeaseDenialReason`) any non-ADMIT decision or decision/request mismatch. `validate_execution_lease` is a deterministic side-effect-free verdict; a `LeaseValidationResult` claiming valid-while-expired/revoked is unconstructible. `revoke_execution_lease` returns a new frozen lease. `ExecJob` is created only from ADMIT (lifecycle ADMITTED — a future executable unit, not execution). `ExecutionAttempt` proves lease-before-attempt: `create_execution_attempt` fail-closes on expired (LEASE_EXPIRED), revoked (LEASE_REVOKED), or job-mismatched (LEASE_JOB_MISMATCH) leases, and `runtime_submit_called=True` is unconstructible. Proven: **execution lease does not imply execution success** (no success/outcome vocabulary exists; a valid lease produces at most a pending attempt skeleton) and **no execution attempt can exist without valid lease**.

## 12. P4-EXEC-B Handoff Clarity

- **Minimal future runtime.submit bridge surface:** `FUTURE_RUNTIME_BRIDGE_STEPS = (ExecJob → ExecutionLease → ExecutionAttempt → CommandEnvelope → AgenticRuntime.submit() → ExecutionOutcome)`; a truncated chain is unconstructible on the frame. Naming the chain is not building it.
- **Objects Exec-B can consume:** `ExecAdmissionDecision.decision_id`, `ExecutionLease.lease_id` (+ full bound scope), `ExecJob.exec_job_id`, `ExecutionAttempt.attempt_id` — all carried by `P4ExecAHandoffFrame` with allowed mode/tool/args-hash/sandbox/budget/authority constraints.
- **Boundaries Exec-B must preserve:** lease-before-attempt; admission-is-not-authorization; scope binding (Exec-B must check submitted command envelopes against the lease scope); truth-label honesty (no LIVE until a real governed submit happens, and even then runtime result ≠ semantic success); trace binding without verification claims (P5 verifies); policy shadow-only until P9.
- **Unavailable until P4-EXEC-B/P5/P9:** runtime.submit bridge and any dispatch (P4-EXEC-B); trace binding/verification and evidence spine (P4-EXEC-B binding refs at most, P5 proof); execution authorization and policy enforcement (P9); operator-facing execution projection (P2 AurelShell); persistence (owner to be fixed by P4 persistence strategy per the L boundary map).

## 13. AurelExec Package Proof

`src/agentic_runtime/aurel_exec/` with `__init__.py` (doctrine + full explicit export surface), `exec_types.py`, `exec_errors.py`, `exec_admission.py`, `exec_lease.py`, `exec_job.py`, `exec_projection.py`. Not re-exported from the `agentic_runtime` top level (same convention as `aurel_flow`). Imports cleanly; `.venv/bin/python -m compileall src tests` passes.

## 14. Admission Proof

17 admission tests: fixture admits through all 8 gates; determinism (same request ⇒ identical decision/hash); missing source ref REJECTs with gate lock after gate 1; UNAVAILABLE/ERROR modes REJECT; non-ready marker HOLDs; sandbox-less TOOL mode HOLDs while CONVERSATION mode does not require sandbox; missing authority REQUIRE_OPERATOR; missing budget HOLDs; TERMINAL-without-verifier REQUIRE_VERIFIER; missing policy context REQUIRE_POLICY; every non-ADMIT decision explains itself; ADMIT carries ENFORCEMENT_UNAVAILABLE custos + SHADOW_ONLY policy + TRACE_VERIFICATION_UNAVAILABLE trace statuses and P4-EXEC-B/P5/P9 future owners.

## 15. Lease Proof

11 lease tests: scope binding field-by-field from the request; denial for REJECT/HOLD/REQUIRE_OPERATOR/REQUIRE_POLICY decisions and for decision/request mismatch; valid-before-expiry; expired invalid; revoked invalid; revocation returns a new frozen lease (original untouched, direct mutation raises `FrozenInstanceError`); valid-while-expired unconstructible; bad lease window and `max_attempts=0` fail closed; LIVE label unconstructible; no execution attribute surface; deterministic lease id/hash.

## 16. Job / Attempt Guard Proof

8 job/attempt tests: job only from ADMIT (JOB_DENIED otherwise); job has no execution surface; attempt created under valid lease with `runtime_submit_called=False` and ATTEMPT_PENDING; attempt denied on expired/revoked/job-mismatched lease with distinct error codes; `runtime_submit_called=True` unconstructible; attempt without a lease reference unconstructible.

## 17. Projection Proof

9 projection tests: full-slice projection shows ADMIT/LEASE_VALID/ADMITTED/ATTEMPT_PENDING_WITH_VALID_LEASE; no-lease projection is BLOCKED_NO_VALID_LEASE; revoked lease projected honestly; runtime.submit/trace/policy availability all False with named reasons (P4-EXEC-B/P5/P9) and availability=True unconstructible; projection frozen and `read_only=True` (False unconstructible); handoff frame names consumable IDs and bound scope; full bridge chain pinned; `is_p4_exec_b`/`runtime_submit_wired`/`execution_performed` True unconstructible.

## 18. No runtime.submit / No Raw Execution / No Trace-Verified / No Custos-Enforcement Proof

Four proof objects (`NoRuntimeSubmitProof`, `NoRawExecutionProof`, `NoTraceVerifiedProof`, `NoCustosEnforcementProof`) with builders; every boundary boolean fail-closed at construction (True/False flips unconstructible), reasons and future pack owners mandatory. 18 boundary tests across three files additionally sweep package source for forbidden runtime/trace/Custos/policy/memory/identity imports and side-effect modules, verify no submit/dispatch verb exists in the public API, and hold `runtime_submit_called=False` across the full slice. These proofs are report evidence and structural checks only — not P5 trace proof of runtime behavior.

## 19. Tests / Validation

All run through `.venv/bin/python` (canonical per `agent/TESTS.md`):

```
.venv/bin/python -m compileall src tests                              → PASS
.venv/bin/python -m pytest tests/aurel_exec -q                        → 76 passed
  test_exec_types.py 13 · test_exec_admission.py 17 · test_exec_lease.py 11
  test_exec_job_guards.py 8 · test_exec_projection.py 9
  no_runtime_submit 6 · no_trace_verified 6 · no_custos_enforcement 6
.venv/bin/python -m pytest tests/test_p3_flow_i_scheduling_intent.py
  tests/test_p3_flow_j_p4_handoff_clarity.py
  tests/test_p3_flow_k_p4_handoff_readiness.py
  tests/test_p3_flow_l_domain_seal.py -q                              → 29 passed
.venv/bin/python -m pytest tests/test_p3_flow_*.py -q                 → 737 passed (full A–L)
.venv/bin/python -m ruff check src tests                              → All checks passed
.venv/bin/python -m mypy src/agentic_runtime                          → Success, 417 files
```

Honest notes: the dispatch listed regression files `test_p3_flow_k_p4_handoff_readiness.py`, `test_p3_flow_j_p4_handoff_clarity.py`, `test_p3_flow_i_scheduling_intent.py` (exist, run) and `test_p3_flow_l_extended_domain_seal.py` (does not exist — the real seal test `test_p3_flow_l_domain_seal.py` was run instead, plus the full L suite via the A–L sweep). Full-suite pytest/coverage/bandit not run (lean validation doctrine: no runtime/security/sandbox path touched).

## 20. Files Created / Modified

Created: `src/agentic_runtime/aurel_exec/{__init__,exec_types,exec_errors,exec_admission,exec_lease,exec_job,exec_projection}.py`; `tests/aurel_exec/{test_exec_types,test_exec_admission,test_exec_lease,test_exec_job_guards,test_exec_projection,test_exec_no_runtime_submit_boundary,test_exec_no_trace_verified_boundary,test_exec_no_custos_enforcement_boundary}.py`; this report.

Modified: `agent/REPORTS.md`, `agent/STATE.md`, `agent/ACTIVE_TASK.md`, `agent/ROADMAP.md`, `agent/ARCHITECTURE.md`, `agent/DECISIONS.md`, `agent/TESTS.md`.

Untouched (verified): `runtime.py`, `tool_runtime.py`, `entity.py`, `repo_agent.py`, `cli.py`, `trace*`, `policy*`, `memory*`, `sandbox*`, `custos/`, `aurel_shell/`, `aurel_flow/` source, all web/frontend paths.

## 21. What Was Deliberately Not Implemented

P4-EXEC-B runtime bridge; any `AgenticRuntime.submit()` call or wiring; `ToolRuntime.dispatch`; worker slot/queue; execution bus; checkpoint/rollback; recovery engine; algedonic routing; topology/concurrency execution; managed execution sessions; tool/model/verifier/terminal/code/sandbox execution; P5 trace binding/verification; P9 Custos authorization/enforcement; HITL/ApprovalGate bridges; persistence; CLI binding; Shell UI/React/API server; memory/policy/identity access.

## 22. Remaining Risks

- The P3 readiness gate keys on the string marker `READY_BUT_NO_P4`; if P3-FLOW-I's `DispatchabilityReason` vocabulary ever changes, `P3_READY_MARKER` must be updated in one place (`exec_types.py`). Exec-B should consume typed frames directly.
- Lease time is a caller-supplied logical tick; P4-EXEC-B must define who owns the clock before real submits.
- `decision_id`/`lease_id`/`attempt_id` are deterministic hashes of inputs — collision-safe for contracts but not a persistence identity strategy (persistence remains UNAVAILABLE by design).
- Admission gate policy (which modes require sandbox/verifier) is a static contract table; P9 will own the real policy source later.
- Shell projection of exec state remains UNAVAILABLE; operators inspect via Python read models only.

## 23. Next Pack: P4-EXEC-B

ExecJob / Attempt / Session / Runtime Submit Bridge — consume `P4ExecAHandoffFrame` (admission decision + lease + job + attempt skeleton + bound scope), build the CommandEnvelope conversion, and perform the first governed `runtime.submit(read_file)` under operator review, with trace binding refs (verification still P5) and policy still shadow-only (enforcement still P9).

## 24. Commit Hash

Recorded post-commit in `agent/ACTIVE_TASK.md` follow-up entry; see `git log` — commit message `feat(aurel-exec): add admission and lease foundation`.

## 25. Final Git Status

Clean after commit (`git status --short` empty); verified in the run that produced this report.
