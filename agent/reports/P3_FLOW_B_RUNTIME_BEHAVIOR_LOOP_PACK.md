# P3-FLOW-B — Runtime Behavior Loop Pack

## 1. Result Header

**DONE — RUNTIME_BEHAVIOR_LOOP / LOCAL_RUNTIME_BEHAVIOR / RUNTIME_EVENT_IS_NOT_TRACE / NO_EXECUTION_BOUNDARY_ACTIVE / P3_FLOW_C_NEXT**

P3-FLOW-B gives AurelFlow reflexes: local runtime events with relations,
deterministic stream snapshots, mediated internal state commitments, workflow
pause with explicit reasons, operator decision signals, responsibility
transfer frames, failure classification with propagation risk, retry
eligibility, recovery proposals, rollback candidates, and a
RuntimeBehaviorReadModel over all of it. AurelFlow can record, pause,
explain, propose and mark candidates. AurelFlow still cannot execute:
execution belongs to P4 AurelExec, trace verification to P5 AurelTrace,
policy enforcement to P9 Custos. RuntimeEvent is not TraceEvent. Nothing is
LIVE and nothing is TRACE_VERIFIED.

## 2. Pack Scope

Covered roadmap ranges (Aurel Roadmap v5.5, P3 AurelFlow):

- P3.3.0–P3.3.20 — Runtime Event Stream
- P3.4.0–P3.4.20 — Approval Pause / Resume
- P3.5.0–P3.5.20 — Retry / Recovery / Rollback

Not covered (deliberately): P3.6 Flow State Projection, P3.7 Flow CLI/TUI
Binding, P3.8 Flow Docs/Reports, P3.9 Flow Exit Seal, P3.10–P3.12, P4
AurelExec, P5 AurelTrace, P6–P9, P10+, P15+, P21+.

## 3. Canon / Preflight

- Branch: `master`; initial `git status --short` clean; no unrelated dirty
  or untracked files.
- HEAD at start: `5e69137` (docs(agent): record P3-FLOW-A commit hash).
- P3-FLOW-A foundation present and reported:
  `src/agentic_runtime/aurel_flow/` (graph/state/scheduler/read model) and
  `agent/reports/P3_FLOW_A_AURELFLOW_RUNTIME_FOUNDATION_SUPERPACK.md`.
- Canon read: AGENT.md, CODEOPS.md (referenced), ACTIVE_TASK.md (P3-FLOW-A
  complete; P3-FLOW-B named next), ROADMAP.md (active canon table names
  P3-FLOW-B as next planned pack), STATE.md, ARCHITECTURE.md, DECISIONS.md,
  TESTS.md, REPORTS.md, latest reports (P3-FLOW-A).
- Standing operator override (recorded in P3-FLOW-A canon) remains in force:
  P3 proceeds by explicit operator decision; P2.11-D–P2.20 stay deferred
  until after full P3. No new conflict; no stop condition.
- `.venv/bin/python` present (Python 3.12.3).
- Canonical TraceEvent identified in `src/agentic_runtime/trace.py`
  (`TraceEvent = dict[str, Any]` appended to the hash-chained AurelTraceLog).
  RuntimeEvent is deliberately structurally distinct (frozen dataclass, no
  hash chain, no ledger backend) and `aurel_flow` behavior modules are
  test-forbidden from importing `agentic_runtime.trace`.

## 4. Roadmap Coverage Matrix

`agent/ROADMAP.md` does not enumerate granular P3.3.x/P3.4.x/P3.5.x
checkpoint names, so coverage is reported as capsule groups.

