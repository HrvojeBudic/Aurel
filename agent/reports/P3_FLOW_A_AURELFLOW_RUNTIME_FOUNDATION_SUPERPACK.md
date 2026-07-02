# P3-FLOW-A — AurelFlow Runtime Foundation Superpack

## 1. Result Header

**DONE — AURELFLOW_RUNTIME_FOUNDATION / LOCAL_RUNTIME_SUBSTRATE / NO_EXECUTION_BOUNDARY_ACTIVE / OPERATOR_OVERRIDE_RECORDED / P3_FLOW_B_NEXT**

P3-FLOW-A implements the first real AurelFlow runtime substrate under
`src/agentic_runtime/aurel_flow/`: workflow graph → workflow run → durable
lifecycle state → node state → ready queue → scheduler decision →
operator-testable runtime read model. The scheduler decides readiness and
never executes. Execution remains UNAVAILABLE and belongs to P4 AurelExec.
Nothing here is LIVE and nothing is TRACE_VERIFIED.

## 2. Pack Scope

Covered roadmap ranges (Aurel Roadmap v5.5, P3 AurelFlow):

- P3.0.0–P3.0.20 — Workflow Graph Foundation
- P3.1.0–P3.1.20 — Durable State / Workflow Lifecycle
- P3.2.0–P3.2.20 — Scheduler / Ready Queue

Not covered (deliberately): P3.3 Runtime Event Stream, P3.4 Approval
Pause/Resume runtime, P3.5 Retry/Recovery/Rollback runtime, P3.6 Flow State
Projection full pack, P3.7 Flow CLI/TUI Binding, P3.8 Flow Docs/Reports,
P3.9 Flow Exit Seal, P3.10–P3.12, P4 AurelExec, P5 AurelTrace, P9 Custos,
P10+ cognition layers.

## 3. Canon / Preflight

**Operator override (recorded honestly):** At dispatch time repo canon
pointed to unfinished P2 work (P2.11-C complete, P2.11-D next, P2.12–P2.20
NOT_STARTED, explicit "no P3 handoff claim" in ACTIVE_TASK/STATE). Per the
P3-FLOW-A stop conditions the run was STOPPED and the blocker reported. The
operator then explicitly overrode: *"override - start p3-Flow-A now,
p2.11D-p2.20 will contiune after full p3"*. P3 is therefore opened by
explicit operator decision, **not** by a P2 completion seal. P2 remains
PARTIAL / not sealed: P2.11-D through P2.20 (including the P2.20 Final
Seven-Surface Exit Seal) are deferred until after full P3. No P2-complete
claim and no organic P3-handoff claim is made.

Preflight facts:

- Branch: `master`; initial `git status --short` clean; no unrelated dirty or
  untracked files.
- HEAD at start: `9ff802d` (docs(agent): record P2.11-C commit hash).
- Canon read: `agent/AGENT.md`, `agent/CODEOPS.md` (referenced),
  `agent/ACTIVE_TASK.md`, `agent/ROADMAP.md`, `agent/STATE.md`,
  `agent/ARCHITECTURE.md`, `agent/DECISIONS.md`, `agent/TESTS.md`,
  `agent/REPORTS.md`, latest `agent/reports/` (P2.11-A/B/C era).
- No existing `aurel_flow` module, no conflicting Workflow/Scheduler runtime
  implementation found (`aurel_shell` workflow references are contract-only
  Shell projections and were not touched).
- `.venv/bin/python` present (Python 3.12.3); pytest/ruff/mypy available.
- Canon conflict found and resolved by operator override (above). Secondary
  observation: the `agent/ROADMAP.md` "Active roadmap canon" table was stale
  (still saying "Last completed pack: P2.9-B-R1") relative to
  ACTIVE_TASK/STATE/git truth (P2.11-C); updated as part of this pack's canon
  sync.

## 4. Roadmap Coverage Matrix

`agent/ROADMAP.md` does not enumerate granular P3.0.x/P3.1.x/P3.2.x
checkpoint names, so coverage is reported as capsule groups per the pack
contract.

