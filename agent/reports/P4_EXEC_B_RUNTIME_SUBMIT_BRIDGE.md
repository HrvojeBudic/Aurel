# P4-EXEC-B — First Governed Runtime Submit Bridge

## 1. Result Header

**DONE — KEY_TURNED_ONCE / EXISTING_KERNEL_NOT_SECOND_EXECUTOR / SESSION_REQUIRED_FOR_SUBMIT / NO_VALID_LEASE_NO_SUBMIT / RUNTIME_SUCCESS_IS_NOT_SEMANTIC_SUCCESS / TRACE_BOUND_IS_NOT_TRACE_VERIFIED / UNSUPPORTED_MODES_UNAVAILABLE / NO_DIRECT_DISPATCH / P4_EXEC_C_NEXT**

Date: 2026-07-03. Roadmap: Aurel Roadmap v5.5, P4.4–P4.6. Truth posture: bridge results/outcomes from the actual `AgenticRuntime.submit()` call are LIVE (proven by tests against the real kernel); trace bindings with real transition refs are TRACE_BOUND with `trace_verified=False` structurally; candidates/fixtures are DEV_FIXTURE; terminal/code/model/conversation/composite execution, worker/queue/bus/checkpoint/recovery, P5 proof, P9 full enforcement, and Shell/React/API remain UNAVAILABLE.

## 2. Pack Scope

P4-EXEC-B turns the key once: lifecycle-capable `ExecJob` and submit-aware `ExecutionAttempt` (P4.4), minimal `ExecutionSession` (P4.5), and `ExecRuntimeBridge` (P4.6) — which validates job + lease + session + attempt coherence, builds a repo-standard `CommandEnvelope`, calls the existing `AgenticRuntime.submit()` kernel exactly once for the safe read-only `read_file` path, normalizes the captured result into `ExecutionOutcome`, and binds real trace refs into `ExecTraceBinding` without ever claiming verification. `ExecProjection` now shows job/session/attempt/submit/outcome/trace-boundary state.

## 3. Canon / Preflight

Branch `master`, clean at start, HEAD `09dc841` (P4-EXEC-A hash record). Canon read: ACTIVE_TASK (P4-EXEC-A complete, P4-EXEC-B next), ROADMAP pointer, STATE, ARCHITECTURE, DECISIONS, TESTS, REPORTS, the P4-EXEC-A report, and the runtime sources (`runtime.py`, `core_types.py`, `tools.py`, `sandbox.py`, `policy.py`) plus `tests/conftest.py` submit patterns. No canon conflicts.

## 4. P4-EXEC-A Prerequisite Confirmation

`agent/reports/P4_EXEC_A_ADMISSION_LEASE_FOUNDATION.md` exists; commit `c99c604` in history; the A package and its 78 tests (after the sanctioned B expansions below) pass in this run. The A handoff surface was consumed as designed: admission decision → lease → job → attempt skeleton → the pinned bridge chain ExecJob → ExecutionLease → ExecutionAttempt → CommandEnvelope → AgenticRuntime.submit() → ExecutionOutcome is now implemented exactly as `FUTURE_RUNTIME_BRIDGE_STEPS` declared it.

## 5. Operational Debt Guard Proof

Avoided: worker slot/pool, queue claim, execution bus, checkpoint/rollback, recovery engine, retry (structurally refused: a submitted attempt cannot resubmit), execution mode registry/profiles, verifier engine, algedonic routing, topology/concurrency/backpressure, harness telemetry, CommandEnvelope redesign (used `CommandEnvelope.make` as-is), runtime.py changes (zero), CLI binding, Shell/React/API. Four new modules + three expanded ones; the bridge is one class with one public method (`submit_once`).

Why minimal: every object either binds a leased job to a session, creates a submit-aware attempt, builds the envelope, calls the kernel once, normalizes the result, exposes honest state, or proves a boundary. Nothing else was added.

How P4-EXEC-C ambiguity was reduced: Exec-C now has a proven single-submit bridge to wrap runtime shape around — `RuntimeBridgeExecution` bundles the exact objects (job/session/attempt/outcome/trace binding) a worker/queue/bus/checkpoint layer must manage, the projection already carries `worker_queue_available/execution_bus_available/checkpoint_available/recovery_available` as structurally-False markers Exec-C will flip honestly, and the no-retry rule marks exactly where bounded recovery will attach later.

## 6. Runtime Submit Bridge Proof