| Range | Capsule group | Status | Evidence | Tests | Truth labels |
|-------|---------------|--------|----------|-------|--------------|
| P3.3.0–P3.3.5 | RuntimeEvent contracts (kind/severity/source/payload) | DONE | `runtime_events.py` — `RuntimeEvent` (`runtime_event.v1`), 24 kinds, 6 severities, `RuntimeEventSource`, closed-world `RuntimeEventPayload` | `test_p3_flow_b_runtime_events.py` | LOCAL_RUNTIME_BEHAVIOR |
| P3.3.6–P3.3.10 | Event relations + append discipline | DONE | `RuntimeEventRelation` (parent/correlation/caused-by/affected nodes+runs), `append_runtime_event` fail-closed result (unknown refs, run mismatch, forbidden labels rejected), immutable streams | relation round-trip + rejection tests | LOCAL_RUNTIME_BEHAVIOR |
| P3.3.11–P3.3.15 | Deterministic stream snapshot + read model | DONE | `RuntimeEventStreamSnapshot` (`runtime_event_stream_snapshot.v1`, order-preserving, hash-stable), `RuntimeEventReadModel` | snapshot order/determinism + read-model tests | LOCAL_RUNTIME_BEHAVIOR |
| P3.3.16–P3.3.20 | RuntimeEvent-is-not-TraceEvent boundary | DONE | `RuntimeEventIsNotTraceBoundary` (all-false, fail-closed `__post_init__`); event/read-model `trace_verified`/`ledger_written`/`global_trace_written` permanently False; TRACE_VERIFIED/LIVE truth labels rejected | trace-boundary + forbidden-label tests | LOCAL_RUNTIME_BEHAVIOR + UNAVAILABLE (trace/ledger) |
| P3.4.0–P3.4.5 | Mediated internal state (MediatedActorOutput, RuntimeStateCommitment) | DONE | `state_commitment.py` — outputs cannot mutate shared state (`direct_state_mutation_allowed` fail-closed); commitments PROPOSED→COMMITTED_INTERNAL/REJECTED; `COMMITTED_INTERNAL` internal-only, `mutation_scope` locked to `INTERNAL_AUREL_FLOW` | `test_p3_flow_b_state_commitment.py` | LOCAL_RUNTIME_BEHAVIOR |
| P3.4.6–P3.4.10 | Workflow pause with explicit reasons | DONE | `pause_resume.py` — `WorkflowPauseState` (`workflow_pause_state.v1`), 11 pause reasons, pause via P3-FLOW-A safe lifecycle map (fails closed if unpausable) | pause tests incl. reason parametrization + fail-closed | LOCAL_RUNTIME_BEHAVIOR |
| P3.4.11–P3.4.15 | Operator decision signals + resume/stop/reject internal state | DONE | `OperatorDecisionSignal` (8 kinds, quality flags preserved, authority/execution booleans fail-closed); resume PAUSED→RUNNING, stop →CANCELLED, reject marks node BLOCKED — all internal, `node_executed=False` | signal/resume/stop/reject tests | LOCAL_RUNTIME_BEHAVIOR + UNAVAILABLE_AUTHORITY |
| P3.4.16–P3.4.20 | Responsibility transfer + pause read model | DONE | `ResponsibilityTransferFrame` (`authority_transferred`/`execution_permission_granted` fail-closed False), `WorkflowPauseReadModel` with authority/execution unavailable reasons | responsibility + pause read-model tests | LOCAL_RUNTIME_BEHAVIOR + UNAVAILABLE_AUTHORITY |
| P3.5.0–P3.5.5 | Failure classification + propagation risk | DONE | `recovery.py` — `FailureClassification` (9), `FailurePropagationRisk` (5), `classify_failure` derives LOCAL/DOWNSTREAM_NODES/WORKFLOW_BLOCKING from declarative graph reachability | classification/risk-variant tests | LOCAL_RUNTIME_BEHAVIOR |
| P3.5.6–P3.5.10 | Retry policy / eligibility / decision (no retry execution) | DONE | `RetryPolicy`, `calculate_retry_eligibility` (operator/policy failures never eligible; explicit reasons), `RetryDecision.retry_executed` fail-closed False, `blocked_by_missing_executor=True` | retry eligible/ineligible/decision tests | LOCAL_RUNTIME_BEHAVIOR + UNAVAILABLE_EXECUTION |
| P3.5.11–P3.5.15 | Recovery frame / proposal / steps (no recovery execution) | DONE | `RecoveryFrame`, `RecoveryProposal` (`recovery_proposal.v1`, `execution_available` fail-closed False, operator review + executor required), declarative `RecoveryStep` (`executable` fail-closed False) | recovery proposal tests | LOCAL_RUNTIME_BEHAVIOR + UNAVAILABLE_EXECUTION |
| P3.5.16–P3.5.20 | Rollback candidates + failure/recovery read model | DONE | `RollbackCandidate` (`safe_to_execute`/`execution_available` fail-closed False), `RollbackCandidateReason` (7), `FailureRecoveryReadModel` with retry/recovery/rollback-executed all False | rollback + read-model tests | LOCAL_RUNTIME_BEHAVIOR + UNAVAILABLE_EXECUTION |
| Cross-cutting | RuntimeBehaviorReadModel | DONE | `runtime_behavior_read_model.py` (`runtime_behavior_read_model.v1`) exposing all behavior state, truth labels, 8 UNAVAILABLE capability declarations, trace boundary, behavior no-execution proof, CLI-binding-unavailable reason | `test_p3_flow_b_behavior_read_model.py`, `test_p3_flow_b_no_execution_boundary.py` | LOCAL_RUNTIME_BEHAVIOR + UNAVAILABLE (execution/trace/ledger/authority/CLI) |