| Range | Capsule group | Status | Evidence | Tests | Truth labels |
|-------|---------------|--------|----------|-------|--------------|
| P3.0.0–P3.0.5 | Graph contracts (WorkflowNode, WorkflowEdge, WorkflowGraph, WorkflowGraphSpec) | DONE | `aurel_flow/workflow_graph.py` (`workflow_graph.v1`, `workflow_graph_spec.v1`) | `test_p3_flow_a_workflow_graph.py` | LOCAL_RUNTIME_SUBSTRATE |
| P3.0.6–P3.0.10 | Closed-world graph validation, fail-closed | DONE | `validate_workflow_graph` — duplicates, unknown refs, unsupported types, entry/exit, cycles, reachability, approval-flag mismatch | duplicate/unknown/type/entry-exit/cycle/unreachable/approval tests (13 tests) | LOCAL_RUNTIME_SUBSTRATE |
| P3.0.11–P3.0.15 | Deterministic serialization / stable graph hash | DONE | `types.py` canonical JSON + sha256 `stable_hash`; `graph_hash` | `test_graph_serialization_and_hash_are_deterministic` | LOCAL_RUNTIME_SUBSTRATE |
| P3.0.16–P3.0.20 | Graph read model / definition-not-permission boundary | DONE | `WorkflowGraphReadModel` (`workflow_graph_read_model.v1`), `graph_is_definition_not_permission`, `graph_executes_nothing` | graph read-model tests | LOCAL_RUNTIME_SUBSTRATE |
| P3.1.0–P3.1.5 | Workflow run creation from valid graph; deterministic run identity | DONE | `create_workflow_run` fail-closed on invalid graph; run_id = sha256(graph_hash + run_key) | `test_p3_flow_a_workflow_state.py` creation/determinism tests | LOCAL_RUNTIME_SUBSTRATE |
| P3.1.6–P3.1.10 | Lifecycle statuses + safe transitions + terminal protection | DONE | `WorkflowLifecycleStatus` (10 values), `ALLOWED_LIFECYCLE_TRANSITIONS`, terminal COMPLETED/FAILED/CANCELLED/UNAVAILABLE/ERROR | lifecycle pass/fail/terminal/stale tests | LOCAL_RUNTIME_SUBSTRATE |
| P3.1.11–P3.1.15 | Node states + safe node transitions + immutable transition history | DONE | `WorkflowNodeState` (11 values), `ALLOWED_NODE_TRANSITIONS`, immutable `WorkflowRun` + appended history | node transition/immutability/terminal tests | LOCAL_RUNTIME_SUBSTRATE |
| P3.1.16–P3.1.20 | Deterministic state snapshots + durability honesty | DONE (persistence itself UNAVAILABLE) | `WorkflowStateSnapshot` (`workflow_state_snapshot.v1`), `persisted=False`, `UNAVAILABLE_PERSISTENCE` label + reason | snapshot determinism + persistence-honesty tests | LOCAL_RUNTIME_SUBSTRATE + UNAVAILABLE_PERSISTENCE |
| P3.2.0–P3.2.5 | Ready queue calculation from graph + run state | DONE | `calculate_ready_queue` (`ready_queue.v1`), `SchedulableNode.is_execution_grant=False` | `test_p3_flow_a_scheduler_ready_queue.py` queue tests | LOCAL_RUNTIME_SUBSTRATE |
| P3.2.6–P3.2.10 | Scheduler decision with explicit reasons | DONE | `make_scheduler_decision` (`scheduler_decision.v1`); reasons READY / WAITING_DEPENDENCY / WAITING_APPROVAL / BLOCKED / RUNNING / COMPLETED / FAILED / SKIPPED / UNAVAILABLE / ERROR, every decision has detail | reason/detail/unlock/failed-prerequisite tests | LOCAL_RUNTIME_SUBSTRATE |
| P3.2.11–P3.2.15 | Approval-wait / blocked / unavailable semantics; scheduler never approves itself | DONE | approval nodes return WAITING_APPROVAL until an explicit recorded approval mark; failed prerequisite → BLOCKED with named prerequisite; UNAVAILABLE node type/state honored | approval/blocked/unavailable tests | LOCAL_RUNTIME_SUBSTRATE |
| P3.2.16–P3.2.20 | No-execution boundary + foundation read model binding | DONE | `FlowNoExecutionProof` all-false; decision booleans false; `FlowRuntimeFoundationReadModel` (`flow_runtime_foundation_read_model.v1`) with UNAVAILABLE capability entries | `test_p3_flow_a_no_execution_boundary.py`, `test_p3_flow_a_runtime_read_model.py` | LOCAL_RUNTIME_SUBSTRATE + UNAVAILABLE (execution/trace/CLI) |

