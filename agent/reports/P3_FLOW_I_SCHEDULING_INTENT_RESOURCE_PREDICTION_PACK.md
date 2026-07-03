# P3-FLOW-I — Workflow-Atomic Scheduling Intent / Resource Prediction Pack

## 1. Result Header

**Status: DONE — SCHEDULING_INTENT_IS_NOT_DISPATCH / ATOMIC_UNIT_IS_NOT_WORKER_JOB / READY_IS_NOT_DISPATCHABLE / PREDICTION_IS_NOT_ALLOCATION / ESTIMATE_IS_NOT_BILLING / QUEUE_CANDIDATE_IS_NOT_QUEUE_INSERTION / CONCURRENCY_WINDOW_IS_NOT_WORKER_SPAWN / REQUIREMENT_IS_NOT_INVOCATION / AUTONOMY_GATED_SCHEDULING_IS_NOT_AUTHORITY / REACT_PROJECTION_ONLY / NO_DISPATCH / NO_EXECUTION / NO_RESOURCE_ALLOCATION / P3_FLOW_J_NEXT**

Date: 2026-07-03
Roadmap: Aurel Roadmap v5.5 — P3.17.0–P3.17.30 (Workflow-Atomic Scheduling Intent / Resource Prediction)
Commit: `feat(flow): add P3-FLOW-I scheduling intent` (hash recorded in section 26)

## 2. Pack Scope

P3-FLOW-I adds the AurelFlow scheduling-intent boundary layer: workflow-atomic
scheduling units, candidate-only scheduling intent, the ready-vs-dispatchable
boundary with explicit why-not-dispatchable reasons, resource prediction and
advisory cost/latency/token/context estimates, queue placement candidates,
dependency/concurrency windows, model/tool/sandbox/data requirement frames,
autonomy-gated scheduling decisions consuming the P3-FLOW-H boundaries, and
React-safe scheduling projection envelopes. Nothing dispatches, enqueues,
allocates, reserves, spawns, invokes, bills, consumes, proves, or authorizes.

New modules:

- `src/agentic_runtime/aurel_flow/flow_scheduling_intent.py`
- `src/agentic_runtime/aurel_flow/flow_dispatchability.py`
- `src/agentic_runtime/aurel_flow/flow_resource_prediction.py`
- `src/agentic_runtime/aurel_flow/flow_scheduling_projection.py`

## 3. Canon / Preflight

- Branch `master`, clean worktree at start; no unrelated dirty/untracked files.
- Read: `agent/AGENT.md` canon set, `agent/ACTIVE_TASK.md`, `agent/STATE.md`,
  `agent/ROADMAP.md`, `agent/TESTS.md`, `agent/REPORTS.md`, `agent/DECISIONS.md`,
  `agent/ARCHITECTURE.md`, the P3-FLOW-H report, and the H source modules.
- Name-collision scan for all dispatched class names over `src`/`tests`: zero hits.
- No canon conflict found; `ACTIVE_TASK.md` and `ROADMAP.md` both pointed at
  P3-FLOW-I as the next pack.

## 4. P3-FLOW-H prerequisite confirmation

CONFIRMED. `flow_autonomy.py`, `flow_autonomy_scope.py`, `flow_autonomy_gates.py`,
`flow_autonomy_projection.py` present; commit `f1080cf feat(flow): add P3-FLOW-H
governed autonomy scope`; report `agent/reports/P3_FLOW_H_GOVERNED_AUTONOMY_SCOPE_PACK.md`
present and indexed; all 7 H test files re-run green in this session. The I gate
layer consumes H truth via `resolve_action_boundary` and `AutonomyScopeEnvelope`
directly — it never re-derives permission rules.

## 5. Roadmap Coverage Matrix