Rollup: **P3.3.0–P3.3.20 DONE. P3.4.0–P3.4.20 DONE. P3.5.0–P3.5.20 DONE.**
UNAVAILABLE items are deliberate boundary declarations only: execution (P4),
trace verification (P5), Ledger (P5), authority/enforcement (P9), event
projection/CLI binding (P3.6/P3.7), persistence (in-memory only, inherited
from P3-FLOW-A).

## 5. Checkpoint-by-checkpoint Status

See capsule matrix (Section 4). All capsule groups DONE with evidence and
mapped tests. UNAVAILABLE declarations with reasons: execution → P4
AurelExec; trace verification → P5 AurelTrace; Ledger → P5 AurelTrace
(`LEDGER_UNAVAILABLE_REASON`); authority → P9 Custos
(`AUTHORITY_UNAVAILABLE_REASON`); CLI/TUI binding → P3.7; event stream
projection → P3.6.

## 6. Implementation Summary

New modules under `src/agentic_runtime/aurel_flow/` (self-contained; no
imports from trace/policy/memory/sandbox/tools — test-enforced):

- `runtime_events.py` — RuntimeEvent/Kind/Severity/Source/Relation/Payload,
  immutable `RuntimeEventStream`, fail-closed `append_runtime_event` →
  `RuntimeEventAppendResult`, deterministic `snapshot_runtime_event_stream`,
  `build_runtime_event_read_model`, `RuntimeEventIsNotTraceBoundary`.
- `state_commitment.py` — `RuntimeSymbolState` (8), `MediatedActorOutput`,
  `RuntimeStateCommitment`, `RuntimeStateCommitmentResult`,
  `create_mediated_actor_output`, `create_runtime_state_commitment`,
  `commit_internal_runtime_state`.
- `pause_resume.py` — `WorkflowPauseReason` (11), `WorkflowPauseState`,
  `OperatorDecisionKind` (8), `OperatorDecisionSignal`,
  resume/stop/reject request+result pairs, `ResponsibilityTransferFrame`,
  `WorkflowPauseReadModel`, helpers `pause_workflow_run`,
  `create_operator_decision_signal`, `resume_workflow_run`,
  `stop_workflow_run`, `reject_workflow_path`,
  `create_responsibility_transfer_frame`,
  `build_workflow_pause_read_model`. All internal state changes go through
  the P3-FLOW-A safe transition maps.