Rollup: **P3.0.0–P3.0.20 DONE. P3.1.0–P3.1.20 DONE** at in-memory substrate
scope with external persistence honestly UNAVAILABLE. **P3.2.0–P3.2.20
DONE.** No checkpoint is claimed BLOCKED or NOT DONE within this pack's
scope; the only UNAVAILABLE items are deliberate boundary declarations
(execution, trace verification, CLI binding, event stream, approval runtime,
external persistence).

## 5. Checkpoint-by-checkpoint Status

See capsule matrix above (Section 4). Every capsule group is DONE with
evidence and mapped tests. UNAVAILABLE declarations with reasons:

- Execution — UNAVAILABLE — belongs to P4 AurelExec.
- Trace verification — UNAVAILABLE — belongs to P5 AurelTrace.
- CLI/TUI binding — UNAVAILABLE — belongs to P3.7.
- Runtime event stream — UNAVAILABLE — belongs to P3.3 / P3-FLOW-B.
- Approval pause/resume runtime — UNAVAILABLE — belongs to P3.4.
- External persistence — UNAVAILABLE — run state is in-memory only.

## 6. Implementation Summary

New package `src/agentic_runtime/aurel_flow/` (self-contained; no dependency
on `aurel_shell` projection modules):

- `errors.py` — `AurelFlowErrorCode` (23 codes), `AurelFlowError`,
  `AurelFlowValidationError` (structured code + field, fail-closed).
- `types.py` — pack constants, `FlowTruthLabel`, `FlowSourceLabel`,
  `FORBIDDEN_FLOW_TRUTH_LABELS` (LIVE, TRACE_VERIFIED — never assigned),
  canonical JSON serialization + sha256 `stable_hash`.
- `workflow_graph.py` — `WorkflowNodeType` (7), `WorkflowEdgeType` (6),
  `WorkflowNode`, `WorkflowEdge`, `WorkflowGraphSpec` (closed world),
  `WorkflowGraph`, `WorkflowGraphValidationIssue/Result`,
  `WorkflowGraphReadModel`, `build_workflow_graph`,
  `validate_workflow_graph`, `build_workflow_graph_read_model`.
  `DEPENDENCY_EDGE_TYPES` distinguishes scheduling dependencies
  (DEFAULT/CONDITIONAL/APPROVAL_REQUIRED) from declarative markers
  (ERROR/ROLLBACK_CANDIDATE/UNAVAILABLE).
- `workflow_state.py` — `WorkflowLifecycleStatus` (10),
  `WorkflowNodeState` (11), `WorkflowTransitionKind`, allowed-transition
  maps with terminal states, `WorkflowStateTransition`, `WorkflowRunState`,
  immutable `WorkflowRun`, `WorkflowStateValidationIssue/Result`,
  `WorkflowStateSnapshot`, `create_workflow_run`,
  `validate_workflow_state_transition`, `transition_workflow_run`
  (returns a new run; explicit snapshots + transitions, no hidden mutation;
  P3.3 event-stream compatible), `snapshot_workflow_state`,
  `lifecycle_transition` / `node_transition` helpers.