`ExecRuntimeBridge.submit_once` calls `self._runtime.submit(envelope, card)` — the injected kernel's own submit. Proven two ways: (1) `test_first_read_file_demo_produces_execution_outcome` runs against a **real** `build_runtime(...)` kernel with `mock.patch.object(..., wraps=runtime.submit)` asserting `call_count == 1`, real file content returned through the kernel's tool path, and a real `txn_*` transition ref captured; (2) `test_runtime_bridge_calls_agentic_runtime_submit` runs against a recording fake exposing only `submit(cmd, card)` — the bridge completes a full pass against an object with no dispatch/sandbox/trace surface at all, proving it needs nothing but the kernel syscall.

## 7. No Second Executor Proof

The bridge contains no execution machinery: no tool functions, no sandbox access, no subprocess/network/filesystem primitives — source-swept by `test_runtime_bridge_does_not_call_tool_runtime_directly` (forbids the tools-module import, `.dispatch(`, subprocess/socket/HTTP imports, sandbox/trace/policy/custos/memory imports, `open(`/`os.system`/`eval(`/`exec(` in every `aurel_exec/*.py`). The kernel import is TYPE_CHECKING-only and sanctioned in exactly one module (`exec_runtime_bridge.py`), enforced by the updated A boundary sweep. The fake-kernel test proves behaviorally that only `.submit` is touched.

## 8. Roadmap Coverage Matrix

| Range | Status | Evidence |
|---|---|---|
| P4.4 ExecJob / Attempt Lifecycle | DONE | `exec_types.py` transition maps + `exec_job.py`; 9 lifecycle tests |
| P4.5 Managed Execution Sessions | DONE | `exec_session.py`; 7 session tests |
| P4.6 Runtime Submit Bridge | DONE | `exec_runtime_bridge.py` + outcome/trace-binding/demo; 41 tests |

## 9. P4.4 ExecJob / Attempt Lifecycle — DONE

`ExecLifecycleState` expanded to 12 closed-world members (SESSION_BOUND, READY_TO_SUBMIT, RUNNING, SUBMITTED, SUCCEEDED, FAILED added; still no EXECUTED/COMPLETED/VERIFIED/PROVEN). `JOB_LIFECYCLE_TRANSITIONS` and `ATTEMPT_LIFECYCLE_TRANSITIONS` are total over the enum with attempt-only states unreachable for jobs and vice versa; `transition_exec_job`/`transition_execution_attempt` fail closed on invalid transitions. `ExecJob` gained lease/session refs, requested mode/tool, and update ticks; `bind_lease_to_job` moves ADMITTED → LEASED. `ExecutionAttempt` gained session/command/outcome/trace refs and the submit-truth guard: `runtime_submit_called=True` requires a submit-aware state + command id + bound session; SUBMITTED/SUCCEEDED without the call is unconstructible. Attempts cannot submit with expired (LEASE_EXPIRED), revoked (LEASE_REVOKED), or scope-mismatched (LEASE_SCOPE_MISMATCH) leases — all refused before any kernel call, verified by the recording fake (`submit_calls == []`). ATTEMPT_PENDING doubles as the attempt's PENDING state (kept from A instead of adding a duplicate member).

## 10. P4.5 Managed Execution Sessions — DONE

`ExecutionSession` (OPEN/RUNNING/CLOSED/FAILED/ERROR with a deterministic transition map and open/close tick-window consistency) opens only for a LEASED job, binds via `bind_session_to_job` (LEASED → SESSION_BOUND), and carries operator/runtime/sandbox/trace-run context refs. `is_workflow`/`is_queue`/`is_worker`/`is_checkpoint` are structurally False. Session is required for submit: a sessionless attempt raises SESSION_REQUIRED and a CLOSED session raises SESSION_INVALID, both before any kernel call. Helpers: `open_execution_session`, `mark_session_running`, `close_execution_session`, `mark_session_failed`.

## 11. P4.6 Runtime Submit Bridge — DONE

`ExecRuntimeBridge(runtime)` validates the injected kernel exposes callable `submit`; `submit_once(request, job=, lease=, session=, attempt=, card=, current_tick=)` runs the deterministic guard ladder — mode/tool support → request/object coherence (ids + issuer card) → lease validity + scope (mode, tool, bound args hash via `stable_hash`) → session active + attempt session-bound → job/attempt submit-eligible states → no resubmit — then builds the envelope via `CommandEnvelope.make`, calls the kernel once, and normalizes. `RuntimeBridgeSubmitRequest`/`RuntimeBridgeSubmitResult` (submitted status ⟺ actually called; success ⟹ called; `direct_tool_dispatch_called`/`trace_verified` unconstructibly True) and `RuntimeBridgeExecution` (result + outcome + trace binding + updated job/session/attempt) carry the pass. `RuntimeSubmitStatus` has no VERIFIED member.

## 12. Safe Read-Only Submit Demo