| Range | Contract | Status |
|-------|----------|--------|
| P3.17.0–P3.17.4 | WorkflowAtomicUnit / Ref / Boundary / ReadModel | DONE |
| P3.17.5–P3.17.9 | SchedulingIntent family + ReadyStateFrame / DispatchabilityFrame family | DONE |
| P3.17.10–P3.17.14 | ResourcePredictionFrame family + Cost/Latency/Token/Context estimates + SchedulingEstimateReadModel | DONE |
| P3.17.15–P3.17.19 | QueuePlacementCandidate family + Dependency/Concurrency windows + ParallelismCandidate | DONE |
| P3.17.20–P3.17.24 | Model/Tool/Sandbox/DataAccess requirement frames + ExecutionResourceRequirementReadModel | DONE |
| P3.17.25–P3.17.30 | AutonomySchedulingGate family + SchedulingProjectionEnvelope + view models + boundary proofs | DONE |

## 6. P3.17.0–P3.17.4 Workflow-Atomic Scheduling Unit status

DONE. `WorkflowAtomicUnitKind` is closed-world (SINGLE_NODE, NODE_GROUP,
RECOVERY_CANDIDATE_GROUP, GRAPH_REVISION_CANDIDATE_GROUP,
CHECKPOINT_BOUND_REPLAY_CANDIDATE, OPERATOR_REVIEW_WAITING_UNIT,
VERIFIER_CANDIDATE_UNIT, FALLBACK_PATH_CANDIDATE_UNIT, UNAVAILABLE, ERROR) with
no WORKER_JOB/EXECUTABLE member. `WorkflowAtomicUnit` carries run/workflow/node
lineage plus source event/checkpoint/recovery/replay/graph-revision ids;
`candidate_only` is fail-closed True and `worker_job`/`execution_available`/
`dispatch_available` are fail-closed False; a unit cannot depend on itself and
must cover at least one node (except UNAVAILABLE/ERROR). Ref, boundary, and
read model are deterministic (`stable_hash` ids) with run-lineage validation.

## 7. P3.17.5–P3.17.9 Scheduling Intent / Ready vs Dispatchable status

DONE. `SchedulingIntentKind` (12 members incl. HOLD/BLOCK/UNAVAILABLE/ERROR, no
dispatch verb) and `SchedulingIntentReason` are closed-world; `SchedulingIntent`
is candidate-only with `requires_p4_dispatch` fail-closed True and
`queued`/`dispatched`/`execution_available` fail-closed False; HOLD/BLOCK/
OPERATOR_REVIEW intents force `requires_operator_review`. `ReadyStateFrame`
covers seven P3-representable readiness dimensions while `policy_ready`,
`proof_ready`, and `execution_ready` are structurally False (`ReadinessDimension`
carries POLICY/PROOF/EXECUTION_READY_UNAVAILABLE members). `classify_dispatchability`
is a deterministic total classifier: every blocking dimension maps to its own
`DispatchabilityReason`, retry-storm/no-progress guards outrank readiness, and a
fully ready unit resolves to `dispatchable_candidate=True` with reason
READY_BUT_NO_P4 and `dispatch_available`/`dispatched` still False — ready is not
dispatchable and a dispatchable candidate is not dispatched.

## 8. P3.17.10–P3.17.14 Resource Prediction / Estimates status

DONE. `ResourceDimension` covers the 16 dispatched dimensions.
`ResourceRequirementEstimate`, `ResourcePressureSignal`,
`ResourceAvailabilityBoundary`, `ResourcePredictionFrame`, and
`ResourcePredictionReadModel` keep `resource_allocated`/`resource_reserved`/
`measured_usage`/`permission_granted` fail-closed False; frame construction
validates unit lineage and derives pressure deterministically.
`EstimateConfidence` is closed-world with no MEASURED/PROVEN/VERIFIED/CERTAIN
member. `CostEstimate`/`LatencyEstimate`/`TokenBudgetEstimate`/
`ContextWindowEstimate` share an advisory base where `billing_performed`/
`tokens_consumed`/`measured_usage`/`proof_available` are fail-closed False and
`exceeds_budget=True` structurally forces operator review; latency is logical
steps, never wall clock. `SchedulingEstimateReadModel` rolls up budget pressure.