- `scheduler.py` — `SchedulerDecisionReason` (10), `SchedulerNodeDecision`,
  `SchedulableNode`, `ReadyQueue`, `SchedulerDecision`,
  `calculate_node_decisions`, `calculate_ready_queue`,
  `make_scheduler_decision`. Pure calculation over graph + recorded state;
  graph/run hash mismatch fails closed; a decision is a readiness
  explanation, not an execution capability (object-capability boundary).
- `read_model.py` — `FlowNoExecutionProof` (18 all-false booleans),
  `FlowCapabilityAvailability`, `UNAVAILABLE_CAPABILITIES` (6 entries with
  reasons), `FlowRuntimeFoundationReadModel`,
  `build_flow_runtime_read_model`, `serialize_flow_runtime_read_model`.
- `demo.py` — DEV_FIXTURE deterministic demo:
  `build_demo_workflow_graph()` (start → fetch → approval gate → apply →
  end, plus a declarative ROLLBACK_CANDIDATE back-edge) and
  `run_flow_foundation_demo()` leaving the run mid-flight so the read model
  shows COMPLETED, WAITING_APPROVAL, and WAITING_DEPENDENCY truth at once.
- `__init__.py` — public exports.

## 7. Graph Foundation Proof

- Valid graph builds and validates: `test_valid_graph_passes_validation`.
- Fail-closed on: duplicate node IDs, duplicate edge IDs, unknown edge
  endpoints, unsupported node/edge types under a restricted closed-world
  spec, missing/unknown entry and exit nodes, dependency cycles, unreachable
  nodes, APPROVAL node without `requires_approval`, empty graph_id/name.
- ROLLBACK_CANDIDATE back-edge is provably *not* a dependency cycle
  (`test_rollback_candidate_back_edge_is_not_a_dependency_cycle`).
- `graph_hash` and canonical JSON are deterministic and input-sensitive.

## 8. Durable State / Lifecycle Proof

- Run creation from a valid graph yields deterministic run_id, lifecycle
  CREATED, step 0, empty history, all nodes NOT_STARTED.
- Run creation from an invalid graph raises `INVALID_GRAPH` (fail closed).
- Safe lifecycle chain CREATED→READY→RUNNING→COMPLETED passes; CREATED→
  RUNNING fails; COMPLETED→RUNNING fails with `TERMINAL_LIFECYCLE_STATE`;
  stale `from_value` fails with `STALE_TRANSITION_SOURCE`.
- Node transitions honor the allowed map; terminal node states reject further
  transitions; unknown node targets fail.
- Runs are immutable: transitions return new runs; the original run is
  unchanged (asserted).
- Snapshots cover all graph nodes, are hash-deterministic, and change hash
  when state changes.
- Durability truth is honest: `persisted=False`,
  `persistence_label=UNAVAILABLE_PERSISTENCE`, reason "in-memory only". No
  fake persistence claim.

## 9. Scheduler / Ready Queue Proof

- Entry node is initially READY; dependents are WAITING_DEPENDENCY with the
  unsatisfied prerequisites named.
- Completing a prerequisite (via explicit recorded marks) unlocks the next
  node to READY.
- Approval-required node returns WAITING_APPROVAL with detail "the scheduler
  does not approve nodes (approval runtime belongs to P3.4)"; deciding twice
  changes nothing (pure); only an explicit recorded WAITING_APPROVAL→READY
  mark makes it READY.
- Failed prerequisite → dependent BLOCKED with the failed prerequisite named.
- UNAVAILABLE node type → UNAVAILABLE reason; recorded UNAVAILABLE
  prerequisite → dependent BLOCKED with reason.
- Every node decision carries an explicit reason and non-empty detail; no
  silent blockage, no vague pending state.
- Ready-queue buckets and hashes are deterministic; graph/run mismatch fails
  closed with `GRAPH_RUN_MISMATCH`.

## 10. Operator-Testable Path

Local, no-network, deterministic:

```bash
.venv/bin/python -m pytest tests/test_p3_flow_a_workflow_graph.py \
  tests/test_p3_flow_a_workflow_state.py \
  tests/test_p3_flow_a_scheduler_ready_queue.py \
  tests/test_p3_flow_a_no_execution_boundary.py \
  tests/test_p3_flow_a_runtime_read_model.py -q

.venv/bin/python -c "
from agentic_runtime.aurel_flow.demo import run_flow_foundation_demo
from agentic_runtime.aurel_flow import serialize_flow_runtime_read_model
print(serialize_flow_runtime_read_model(run_flow_foundation_demo()))"
```

The demo read model shows: graph summary (5 nodes / 5 edges, valid), run
lifecycle RUNNING at step 8, start/fetch COMPLETED, gate WAITING_APPROVAL,
apply/end WAITING_DEPENDENCY, empty ready queue (the approval gate honestly
holds everything), truth labels, six UNAVAILABLE capability declarations,
and the all-false no-execution proof.

## 11. Truth Labels

- LIVE: **not used** (forbidden in this pack; enforced by test).
- TRACE_VERIFIED: **not used** (forbidden in this pack; enforced by test).
- SIMULATED: not used.
- DEV_FIXTURE: demo graph/run in `demo.py` only.
- UNAVAILABLE: execution, trace verification, CLI binding, event stream,
  approval runtime, persistence — each with an explicit reason.
- ERROR: available in vocabulary for error states; not asserted as a truth
  claim anywhere.
- Additional labels used: LOCAL_RUNTIME_SUBSTRATE (graph/state/scheduler
  models), UNAVAILABLE_PERSISTENCE (run durability),
  UNAVAILABLE_EXECUTION / UNAVAILABLE_TRACE_VERIFICATION /
  UNAVAILABLE_CLI_BINDING / UNAVAILABLE_EVENT_STREAM /
  UNAVAILABLE_APPROVAL_RUNTIME (capability entries).

## 12. No-Execution Boundary Proof

- Source-scan test proves no `subprocess`/`socket`/`requests`/`urllib`/
  `httpx`/`asyncio` imports and no `os.system`/`os.exec*`/`os.spawn*`/
  `popen`/`eval(`/`exec(` in any `aurel_flow` source file.
- `SchedulerDecision.is_execution_capability/executes_nodes/dispatches_work/
  approves_approvals` are False; `ReadyQueue.executes_nothing` is True;
  `SchedulableNode.is_execution_grant` is False.
- Scheduling and read-model building never mutate run state (asserted on
  node states, lifecycle, step, and history).
- `FlowNoExecutionProof` is all-false across 18 fields: tool, command,
  subprocess, network, sandbox, worker dispatch, agent dispatch, approval
  execution, retry, rollback, memory write, policy mutation, identity
  mutation, global trace write, ledger write, business action, live claim,
  trace-verified claim.
- Read model asserts `live=False`, `trace_verified=False`, and no forbidden
  truth label appears.

## 13. Tests / Validation

Focused tests added (50 total):

- `tests/test_p3_flow_a_workflow_graph.py` — 15 tests
- `tests/test_p3_flow_a_workflow_state.py` — 12 tests
- `tests/test_p3_flow_a_scheduler_ready_queue.py` — 8 tests
- `tests/test_p3_flow_a_no_execution_boundary.py` — 6 tests
- `tests/test_p3_flow_a_runtime_read_model.py` — 9 tests

Validation run (all through `.venv/bin/python`):

- `compileall src tests` — **PASS**
- P3-FLOW-A focused tests — **50 passed**
- P2.11-C regression subset per `agent/TESTS.md` (P2.11-C inspection ×5,
  command preflight, validation truth gates + drift gates, Golden Thread B)
  — **67 passed**
- `ruff check src tests` — **PASS**
- `mypy src/agentic_runtime` — **PASS** (362 source files)

Not run (honest): full pytest suite, coverage, Bandit, core strict mypy
probe. No full-suite PASS and no coverage claim is made.

## 14. Files Created / Modified