Tool: `read_file` — the repo's canonical read-only tool (`ToolSpec("read_file", ...)` in `tools.py`, `ToolRiskLevel.TRIVIAL`, `FILESYSTEM_READ`, no verifier requirement). Demo (`tests/aurel_exec/test_exec_first_read_file_demo.py`) against a real kernel in a pytest tmp sandbox: DEV_FIXTURE candidate → ADMIT → lease scoped to `read_file` + args hash → job → session (bound to the kernel's real trace run id) → attempt → bridge → real submit → `ExecutionOutcome` with the actual file content as summary → TRACE_BOUND binding with a real `txn_*` ref → projection showing the full state → session closed. The failure demo reads a missing file through the same path: `success=False`, `FileNotFoundError` preserved in `error_message`, job/attempt FAILED — runtime failure is never rewritten.

## 13. AgenticRuntime.submit Signature Observed

`src/agentic_runtime/runtime.py:168`: `def submit(self, cmd: CommandEnvelope, card: AgentCard) -> CommandResult`. `CommandResult` carries `observation: ObservationEnvelope` (success/stdout/stderr), `verifier: VerifierResult` (passed), `decision: PolicyDecision` (verdict), `transition: StateTransitionRecord | None` (id + entry_hash — the trace refs), `rolled_back`, approval fields, and `ok = observation.success and verifier.passed`. The kernel path runs contract validation → budget → identity/sandbox governance gates → policy → HITL approval → sandbox profile → dispatch → verifier → trace append. The bridge adapts to this signature exactly; `runtime.py` was not modified.

## 14. CommandEnvelope Builder / Adapter Proof

The bridge uses the repo-standard factory as-is: `CommandEnvelope.make(issuer_card_id=card.id, tool=request.requested_tool_name, args=request.args_dict(), rationale=..., declared_risk=RiskLevel.LOW, expected_effect=...)`. Lease constraints are preserved by construction — the args dict is validated against the lease's `allowed_args_hash`, the tool against `allowed_tool_name`, the mode against `allowed_execution_mode` before the envelope is built; the attempt records `command_id` and `command_envelope_hash` (the envelope's own `command_hash()`), binding job/attempt/session refs to the exact submitted command.

## 15. ExecutionOutcome Proof

`normalize_runtime_result` is deterministic over the captured result: `success = observation.success and verifier.passed`, RUNTIME_SUCCESS/RUNTIME_FAILURE status agreement enforced structurally, stderr preserved as `error_message` with `tool_failure`/`verifier_failure`/`policy_*` categories, `verifier_passed`/`rollback_performed`/`trace_ref` captured, summaries truncated at 400 chars. `semantic_success` and `trace_verified` are unconstructibly True — runtime success is not semantic success (no verifier evidence engine exists), and the status vocabulary has no SEMANTIC/VERIFIED member.

## 16. ExecTraceBinding Proof

Bound only from real refs: `trace_bound ⟺ runtime_trace_ref is not None`, refs taken from the kernel's own `StateTransitionRecord` (`id`, `entry_hash`); a bound binding must carry TRACE_BOUND and an unbound one must not; `trace_verified=False` and `p5_required=True` are structural. When the runtime returns no transition, the binding is honestly unbound UNAVAILABLE (tested). AurelExec writes nothing to the trace — the kernel already recorded it.

## 17. No Direct Dispatch Proof

`NoDirectDispatchProof` (11 fail-closed booleans: direct dispatch/subprocess/network/raw-filesystem/sandbox/model/verifier + manual trace/ledger/policy/custos) + builder; behavioral proof via the submit-only fake; source sweeps in both the B dispatch-boundary file and the updated A sweep (kernel import sanctioned only in `exec_runtime_bridge.py`, TYPE_CHECKING-only, verified line-level); every blocked submit test asserts `fake.submit_calls == []`.

## 18. No Trace Verified Proof

Even after a real submit with real refs: binding/outcome/result all hold `trace_verified=False` with True unconstructible; `ExecTruthLabel` still has no TRACE_VERIFIED member; projection `trace_verified_available` stays locked False with the P5 reason; the A-era `NoTraceVerifiedProof` still builds and names P5 AurelTrace.

## 19. Unsupported Modes Unavailable Proof

`SUPPORTED_BRIDGE_EXECUTION_MODES == (TOOL,)`, `SUPPORTED_BRIDGE_TOOLS == ("read_file",)`. All seven non-TOOL modes are refused pre-kernel (UNSUPPORTED_EXECUTION_MODE) and covered by `UnsupportedExecutionModeProof`s naming P4-EXEC-D as future owner; write/shell/python/edit/delete tools are refused (UNSUPPORTED_TOOL) even in TOOL mode; a supported mode cannot carry an unsupported-mode proof; the projection lists the unsupported modes and keeps worker/queue/bus/checkpoint/recovery structurally False.