## 9. P3.17.15–P3.17.19 Queue Candidate / Dependency / Concurrency status

DONE. `QueuePlacementKind` matches the dispatched 12-member vocabulary;
`derive_queue_placement_candidate` is a total deterministic mapping over all 14
`DispatchabilityReason` members (totality is tested). `QueuePlacementCandidate`
keeps `queue_candidate_only` fail-closed True and `actual_queue_inserted`/
`worker_assigned`/`dispatch_available`/`execution_available` fail-closed False.
`DependencyWindow` orders candidates without being an execution order;
`ConcurrencyWindow` separates safe/unsafe parallel sets (overlap and unknown
unit ids are unconstructible) with shared-resource constraints and
operator-ordering flags; `ParallelismCandidate` requires two or more units and
keeps `worker_spawned`/`parallel_execution_available` fail-closed False.
Boundary and read model aggregate deterministically with run validation.

## 10. P3.17.20–P3.17.24 Model / Tool / Sandbox / Data Requirements status

DONE. `ModelRequirementFrame` (model_invoked, tokens_consumed False),
`ToolRequirementFrame` (tool_invoked False), `SandboxRequirementFrame`
(sandbox_executed, subprocess_spawned False), `DataAccessRequirementFrame`
(data_access_performed, network_called, memory_access_performed False) — all
with `requires_p4_execution` and `requires_p9_authority` fail-closed True.
`ExecutionResourceRequirementReadModel` aggregates presence per unit with the
same fail-closed invocation booleans. A requirement is never an invocation.

## 11. P3.17.25–P3.17.30 Autonomy-Gated Scheduling / Projection status

DONE. `SchedulingScopeCheck` fails closed to outside-scope with no envelope and
never authorizes; `SchedulingActionBoundaryCheck` wraps the H
`resolve_action_boundary` output verbatim; `evaluate_autonomy_scheduling_gate`
is a deterministic ladder (forbidden-in-P3 → BLOCK_SCHEDULING, P9-bound →
REQUIRE_P9_AUTHORITY, outside scope → HOLD_SCHEDULING, review-bound →
REQUIRE_OPERATOR_REVIEW, else ALLOW_SCHEDULING_CANDIDATE) that can never
out-allow H; `SchedulingAutonomyDecision` has no DISPATCH/EXECUTE/APPROVE/
AUTHORIZE member; the gate keeps `gate_is_not_authority`/`gate_is_not_dispatch`/
`requires_p4_execution` fail-closed True and authority/permission/execution/
dispatch booleans fail-closed False. `SchedulingProjectionEnvelope` plus
timeline/intent/resource/dispatchability/queue/concurrency view models and
`SchedulingReactProjectionBoundary` all keep `react_projection_only` True and
the six UI-powerlessness booleans (`frontend_mutation_allowed`,
`ui_schedule_action_allowed`, `ui_queue_action_allowed`, `ui_dispatch_allowed`,
`api_server_implemented`, `frontend_implemented`) fail-closed False, with
`runtime_source_of_truth == "python"` enforced.

## 12. Workflow Atomic Unit Proof

Deterministic (`create_workflow_atomic_unit` twice → identical ids); not a
worker job and does not execute (constructing with `worker_job=True`,
`execution_available=True`, `dispatch_available=True`, or
`candidate_only=False` raises `AurelFlowValidationError`); self-dependency and
empty node sets are unconstructible. Tests: `test_p3_flow_i_scheduling_intent.py`.

## 13. Scheduling Intent Proof

Deterministic; does not enqueue and does not dispatch (`queued`, `dispatched`,
`execution_available` unconstructible True; `requires_p4_dispatch`
unconstructible False); kind vocabulary carries no dispatch verb; HOLD/BLOCK
require operator review. Tests: `test_p3_flow_i_scheduling_intent.py`.