- `recovery.py` — `FailureClassification` (9), `FailurePropagationRisk` (5),
  `FailureAssessment`, `RetryPolicy`/`RetryEligibility`/`RetryDecision`,
  `RecoveryFrame`/`RecoveryProposal`/`RecoveryStep`, `RollbackCandidate` +
  `RollbackCandidateReason` (7), `FailureRecoveryReadModel`, helpers
  `classify_failure`, `calculate_retry_eligibility`, `make_retry_decision`,
  `build_recovery_frame/proposal`, `build_rollback_candidate`,
  `build_failure_recovery_read_model`.
- `runtime_behavior_read_model.py` — `RuntimeBehaviorReadModel`,
  `RuntimeBehaviorNoExecutionProof` (P3-FLOW-A proof + 10 behavior
  negatives), `BEHAVIOR_UNAVAILABLE_CAPABILITIES` (8 entries),
  `build_runtime_behavior_read_model`,
  `serialize_runtime_behavior_read_model`.
- `demo.py` — added `run_runtime_behavior_demo()` (DEV_FIXTURE): full
  behavior loop, deterministic.
- `types.py` — added `LOCAL_RUNTIME_BEHAVIOR` truth label, P3-FLOW-B pack
  constants, `AUTHORITY_UNAVAILABLE_REASON`, `LEDGER_UNAVAILABLE_REASON`.
- `errors.py` — added 9 behavior error codes (UNKNOWN_EVENT_REF,
  RUN_MISMATCH, FORBIDDEN_TRUTH_LABEL, FORBIDDEN_BOUNDARY_CLAIM,
  DIRECT_STATE_MUTATION_FORBIDDEN, INVALID_COMMITMENT_STATUS,
  SIGNAL_KIND_MISMATCH, NOT_RESUMABLE, EMPTY_ACTOR_ID).
- `__init__.py` — public exports extended.

## 7. Runtime Event Stream Proof

Events append deterministically (same inputs → same event_id/hash); streams
are immutable (rejected appends leave the stream unchanged and carry an
explicit reject code); snapshots preserve order and are hash-stable;
relations round-trip parent_event_id, correlation_id, caused_by_event_id,
affected_node_ids and affected_run_ids; unknown parent/caused-by refs and
run mismatches are rejected closed-world.

## 8. RuntimeEvent-is-not-TraceEvent Proof

- Canonical TraceEvent is a dict appended to the hash-chained AurelTraceLog;
  RuntimeEvent is a frozen local dataclass — asserted structurally in tests.
- `RuntimeEventIsNotTraceBoundary` is all-false and fail-closed; attached to
  every stream, snapshot, read model, and the behavior read model.
- `trace_verified`, `ledger_written`, `global_trace_written` are permanently
  False on events and read models; constructing an event with any of them
  True raises `FORBIDDEN_BOUNDARY_CLAIM`.
- Appending with truth label TRACE_VERIFIED or LIVE is rejected
  (`FORBIDDEN_TRUTH_LABEL`).
- Behavior modules are test-forbidden from importing `agentic_runtime.trace`.

## 9. Mediated State Commitment Proof

`MediatedActorOutput.direct_state_mutation_allowed` is permanently False
(fail-closed). Internal state changes only occur via
`create_runtime_state_commitment` → `commit_internal_runtime_state`;
COMMITTED_INTERNAL sets `state_mutated=True` with `mutation_scope` locked to
`INTERNAL_AUREL_FLOW`; rejected validation and already-terminal commitments
are refused with explicit reasons; `authority_granted`, `ledger_written`,
`external_side_effect` are fail-closed False.

## 10. Pause / Resume / Operator Signal Proof

Pause uses the P3-FLOW-A safe lifecycle map (RUNNING/WAITING→PAUSED) with an
explicit `WorkflowPauseReason`; unpausable lifecycles fail closed. Resume
(PAUSED→RUNNING), stop (→CANCELLED) and reject (node→BLOCKED) are internal
state changes that require a matching-kind, matching-run operator signal and
never execute a node (`node_executed=False`, node states unchanged on
resume). Non-resumable pauses fail closed. Decision quality flags
(counterargument, minority objection, mediation, decision pressure)
round-trip.

