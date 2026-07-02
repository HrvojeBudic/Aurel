"""P3-FLOW-A workflow run state / lifecycle (P3.1.x).

Workflow state tracks lifecycle; it is not proof and not execution. Runs are
immutable: every transition returns a new run with the transition appended to
its history, so state evolves as explicit snapshots + transitions rather than
hidden procedural mutation (future P3.3 event-stream compatible).

Durability truth: run state is in-memory only. There is no database, file, or
external persistence in this pack, and none is claimed.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from typing import Mapping

from .errors import AurelFlowErrorCode, AurelFlowValidationError
from .types import (
    PERSISTENCE_UNAVAILABLE_REASON,
    FlowSourceLabel,
    FlowTruthLabel,
    _CanonicalMixin,
    stable_hash,
)
from .workflow_graph import (
    DEFAULT_WORKFLOW_GRAPH_SPEC,
    WorkflowGraph,
    WorkflowGraphSpec,
    validate_workflow_graph,
)

WORKFLOW_RUN_CONTRACT_VERSION = "workflow_run.v1"
WORKFLOW_STATE_SNAPSHOT_VERSION = "workflow_state_snapshot.v1"
WORKFLOW_LIFECYCLE_TARGET = "workflow"
PERSISTENCE_LABEL_UNAVAILABLE = "UNAVAILABLE_PERSISTENCE"


class WorkflowLifecycleStatus(str, Enum):
    CREATED = "CREATED"
    READY = "READY"
    RUNNING = "RUNNING"
    WAITING = "WAITING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


class WorkflowNodeState(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    READY = "READY"
    RUNNING = "RUNNING"
    WAITING_DEPENDENCY = "WAITING_DEPENDENCY"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    BLOCKED = "BLOCKED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


class WorkflowTransitionKind(str, Enum):
    LIFECYCLE = "LIFECYCLE"
    NODE = "NODE"


# Safe lifecycle transitions. COMPLETED / FAILED / CANCELLED / UNAVAILABLE /
# ERROR are terminal: a completed workflow cannot return to running.
ALLOWED_LIFECYCLE_TRANSITIONS: dict[
    WorkflowLifecycleStatus, tuple[WorkflowLifecycleStatus, ...]
] = {
    WorkflowLifecycleStatus.CREATED: (
        WorkflowLifecycleStatus.READY,
        WorkflowLifecycleStatus.CANCELLED,
        WorkflowLifecycleStatus.ERROR,
    ),
    WorkflowLifecycleStatus.READY: (
        WorkflowLifecycleStatus.RUNNING,
        WorkflowLifecycleStatus.CANCELLED,
        WorkflowLifecycleStatus.ERROR,
    ),
    WorkflowLifecycleStatus.RUNNING: (
        WorkflowLifecycleStatus.WAITING,
        WorkflowLifecycleStatus.PAUSED,
        WorkflowLifecycleStatus.COMPLETED,
        WorkflowLifecycleStatus.FAILED,
        WorkflowLifecycleStatus.CANCELLED,
        WorkflowLifecycleStatus.ERROR,
    ),
    WorkflowLifecycleStatus.WAITING: (
        WorkflowLifecycleStatus.RUNNING,
        WorkflowLifecycleStatus.PAUSED,
        WorkflowLifecycleStatus.CANCELLED,
        WorkflowLifecycleStatus.FAILED,
        WorkflowLifecycleStatus.ERROR,
    ),
    WorkflowLifecycleStatus.PAUSED: (
        WorkflowLifecycleStatus.RUNNING,
        WorkflowLifecycleStatus.CANCELLED,
        WorkflowLifecycleStatus.ERROR,
    ),
    WorkflowLifecycleStatus.COMPLETED: (),
    WorkflowLifecycleStatus.FAILED: (),
    WorkflowLifecycleStatus.CANCELLED: (),
    WorkflowLifecycleStatus.UNAVAILABLE: (),
    WorkflowLifecycleStatus.ERROR: (),
}

# Safe node-state transitions. WAITING_APPROVAL -> READY is a recorded
# approval mark primitive for the future P3.4 approval runtime; nothing in
# this pack grants or executes approval. RUNNING/COMPLETED marks are recorded
# state, not execution.
ALLOWED_NODE_TRANSITIONS: dict[WorkflowNodeState, tuple[WorkflowNodeState, ...]] = {
    WorkflowNodeState.NOT_STARTED: (
        WorkflowNodeState.READY,
        WorkflowNodeState.WAITING_DEPENDENCY,
        WorkflowNodeState.WAITING_APPROVAL,
        WorkflowNodeState.BLOCKED,
        WorkflowNodeState.SKIPPED,
        WorkflowNodeState.UNAVAILABLE,
        WorkflowNodeState.ERROR,
    ),
    WorkflowNodeState.READY: (
        WorkflowNodeState.RUNNING,
        WorkflowNodeState.WAITING_APPROVAL,
        WorkflowNodeState.BLOCKED,
        WorkflowNodeState.SKIPPED,
        WorkflowNodeState.ERROR,
    ),
    WorkflowNodeState.WAITING_DEPENDENCY: (
        WorkflowNodeState.READY,
        WorkflowNodeState.WAITING_APPROVAL,
        WorkflowNodeState.BLOCKED,
        WorkflowNodeState.SKIPPED,
        WorkflowNodeState.ERROR,
    ),
    WorkflowNodeState.WAITING_APPROVAL: (
        WorkflowNodeState.READY,
        WorkflowNodeState.BLOCKED,
        WorkflowNodeState.SKIPPED,
        WorkflowNodeState.ERROR,
    ),
    WorkflowNodeState.RUNNING: (
        WorkflowNodeState.COMPLETED,
        WorkflowNodeState.FAILED,
        WorkflowNodeState.ERROR,
    ),
    WorkflowNodeState.BLOCKED: (
        WorkflowNodeState.READY,
        WorkflowNodeState.SKIPPED,
        WorkflowNodeState.ERROR,
    ),
    WorkflowNodeState.COMPLETED: (),
    WorkflowNodeState.FAILED: (),
    WorkflowNodeState.SKIPPED: (),
    WorkflowNodeState.UNAVAILABLE: (),
    WorkflowNodeState.ERROR: (),
}

TERMINAL_LIFECYCLE_STATUSES: tuple[WorkflowLifecycleStatus, ...] = tuple(
    status for status, targets in ALLOWED_LIFECYCLE_TRANSITIONS.items() if not targets
)
TERMINAL_NODE_STATES: tuple[WorkflowNodeState, ...] = tuple(
    state for state, targets in ALLOWED_NODE_TRANSITIONS.items() if not targets
)


@dataclass(frozen=True)
class WorkflowStateTransition(_CanonicalMixin):
    """Safe lifecycle / node-state transition model.

    ``target`` is ``"workflow"`` for LIFECYCLE transitions or a node_id for
    NODE transitions. ``from_value`` must match current state (optimistic
    staleness check); values are enum value strings.
    """

    kind: WorkflowTransitionKind
    target: str
    from_value: str
    to_value: str
    reason: str = ""


@dataclass(frozen=True)
class WorkflowRunState(_CanonicalMixin):
    """Current lifecycle + node state map at a monotonic step."""

    lifecycle_status: WorkflowLifecycleStatus
    node_states: Mapping[str, WorkflowNodeState]
    step: int


@dataclass(frozen=True)
class WorkflowRun(_CanonicalMixin):
    """Workflow run created from a valid graph. Immutable; in-memory only."""

    run_id: str
    run_key: str
    graph_id: str
    graph_hash: str
    contract_version: str
    state: WorkflowRunState
    history: tuple[WorkflowStateTransition, ...]
    truth_label: FlowTruthLabel
    source_label: FlowSourceLabel
    persisted: bool
    persistence_label: str
    persistence_reason: str


@dataclass(frozen=True)
class WorkflowStateValidationIssue(_CanonicalMixin):
    code: AurelFlowErrorCode
    field: str
    message: str


@dataclass(frozen=True)
class WorkflowStateValidationResult(_CanonicalMixin):
    """Transition/state validation result. Any issue means invalid."""

    run_id: str
    step: int
    valid: bool
    issues: tuple[WorkflowStateValidationIssue, ...]


@dataclass(frozen=True)
class WorkflowStateSnapshot(_CanonicalMixin):
    """Deterministic read-only snapshot of run state. Not proof, not trace."""

    snapshot_version: str
    run_id: str
    graph_id: str
    graph_hash: str
    step: int
    lifecycle_status: WorkflowLifecycleStatus
    node_states: Mapping[str, WorkflowNodeState]
    transition_count: int
    truth_label: FlowTruthLabel
    persisted: bool
    persistence_label: str
    snapshot_hash: str


def lifecycle_transition(
    from_status: WorkflowLifecycleStatus,
    to_status: WorkflowLifecycleStatus,
    reason: str = "",
) -> WorkflowStateTransition:
    return WorkflowStateTransition(
        kind=WorkflowTransitionKind.LIFECYCLE,
        target=WORKFLOW_LIFECYCLE_TARGET,
        from_value=from_status.value,
        to_value=to_status.value,
        reason=reason,
    )


def node_transition(
    node_id: str,
    from_state: WorkflowNodeState,
    to_state: WorkflowNodeState,
    reason: str = "",
) -> WorkflowStateTransition:
    return WorkflowStateTransition(
        kind=WorkflowTransitionKind.NODE,
        target=node_id,
        from_value=from_state.value,
        to_value=to_state.value,
        reason=reason,
    )


def create_workflow_run(
    graph: WorkflowGraph,
    *,
    run_key: str = "run-0001",
    spec: WorkflowGraphSpec = DEFAULT_WORKFLOW_GRAPH_SPEC,
    truth_label: FlowTruthLabel = FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
    source_label: FlowSourceLabel = FlowSourceLabel.LOCAL_CONSTRUCTION,
) -> WorkflowRun:
    """Create a run from a valid graph. Invalid graphs fail closed."""

    if not run_key:
        raise AurelFlowValidationError(
            "run_key must be non-empty",
            code=AurelFlowErrorCode.EMPTY_RUN_KEY,
            field="run_key",
        )
    validation = validate_workflow_graph(graph, spec)
    if not validation.valid:
        codes = ", ".join(sorted({issue.code.value for issue in validation.issues}))
        raise AurelFlowValidationError(
            f"cannot create workflow run from invalid graph {graph.graph_id!r}: {codes}",
            code=AurelFlowErrorCode.INVALID_GRAPH,
            field="graph",
        )
    run_id = "wfrun-" + stable_hash(
        {"graph_hash": graph.graph_hash, "run_key": run_key}
    )[:16]
    node_states = {node.node_id: WorkflowNodeState.NOT_STARTED for node in graph.nodes}
    return WorkflowRun(
        run_id=run_id,
        run_key=run_key,
        graph_id=graph.graph_id,
        graph_hash=graph.graph_hash,
        contract_version=WORKFLOW_RUN_CONTRACT_VERSION,
        state=WorkflowRunState(
            lifecycle_status=WorkflowLifecycleStatus.CREATED,
            node_states=node_states,
            step=0,
        ),
        history=(),
        truth_label=truth_label,
        source_label=source_label,
        persisted=False,
        persistence_label=PERSISTENCE_LABEL_UNAVAILABLE,
        persistence_reason=PERSISTENCE_UNAVAILABLE_REASON,
    )


def validate_workflow_state_transition(
    run: WorkflowRun, transition: WorkflowStateTransition
) -> WorkflowStateValidationResult:
    issues: list[WorkflowStateValidationIssue] = []

    def issue(code: AurelFlowErrorCode, field_name: str, message: str) -> None:
        issues.append(
            WorkflowStateValidationIssue(code=code, field=field_name, message=message)
        )

    if transition.kind is WorkflowTransitionKind.LIFECYCLE:
        if transition.target != WORKFLOW_LIFECYCLE_TARGET:
            issue(
                AurelFlowErrorCode.UNKNOWN_TRANSITION_TARGET,
                "target",
                f"lifecycle transition target must be {WORKFLOW_LIFECYCLE_TARGET!r}",
            )
        current = run.state.lifecycle_status
        try:
            to_status = WorkflowLifecycleStatus(transition.to_value)
        except ValueError:
            to_status = None
            issue(
                AurelFlowErrorCode.INVALID_LIFECYCLE_TRANSITION,
                "to_value",
                f"unknown lifecycle status {transition.to_value!r}",
            )
        if transition.from_value != current.value:
            issue(
                AurelFlowErrorCode.STALE_TRANSITION_SOURCE,
                "from_value",
                f"transition expects {transition.from_value!r} but run is {current.value!r}",
            )
        if to_status is not None:
            if current in TERMINAL_LIFECYCLE_STATUSES:
                issue(
                    AurelFlowErrorCode.TERMINAL_LIFECYCLE_STATE,
                    "from_value",
                    f"lifecycle status {current.value!r} is terminal",
                )
            elif to_status not in ALLOWED_LIFECYCLE_TRANSITIONS[current]:
                issue(
                    AurelFlowErrorCode.INVALID_LIFECYCLE_TRANSITION,
                    "to_value",
                    f"lifecycle transition {current.value!r} -> {to_status.value!r} is not allowed",
                )
    else:
        node_id = transition.target
        if node_id not in run.state.node_states:
            issue(
                AurelFlowErrorCode.UNKNOWN_TRANSITION_TARGET,
                "target",
                f"node {node_id!r} is not part of run {run.run_id!r}",
            )
        else:
            current_node = run.state.node_states[node_id]
            try:
                to_state = WorkflowNodeState(transition.to_value)
            except ValueError:
                to_state = None
                issue(
                    AurelFlowErrorCode.INVALID_NODE_TRANSITION,
                    "to_value",
                    f"unknown node state {transition.to_value!r}",
                )
            if transition.from_value != current_node.value:
                issue(
                    AurelFlowErrorCode.STALE_TRANSITION_SOURCE,
                    "from_value",
                    f"transition expects {transition.from_value!r} but node {node_id!r} "
                    f"is {current_node.value!r}",
                )
            if to_state is not None:
                if current_node in TERMINAL_NODE_STATES:
                    issue(
                        AurelFlowErrorCode.TERMINAL_NODE_STATE,
                        "from_value",
                        f"node state {current_node.value!r} is terminal",
                    )
                elif to_state not in ALLOWED_NODE_TRANSITIONS[current_node]:
                    issue(
                        AurelFlowErrorCode.INVALID_NODE_TRANSITION,
                        "to_value",
                        f"node transition {current_node.value!r} -> {to_state.value!r} "
                        "is not allowed",
                    )

    return WorkflowStateValidationResult(
        run_id=run.run_id,
        step=run.state.step,
        valid=not issues,
        issues=tuple(issues),
    )


def transition_workflow_run(
    run: WorkflowRun, transition: WorkflowStateTransition
) -> WorkflowRun:
    """Apply a safe transition, returning a new immutable run. Fails closed."""

    validation = validate_workflow_state_transition(run, transition)
    if not validation.valid:
        first = validation.issues[0]
        raise AurelFlowValidationError(first.message, code=first.code, field=first.field)

    if transition.kind is WorkflowTransitionKind.LIFECYCLE:
        new_state = WorkflowRunState(
            lifecycle_status=WorkflowLifecycleStatus(transition.to_value),
            node_states=dict(run.state.node_states),
            step=run.state.step + 1,
        )
    else:
        node_states = dict(run.state.node_states)
        node_states[transition.target] = WorkflowNodeState(transition.to_value)
        new_state = WorkflowRunState(
            lifecycle_status=run.state.lifecycle_status,
            node_states=node_states,
            step=run.state.step + 1,
        )
    return replace(run, state=new_state, history=run.history + (transition,))


def snapshot_workflow_state(run: WorkflowRun) -> WorkflowStateSnapshot:
    """Deterministic read-only snapshot of the current run state."""

    payload = {
        "snapshot_version": WORKFLOW_STATE_SNAPSHOT_VERSION,
        "run_id": run.run_id,
        "graph_hash": run.graph_hash,
        "step": run.state.step,
        "lifecycle_status": run.state.lifecycle_status,
        "node_states": dict(run.state.node_states),
    }
    return WorkflowStateSnapshot(
        snapshot_version=WORKFLOW_STATE_SNAPSHOT_VERSION,
        run_id=run.run_id,
        graph_id=run.graph_id,
        graph_hash=run.graph_hash,
        step=run.state.step,
        lifecycle_status=run.state.lifecycle_status,
        node_states=dict(run.state.node_states),
        transition_count=len(run.history),
        truth_label=run.truth_label,
        persisted=run.persisted,
        persistence_label=run.persistence_label,
        snapshot_hash=stable_hash(payload),
    )