## 14. Ready vs Dispatchable Boundary Proof

A ready frame cannot claim policy/proof/execution readiness; a fully ready unit
classifies as candidate-only READY_BUT_NO_P4 with `dispatch_available=False`;
each blocking dimension yields its own explanatory reason; guard signals
outrank readiness. Tests: `test_p3_flow_i_dispatchability.py`.

## 15. Resource Prediction / Estimate Proof

Prediction frames and estimates are deterministic and read-only; allocation,
reservation, measurement, permission, billing, and token-consumption booleans
are unconstructible True; confidence has no measured/proven member;
budget-exceeding estimates structurally require operator review. Tests:
`test_p3_flow_i_resource_prediction.py`, `test_p3_flow_i_no_resource_allocation.py`.

## 16. Queue Candidate / Concurrency Proof

Queue mapping is total over dispatchability reasons; a queue candidate never
inserts into a queue or assigns a worker (unconstructible); dependency and
concurrency windows are deterministic; a parallelism candidate never spawns a
worker (unconstructible). Tests: `test_p3_flow_i_queue_concurrency.py`.

## 17. Requirement Frame Proof

Model/tool/sandbox/data requirements never invoke, call, execute, or access
(all invocation booleans unconstructible True; P4/P9 requirements
unconstructible False). Tests: `test_p3_flow_i_requirements.py`.

## 18. Autonomy-Gated Scheduling Proof

The gate consumes H resolver truth; H-forbidden classes (tool execution,
network call, memory write, external side effect) always BLOCK_SCHEDULING with
`forbidden_in_p3=True`; missing scope envelope fails closed to HOLD; authority
requests route to REQUIRE_P9_AUTHORITY; low tiers require operator review; the
gate grants nothing (authority/permission/execution/dispatch unconstructible
True). Tests: `test_p3_flow_i_no_dispatch_boundary.py`.

## 19. Projection / React Readiness Proof

Every view model, the envelope, and the React boundary preserve UI
powerlessness structurally (all six UI booleans unconstructible True;
`react_projection_only`/`read_only` unconstructible False); Python is the
enforced source of truth; view models mirror source truth without re-deriving
it; foreign-run views are rejected. Tests: `test_p3_flow_i_projection.py`.

## 20. No-Dispatch / No-Execution / No-Resource-Allocation Proof

`NoDispatchBoundaryProof`, `NoExecutionBoundaryProof`, and
`NoResourceAllocationProof` are all-false fail-closed contracts explicitly
marked `is_p5_trace_proof=False` (report evidence, not runtime proof). Source
scans over the four I modules verify: no subprocess/socket/requests/urllib/
httpx/asyncio/sqlite3/pickle imports, no os.system/exec/spawn/fork, no
eval/exec/open, no `.submit(`, no AgenticRuntime/ApprovalGate/TraceLedger, no
trace/memory/policy/sandbox/tools/runtime imports, no queue.Queue/threading/
multiprocessing/concurrent.futures, no React/FastAPI/Flask/Django/WebSocket
machinery, no FlowTruthLabel.LIVE/TRACE_VERIFIED assignment, and zero
lint/type suppressions. AST scan confirms only `__future__`/`dataclasses`/
`enum`/`typing` absolute imports. Tests: `test_p3_flow_i_no_dispatch_boundary.py`,
`test_p3_flow_i_no_execution_boundary.py`, `test_p3_flow_i_no_resource_allocation.py`.

## 21. Tests / Validation

Focused (2026-07-03, all PASS):

- `test_p3_flow_i_scheduling_intent.py` — 13 passed
- `test_p3_flow_i_dispatchability.py` — 9 passed
- `test_p3_flow_i_resource_prediction.py` — 9 passed
- `test_p3_flow_i_queue_concurrency.py` — 10 passed
- `test_p3_flow_i_requirements.py` — 8 passed
- `test_p3_flow_i_projection.py` — 6 passed
- `test_p3_flow_i_no_dispatch_boundary.py` — 10 passed
- `test_p3_flow_i_no_execution_boundary.py` — 6 passed
- `test_p3_flow_i_no_resource_allocation.py` — 8 passed
- **Total: 79 passed**