## 11. Responsibility Transfer-is-not-Authority Proof

`ResponsibilityTransferFrame.authority_transferred` and
`.execution_permission_granted` are permanently False and fail-closed;
`OperatorDecisionSignal.authority_granted` and
`.execution_permission_granted` likewise. The pause read model exposes
`authority_available=False` with `AUTHORITY_UNAVAILABLE_REASON` naming P9
Custos as the authority home.

## 12. Retry / Recovery / Rollback Candidate Proof

Retry eligibility is calculated, never executed: OPERATOR_REJECTED and
POLICY_BLOCKED failures are never eligible ("not retried away"); exhausted
attempts and uncovered classifications are ineligible with explicit reasons;
`blocked_by_missing_executor=True` and `execution_available=False` always.
Recovery proposals carry declarative, non-executable steps requiring an
executor and operator review. Rollback candidates have `safe_to_execute` and
`execution_available` fail-closed False. Failure propagation risk is derived
from graph reachability (LOCAL / DOWNSTREAM_NODES / WORKFLOW_BLOCKING /
SYSTEMIC / UNKNOWN) and is visible on assessments, eligibilities and read
models.

## 13. No-Execution Boundary Proof

- Source-scan test over all behavior modules: no subprocess/socket/requests/
  urllib/httpx/asyncio imports, no os.system/exec/spawn/popen/eval/exec, and
  no imports of agentic_runtime trace/memory/policy/sandbox/tools modules.
- The P3-FLOW-A no-execution source scan (all `aurel_flow/*.py`) also passes
  over the new modules.
- `RuntimeBehaviorNoExecutionProof` all-false: foundation proof (18 fields)
  plus retry/recovery/rollback executed, resume/pause executed node,
  operator-signal authority, responsibility authority, event trace/ledger
  writes, commitment ledger write.
- Behavior helpers never mutate input runs (asserted); all boundary booleans
  across all objects are fail-closed at construction.

## 14. Runtime Behavior Read Model

`RuntimeBehaviorReadModel` (`runtime_behavior_read_model.v1`) exposes:
events count + relations + stream snapshot, mediated outputs, state
commitments, pause states, operator signals, responsibility frames, retry
eligibilities, recovery proposals, rollback candidates, failure
classifications and propagation risks, advisory predictability labels, truth
labels, 8 unavailable capability declarations (execution, trace
verification, CLI binding, event-stream projection, approval runtime,
persistence, authority, ledger), trace boundary, behavior no-execution
proof, CLI-binding-unavailable reason, and top-level
`execution_available=False`, `trace_verified=False`, `ledger_written=False`,
`global_trace_written=False`. Deterministic JSON export via
`serialize_runtime_behavior_read_model`.

## 15. Truth Labels

- LIVE: not used (rejected by event append; test-enforced).
- TRACE_VERIFIED: not used (rejected by event append; test-enforced).
- SIMULATED: not used.
- DEV_FIXTURE: behavior demo objects in `demo.py` only.
- UNAVAILABLE: execution, trace verification, ledger, authority, CLI
  binding, event projection, approval runtime, persistence — each with an
  explicit reason.
- ERROR: vocabulary only, no truth claim.
- Additional labels used: LOCAL_RUNTIME_BEHAVIOR (all behavior objects),
  UNAVAILABLE_AUTHORITY, UNAVAILABLE_LEDGER (capability entries), plus the
  P3-FLOW-A labels unchanged.

## 16. Tests / Validation

Focused tests added (53 total):

- `tests/test_p3_flow_b_runtime_events.py` — 9 tests
- `tests/test_p3_flow_b_state_commitment.py` — 7 tests
- `tests/test_p3_flow_b_pause_resume.py` — 15 tests
- `tests/test_p3_flow_b_retry_recovery.py` — 9 tests
- `tests/test_p3_flow_b_no_execution_boundary.py` — 6 tests
- `tests/test_p3_flow_b_behavior_read_model.py` — 7 tests

Validation run (all through `.venv/bin/python`):

