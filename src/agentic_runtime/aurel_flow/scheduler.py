"""P3-FLOW-A scheduler / ready queue (P3.2.x).

The scheduler decides readiness; it does not execute. A scheduler decision is
a readiness explanation, not a capability to execute (object-capability
boundary). This module never dispatches, executes, calls tools, calls
workers, spawns subprocesses, or mutates run state — it is a pure calculation
over graph + recorded run state. Approval-required nodes wait; the scheduler
never approves them itself.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .errors import AurelFlowErrorCode, AurelFlowValidationError
from .types import FlowTruthLabel, _CanonicalMixin, stable_hash
from .workflow_graph import (
    DEPENDENCY_EDGE_TYPES,
    WorkflowEdgeType,
    WorkflowGraph,
    WorkflowNode,
    WorkflowNodeType,
)
from .workflow_state import WorkflowNodeState, WorkflowRun

READY_QUEUE_VERSION = "ready_queue.v1"
SCHEDULER_DECISION_VERSION = "scheduler_decision.v1"


class SchedulerDecisionReason(str, Enum):
    """Explicit per-node readiness reasons. RUNNING and SKIPPED are
    implementation-level additions so recorded states are never mislabeled."""

    READY = "READY"
    WAITING_DEPENDENCY = "WAITING_DEPENDENCY"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    BLOCKED = "BLOCKED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


# Prerequisite states that satisfy a dependency edge.
_DEPENDENCY_SATISFIED_STATES = (WorkflowNodeState.COMPLETED, WorkflowNodeState.SKIPPED)
_DEPENDENCY_DEAD_STATES = (WorkflowNodeState.FAILED, WorkflowNodeState.ERROR)


@dataclass(frozen=True)
class SchedulerNodeDecision(_CanonicalMixin):
    node_id: str
    node_state: WorkflowNodeState
    reason: SchedulerDecisionReason
    detail: str


@dataclass(frozen=True)
class SchedulableNode(_CanonicalMixin):
    """Node candidate for future execution, without executing it.

    ``is_execution_grant`` is permanently False: appearing in the ready queue
    grants no authority to run anything.
    """

    node_id: str
    node_type: WorkflowNodeType
    requires_approval: bool
    risk_tier: str
    reason: SchedulerDecisionReason
    detail: str
    is_execution_grant: bool
    truth_label: FlowTruthLabel


@dataclass(frozen=True)
class ReadyQueue(_CanonicalMixin):
    """Calculated list of schedulable nodes plus waiting/blocked truth."""

    queue_version: str
    run_id: str
    graph_id: str
    step: int
    schedulable_nodes: tuple[SchedulableNode, ...]
    ready_node_ids: tuple[str, ...]
    waiting_dependency_node_ids: tuple[str, ...]
    waiting_approval_node_ids: tuple[str, ...]
    blocked_node_ids: tuple[str, ...]
    running_node_ids: tuple[str, ...]
    completed_node_ids: tuple[str, ...]
    failed_node_ids: tuple[str, ...]
    skipped_node_ids: tuple[str, ...]
    unavailable_node_ids: tuple[str, ...]
    error_node_ids: tuple[str, ...]
    executes_nothing: bool
    truth_label: FlowTruthLabel
    queue_hash: str


@dataclass(frozen=True)
class SchedulerDecision(_CanonicalMixin):
    """Scheduler output explaining next-ready/waiting/blocked status.

    A decision object is not a dispatcher: all execution-authority booleans
    are permanently False.
    """

    decision_version: str
    run_id: str
    graph_id: str
    step: int
    node_decisions: tuple[SchedulerNodeDecision, ...]
    ready_node_ids: tuple[str, ...]
    next_ready_node_id: str
    is_execution_capability: bool
    executes_nodes: bool
    dispatches_work: bool
    approves_approvals: bool
    truth_label: FlowTruthLabel
    decision_hash: str


def _require_matching_graph(graph: WorkflowGraph, run: WorkflowRun) -> None:
    if graph.graph_hash != run.graph_hash:
        raise AurelFlowValidationError(
            f"run {run.run_id!r} was created from graph hash {run.graph_hash!r}, "
            f"not {graph.graph_hash!r}",
            code=AurelFlowErrorCode.GRAPH_RUN_MISMATCH,
            field="graph",
        )


def _dependency_map(graph: WorkflowGraph) -> dict[str, tuple[str, ...]]:
    prerequisites: dict[str, list[str]] = {node.node_id: [] for node in graph.nodes}
    for edge in graph.edges:
        if edge.edge_type in DEPENDENCY_EDGE_TYPES and edge.to_node_id in prerequisites:
            prerequisites[edge.to_node_id].append(edge.from_node_id)
    return {node_id: tuple(deps) for node_id, deps in prerequisites.items()}


def _approval_required(graph: WorkflowGraph, node: WorkflowNode) -> bool:
    if node.requires_approval or node.node_type is WorkflowNodeType.APPROVAL:
        return True
    return any(
        edge.edge_type is WorkflowEdgeType.APPROVAL_REQUIRED
        and edge.to_node_id == node.node_id
        for edge in graph.edges
    )


_RECORDED_STATE_REASONS: dict[WorkflowNodeState, SchedulerDecisionReason] = {
    WorkflowNodeState.COMPLETED: SchedulerDecisionReason.COMPLETED,
    WorkflowNodeState.FAILED: SchedulerDecisionReason.FAILED,
    WorkflowNodeState.SKIPPED: SchedulerDecisionReason.SKIPPED,
    WorkflowNodeState.ERROR: SchedulerDecisionReason.ERROR,
    WorkflowNodeState.UNAVAILABLE: SchedulerDecisionReason.UNAVAILABLE,
    WorkflowNodeState.RUNNING: SchedulerDecisionReason.RUNNING,
}


def _decide_node(
    graph: WorkflowGraph,
    run: WorkflowRun,
    node: WorkflowNode,
    prerequisites: tuple[str, ...],
) -> SchedulerNodeDecision:
    state = run.state.node_states[node.node_id]

    recorded = _RECORDED_STATE_REASONS.get(state)
    if recorded is not None:
        return SchedulerNodeDecision(
            node_id=node.node_id,
            node_state=state,
            reason=recorded,
            detail=f"node state is recorded {state.value}",
        )

    if node.node_type is WorkflowNodeType.UNAVAILABLE:
        return SchedulerNodeDecision(
            node_id=node.node_id,
            node_state=state,
            reason=SchedulerDecisionReason.UNAVAILABLE,
            detail="node type is UNAVAILABLE",
        )

    node_states = run.state.node_states
    dead = [dep for dep in prerequisites if node_states.get(dep) in _DEPENDENCY_DEAD_STATES]
    if dead:
        return SchedulerNodeDecision(
            node_id=node.node_id,
            node_state=state,
            reason=SchedulerDecisionReason.BLOCKED,
            detail="prerequisite failed: " + ", ".join(sorted(dead)),
        )

    unavailable_deps = sorted(
        dep
        for dep in prerequisites
        if node_states.get(dep) is WorkflowNodeState.UNAVAILABLE
    )
    if unavailable_deps:
        return SchedulerNodeDecision(
            node_id=node.node_id,
            node_state=state,
            reason=SchedulerDecisionReason.BLOCKED,
            detail="prerequisite unavailable: " + ", ".join(unavailable_deps),
        )

    unsatisfied = sorted(
        dep
        for dep in prerequisites
        if node_states.get(dep) not in _DEPENDENCY_SATISFIED_STATES
    )
    if unsatisfied:
        return SchedulerNodeDecision(
            node_id=node.node_id,
            node_state=state,
            reason=SchedulerDecisionReason.WAITING_DEPENDENCY,
            detail="waiting on prerequisites: " + ", ".join(unsatisfied),
        )

    if state is WorkflowNodeState.BLOCKED:
        return SchedulerNodeDecision(
            node_id=node.node_id,
            node_state=state,
            reason=SchedulerDecisionReason.BLOCKED,
            detail="node is recorded BLOCKED",
        )

    if _approval_required(graph, node) and state is not WorkflowNodeState.READY:
        return SchedulerNodeDecision(
            node_id=node.node_id,
            node_state=state,
            reason=SchedulerDecisionReason.WAITING_APPROVAL,
            detail=(
                "approval required and not recorded; the scheduler does not "
                "approve nodes (approval runtime belongs to P3.4)"
            ),
        )

    return SchedulerNodeDecision(
        node_id=node.node_id,
        node_state=state,
        reason=SchedulerDecisionReason.READY,
        detail="all dependencies satisfied",
    )


def calculate_node_decisions(
    graph: WorkflowGraph, run: WorkflowRun
) -> tuple[SchedulerNodeDecision, ...]:
    """Pure readiness calculation in graph node declaration order."""

    _require_matching_graph(graph, run)
    prerequisites = _dependency_map(graph)
    return tuple(
        _decide_node(graph, run, node, prerequisites[node.node_id]) for node in graph.nodes
    )


def _ids_with_reason(
    decisions: tuple[SchedulerNodeDecision, ...], reason: SchedulerDecisionReason
) -> tuple[str, ...]:
    return tuple(decision.node_id for decision in decisions if decision.reason is reason)


def calculate_ready_queue(graph: WorkflowGraph, run: WorkflowRun) -> ReadyQueue:
    """Calculate ready/waiting/blocked nodes. Executes nothing."""

    decisions = calculate_node_decisions(graph, run)
    nodes_by_id = {node.node_id: node for node in graph.nodes}
    schedulable = tuple(
        SchedulableNode(
            node_id=decision.node_id,
            node_type=nodes_by_id[decision.node_id].node_type,
            requires_approval=nodes_by_id[decision.node_id].requires_approval,
            risk_tier=nodes_by_id[decision.node_id].risk_tier,
            reason=decision.reason,
            detail=decision.detail,
            is_execution_grant=False,
            truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
        )
        for decision in decisions
        if decision.reason is SchedulerDecisionReason.READY
    )
    payload = {
        "queue_version": READY_QUEUE_VERSION,
        "run_id": run.run_id,
        "step": run.state.step,
        "decisions": decisions,
    }
    return ReadyQueue(
        queue_version=READY_QUEUE_VERSION,
        run_id=run.run_id,
        graph_id=graph.graph_id,
        step=run.state.step,
        schedulable_nodes=schedulable,
        ready_node_ids=_ids_with_reason(decisions, SchedulerDecisionReason.READY),
        waiting_dependency_node_ids=_ids_with_reason(
            decisions, SchedulerDecisionReason.WAITING_DEPENDENCY
        ),
        waiting_approval_node_ids=_ids_with_reason(
            decisions, SchedulerDecisionReason.WAITING_APPROVAL
        ),
        blocked_node_ids=_ids_with_reason(decisions, SchedulerDecisionReason.BLOCKED),
        running_node_ids=_ids_with_reason(decisions, SchedulerDecisionReason.RUNNING),
        completed_node_ids=_ids_with_reason(decisions, SchedulerDecisionReason.COMPLETED),
        failed_node_ids=_ids_with_reason(decisions, SchedulerDecisionReason.FAILED),
        skipped_node_ids=_ids_with_reason(decisions, SchedulerDecisionReason.SKIPPED),
        unavailable_node_ids=_ids_with_reason(decisions, SchedulerDecisionReason.UNAVAILABLE),
        error_node_ids=_ids_with_reason(decisions, SchedulerDecisionReason.ERROR),
        executes_nothing=True,
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
        queue_hash=stable_hash(payload),
    )


def make_scheduler_decision(graph: WorkflowGraph, run: WorkflowRun) -> SchedulerDecision:
    """Return a readiness decision with explicit reasons. Not a dispatcher."""

    decisions = calculate_node_decisions(graph, run)
    ready_ids = _ids_with_reason(decisions, SchedulerDecisionReason.READY)
    payload = {
        "decision_version": SCHEDULER_DECISION_VERSION,
        "run_id": run.run_id,
        "step": run.state.step,
        "decisions": decisions,
    }
    return SchedulerDecision(
        decision_version=SCHEDULER_DECISION_VERSION,
        run_id=run.run_id,
        graph_id=graph.graph_id,
        step=run.state.step,
        node_decisions=decisions,
        ready_node_ids=ready_ids,
        next_ready_node_id=ready_ids[0] if ready_ids else "",
        is_execution_capability=False,
        executes_nodes=False,
        dispatches_work=False,
        approves_approvals=False,
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
        decision_hash=stable_hash(payload),
    )