Regression (the exact dispatched A–H command sets, batched): A+B 89 passed;
C+D 107 passed; E+F 134 passed; G+H 153 passed — **483 regression tests passed**.

Toolchain: `compileall src tests` PASS; `ruff check src tests` "All checks
passed!"; `mypy src/agentic_runtime` "Success: no issues found in 398 source
files". Full pytest suite / coverage / Bandit NOT run (no runtime/security/
sandbox/network/subprocess path touched; lean doctrine applies).

## 22. Files Created / Modified

Created:

- `src/agentic_runtime/aurel_flow/flow_scheduling_intent.py`
- `src/agentic_runtime/aurel_flow/flow_dispatchability.py`
- `src/agentic_runtime/aurel_flow/flow_resource_prediction.py`
- `src/agentic_runtime/aurel_flow/flow_scheduling_projection.py`
- `tests/test_p3_flow_i_scheduling_intent.py`
- `tests/test_p3_flow_i_dispatchability.py`
- `tests/test_p3_flow_i_resource_prediction.py`
- `tests/test_p3_flow_i_queue_concurrency.py`
- `tests/test_p3_flow_i_requirements.py`
- `tests/test_p3_flow_i_projection.py`
- `tests/test_p3_flow_i_no_dispatch_boundary.py`
- `tests/test_p3_flow_i_no_execution_boundary.py`
- `tests/test_p3_flow_i_no_resource_allocation.py`
- `agent/reports/P3_FLOW_I_SCHEDULING_INTENT_RESOURCE_PREDICTION_PACK.md`

Modified:

- `src/agentic_runtime/aurel_flow/__init__.py` (I-pack exports)
- `agent/REPORTS.md`, `agent/STATE.md`, `agent/ACTIVE_TASK.md`,
  `agent/ROADMAP.md`, `agent/ARCHITECTURE.md`, `agent/DECISIONS.md`,
  `agent/TESTS.md`

## 23. What Was Deliberately Not Implemented

P3.18 compound runtime topology; P3.19 harness evaluation; P3.20 extended
seal; P4 dispatch/execution/worker allocation; P5 trace/proof; P9 Custos
authority; runtime.submit bridge; actual dispatch, queue insertion, worker
allocation/spawn, resource allocation/reservation, cost billing, token
consumption; model/tool/sandbox/network/subprocess execution; data access;
Trace/Ledger writes; memory/policy/identity mutation; CLI control commands;
React components/routes/frontend state; AurelShell UI; API server; REST;
WebSocket; persistence; migration.

## 24. Remaining Risks

- Ready-state inputs are declared, not derived from the A-pack scheduler; a
  future pack may want a bridge from `ReadyQueue` truth to `ReadyStateFrame`.
- Estimates carry magnitudes but no calibration source; P3-FLOW-K harness
  evaluation should score estimate quality.
- The gate's decision-class input is chosen by the caller; misclassifying a
  side-effecting action as PREPARE_PLAN would soften gating in P3 (it still
  cannot execute anything — the boundary matrix and P4 absence hold).
- `_AdvisoryEstimateBase` and `_ReactViewModelBase` are shared bases; future
  packs must not add mutable authority fields to them.

## 25. Next Pack: P3-FLOW-J

Compound Runtime Topology / Model-Agent-Environment Services Pack (P3.18) —
scheduling intent across model, agent, tool, memory, verifier, and environment
service boundaries.

## 26. Commit Hash

Recorded post-commit in `git log`: commit message
`feat(flow): add P3-FLOW-I scheduling intent`. (Hash appears in the final run
report and the follow-up canon commit, per repo convention.)

## 27. Final Git Status

Clean after commit (verified in the run's final `git status --short`).