- `compileall src tests` — **PASS**
- P3-FLOW-B focused tests — **53 passed**
- P3-FLOW-A regression (all 5 files) — **50 passed**
- `ruff check src tests` — **PASS**
- `mypy src/agentic_runtime` — **PASS** (367 source files)
- Canon-gate regression subset after canon edits — recorded below in the
  final response (run post-canon-update).

Not run (honest): full pytest suite, coverage, Bandit, core strict mypy
probe. No full-suite PASS and no coverage claim is made.

## 17. Files Created / Modified

Created:

- `src/agentic_runtime/aurel_flow/runtime_events.py`
- `src/agentic_runtime/aurel_flow/state_commitment.py`
- `src/agentic_runtime/aurel_flow/pause_resume.py`
- `src/agentic_runtime/aurel_flow/recovery.py`
- `src/agentic_runtime/aurel_flow/runtime_behavior_read_model.py`
- `tests/test_p3_flow_b_runtime_events.py`
- `tests/test_p3_flow_b_state_commitment.py`
- `tests/test_p3_flow_b_pause_resume.py`
- `tests/test_p3_flow_b_retry_recovery.py`
- `tests/test_p3_flow_b_no_execution_boundary.py`
- `tests/test_p3_flow_b_behavior_read_model.py`
- `agent/reports/P3_FLOW_B_RUNTIME_BEHAVIOR_LOOP_PACK.md`

Modified:

- `src/agentic_runtime/aurel_flow/types.py` (behavior label + reasons + pack constants)
- `src/agentic_runtime/aurel_flow/errors.py` (behavior error codes)
- `src/agentic_runtime/aurel_flow/demo.py` (behavior loop demo)
- `src/agentic_runtime/aurel_flow/__init__.py` (exports)
- `agent/REPORTS.md`, `agent/STATE.md`, `agent/ACTIVE_TASK.md`,
  `agent/ROADMAP.md`, `agent/ARCHITECTURE.md`, `agent/DECISIONS.md`,
  `agent/TESTS.md`

## 18. What Was Deliberately Not Implemented

- P3.6 Flow State Projection; P3.7 Flow CLI/TUI binding; P3.8 Flow
  Docs/Reports; P3.9 Flow Exit Seal; P3.10–P3.12.
- P4 AurelExec (no retry/recovery/rollback/resume execution — candidates and
  internal state only); P5 AurelTrace (RuntimeEvent is not TraceEvent; no
  Ledger, no global Trace, no TRACE_VERIFIED); P9 Custos (signals and frames
  grant no authority).
- Event-sourced replay engine, formal verifier, worker registry, agent
  dispatch, memory/policy/identity mutation, product UI, external
  persistence.

## 19. Remaining Risks

- Runtime event: streams are per-run and in-memory; cross-run correlation is
  advisory via relation fields only.
- State commitment: symbol/state refs are opaque strings; a future object
  plane (P6) must bind them to real objects.
- Pause/resume: pause states are records beside the run, not embedded in the
  run contract; P3.6 projection must join them by run_id.
- Retry/recovery: eligibility policy is deliberately simple (attempt count +
  classification); cooldown is a label, not a timer (no clocks in this pack).
- Rollback candidate: `safe_to_prepare` is caller-asserted, not verified.
- Trace verification / execution: UNAVAILABLE by design; future packs must
  flip labels honestly when implementing.
- Next pack risk: P3-FLOW-C (projection/CLI/docs/seal) must project this
  behavior truth without turning read models into execution or claiming
  LIVE.

## 20. Next Pack

**P3-FLOW-C — Flow State Projection / CLI-TUI / Docs / P3.9 Seal.** After
full P3: resume the deferred P2 tail (P2.11-D → P2.20).

## 21. Commit Hash

Implementation commit: recorded in the follow-up docs commit per repo
convention (`feat(flow): add P3-FLOW-B runtime behavior loop`).

## 22. Final Git Status

Clean after commit (only in-scope files staged and committed; no push; no
branch created).