## 20. Tests / Validation

All through `.venv/bin/python`:

```
compileall src tests                                → PASS
pytest tests/aurel_exec -q                          → 140 passed
  A suite (updated): 78 · B new: 62
  job_lifecycle 9 · session 7 · runtime_bridge 12 · outcome 8
  trace_binding 6 · first_read_file_demo 3 (real kernel)
  no_raw_dispatch 5 · no_trace_verified_b 5 · unsupported_modes 7
pytest tests/test_runtime*.py tests/test_tool*.py
  tests/test_sandbox*.py tests/test_trace*.py -q    → 421 passed
pytest tests/test_p3_flow_*.py -q                   → 737 passed
ruff check src tests                                → All checks passed
mypy src/agentic_runtime                            → Success, 421 files
```

Sanctioned A-test updates (pack-boundary evolution, recorded in DECISIONS): `test_exec_types.py` exact enum sets gained TRACE_BOUND + the six submit-aware lifecycle states (still forbidding EXECUTED/COMPLETED/VERIFIED/PROVEN) and a new transition-map totality test; `test_exec_no_runtime_submit_boundary.py` sweep now sanctions the kernel import in `exec_runtime_bridge.py` only (TYPE_CHECKING-verified) and checks callables (not the `SUBMIT_AWARE_ATTEMPT_STATES` constant) for ambient submit/dispatch verbs. No other A tests changed; all A guards (LIVE forbidden on eligibility objects, lease-before-attempt, projection fail-closed flips) still pass.

## 21. Files Created / Modified

Created: `src/agentic_runtime/aurel_exec/{exec_session,exec_runtime_bridge,exec_outcome,exec_trace_binding}.py`; `tests/aurel_exec/{_bridge_helpers,test_exec_job_lifecycle,test_exec_session,test_exec_runtime_bridge,test_exec_outcome,test_exec_trace_binding,test_exec_first_read_file_demo,test_exec_no_raw_dispatch_boundary,test_exec_no_trace_verified_boundary_b,test_exec_unsupported_modes_boundary}.py`; this report.

Modified: `aurel_exec/{__init__,exec_types,exec_errors,exec_job,exec_projection}.py`; `tests/aurel_exec/{test_exec_types,test_exec_no_runtime_submit_boundary}.py`; `agent/{REPORTS,STATE,ACTIVE_TASK,ROADMAP,ARCHITECTURE,DECISIONS,TESTS}.md`.

Untouched (verified by git diff): `runtime.py`, `tools.py`, `entity.py`, `cli.py`, `trace*`, `policy*`, `sandbox*`, `memory*`, `custos/`, `aurel_shell/`, `aurel_flow/`, all web/frontend paths.

## 22. What Was Deliberately Not Implemented

Worker slot/queue claim (P4.7), execution bus (P4.8), checkpoint/rollback (P4.9), execution mode registry/profiles (P4.10+), verifier engine (P4.14), recovery/retry (P4.15 — resubmit structurally refused), algedonic routing (P4.16), topology/concurrency/backpressure (P4.17), harness telemetry (P4.18), P5 trace verification, P8 routing, P9 Custos enforcement (runtime policy/approval gates run inside the kernel as before; AurelExec adds no enforcement), Shell UI/React/API server, persistence, service mesh/distributed runtime.

## 23. Remaining Risks

- The bridge trusts the injected kernel to be the real governed runtime; a caller could inject a permissive fake (tests do, deliberately). Kernel provenance/attestation is a P5/P9 concern.
- Session/job/attempt state objects are immutable snapshots; the caller must thread the returned copies (`RuntimeBridgeExecution`). Exec-C's runtime shape should own that threading.
- `ExecutionOutcome.error_category` derives from result shape heuristics (tool/verifier/policy); a richer failure taxonomy belongs to the Exec-E failure classification pack.
- The demo relies on `UnsafeLocalSandbox` in tmp dirs (repo-standard test posture); no production sandbox claim is made.
- Trace refs are captured, not verified — P5 must verify chain membership before any proof claim.

## 24. Next Pack: P4-EXEC-C

Worker / Queue / Bus / Checkpoint Runtime Shape — wrap runtime management around the proven single-submit bridge: worker slots and queue claims feeding `submit_once`, a local execution bus for `RuntimeBridgeExecution` events, and checkpoint refs around submit boundaries, flipping the projection's structurally-False availability markers honestly as each arrives.

## 25. Commit Hash

Recorded post-commit: see `git log` — `feat(aurel-exec): add first runtime submit bridge`.

## 26. Final Git Status

Clean after commit (`git status --short` empty); verified in the run that produced this report.