Created:

- `src/agentic_runtime/aurel_flow/__init__.py`
- `src/agentic_runtime/aurel_flow/errors.py`
- `src/agentic_runtime/aurel_flow/types.py`
- `src/agentic_runtime/aurel_flow/workflow_graph.py`
- `src/agentic_runtime/aurel_flow/workflow_state.py`
- `src/agentic_runtime/aurel_flow/scheduler.py`
- `src/agentic_runtime/aurel_flow/read_model.py`
- `src/agentic_runtime/aurel_flow/demo.py`
- `tests/test_p3_flow_a_workflow_graph.py`
- `tests/test_p3_flow_a_workflow_state.py`
- `tests/test_p3_flow_a_scheduler_ready_queue.py`
- `tests/test_p3_flow_a_no_execution_boundary.py`
- `tests/test_p3_flow_a_runtime_read_model.py`
- `agent/reports/P3_FLOW_A_AURELFLOW_RUNTIME_FOUNDATION_SUPERPACK.md`

Modified:

- `agent/REPORTS.md` (report indexed)
- `agent/STATE.md` (P3-FLOW-A status + override truth)
- `agent/ACTIVE_TASK.md` (P3-FLOW-A status; P3-FLOW-B next; P2.11-D–P2.20 deferred)
- `agent/ROADMAP.md` (active canon table sync: operator override + current position)
- `agent/ARCHITECTURE.md` (aurel_flow module map row)
- `agent/DECISIONS.md` (operator override + AurelFlow boundary decisions)
- `agent/TESTS.md` (P3-FLOW-A validation section)

## 15. What Was Deliberately Not Implemented

- P3.3 Runtime Event Stream (state transitions are shaped for it, not emitted).
- P3.4 Approval Pause/Resume runtime (WAITING_APPROVAL is a scheduler reason
  and a transition primitive, not an approval runtime).
- P3.5 Retry/Recovery/Rollback runtime (ROLLBACK_CANDIDATE edges are
  declarative markers only).
- P3.6 Flow State Projection full pack; P3.7 Flow CLI/TUI binding; P3.8 Flow
  Docs/Reports; P3.9 Flow Exit Seal; P3.10–P3.12.
- P4 AurelExec execution engine; P5 AurelTrace verification; P9 Custos
  enforcement; any worker registry, agent dispatch, sandbox/network/
  subprocess behavior, memory writes, policy/identity mutation, Ledger or
  global Trace writes.
- External persistence (no database/file store; honestly labeled
  UNAVAILABLE_PERSISTENCE).

## 16. Remaining Risks

- Graph: reachability/cycle checks cover dependency edges; richer condition
  semantics on CONDITIONAL edges are future scope (P3.3+/DECISION runtime).
- State: in-memory-only durability means run state does not survive process
  exit; durable storage is a future pack decision.
- Scheduler: readiness reasons are per-node; cross-run scheduling policy
  (priorities, concurrency budgets) is out of scope.
- Persistence / CLI binding / trace verification / execution: all
  UNAVAILABLE by design; risk is only that a future pack forgets to flip the
  honest labels when implementing them.
- Next pack risk: P3-FLOW-B must build the event stream on top of the
  transition history without redefining transition semantics.
- Process risk: P2.11-D–P2.20 remain deferred by operator override; the P2
  tail must be resumed after full P3 or the P2 exit seal will remain open.

## 17. Next Pack

**P3-FLOW-B — Runtime Event Stream / Approval Pause / Retry-Recovery-Rollback
Pack** (P3.3–P3.5). After full P3: resume the deferred P2 tail
(P2.11-D → P2.20 Final Seven-Surface Exit Seal).

## 18. Commit Hash

Implementation commit: recorded in the follow-up docs commit per repo
convention (see `git log` — `feat(flow): add P3-FLOW-A runtime foundation`).

## 19. Final Git Status

Clean after commit (verified in Section 13 validation flow; only in-scope
files staged and committed; no push; no branch created).
