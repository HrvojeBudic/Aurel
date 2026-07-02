from __future__ import annotations

import pytest

from agentic_runtime.aurel_flow import (
    AurelFlowErrorCode,
    AurelFlowValidationError,
    SchedulerDecisionReason,
    WorkflowEdge,
    WorkflowNode,
    WorkflowNodeState,
    WorkflowNodeType,
    build_workflow_graph,
    calculate_ready_queue,
    create_workflow_run,
    make_scheduler_decision,
    node_transition,
    transition_workflow_run,
)


def _graph():
    """start -> work -> gate(APPROVAL) -> end."""

    return build_workflow_graph(
        graph_id="g-sched",
        name="scheduler graph",
        nodes=(
            WorkflowNode(node_id="start", node_type=WorkflowNodeType.START),
            WorkflowNode(node_id="work", node_type=WorkflowNodeType.TASK),
            WorkflowNode(
                node_id="gate", node_type=WorkflowNodeType.APPROVAL, requires_approval=True
            ),
            WorkflowNode(node_id="end", node_type=WorkflowNodeType.END),
        ),
        edges=(
            WorkflowEdge(edge_id="e1", from_node_id="start", to_node_id="work"),
            WorkflowEdge(edge_id="e2", from_node_id="work", to_node_id="gate"),
            WorkflowEdge(edge_id="e3", from_node_id="gate", to_node_id="end"),
        ),
        entry_node_ids=("start",),
        exit_node_ids=("end",),
    )


def _mark(run, node_id: str, *states: WorkflowNodeState):
    current = run.state.node_states[node_id]
    for state in states:
        run = transition_workflow_run(run, node_transition(node_id, current, state))
        current = state
    return run


def _reason_map(graph, run) -> dict[str, SchedulerDecisionReason]:
    decision = make_scheduler_decision(graph, run)
    return {d.node_id: d.reason for d in decision.node_decisions}


def test_entry_node_is_initially_ready_and_dependents_wait() -> None:
    graph = _graph()
    run = create_workflow_run(graph)
    reasons = _reason_map(graph, run)

    assert reasons["start"] is SchedulerDecisionReason.READY
    assert reasons["work"] is SchedulerDecisionReason.WAITING_DEPENDENCY
    assert reasons["gate"] is SchedulerDecisionReason.WAITING_DEPENDENCY
    assert reasons["end"] is SchedulerDecisionReason.WAITING_DEPENDENCY


def test_completed_prerequisite_unlocks_next_node() -> None:
    graph = _graph()
    run = create_workflow_run(graph)

    before = _reason_map(graph, run)
    assert before["work"] is SchedulerDecisionReason.WAITING_DEPENDENCY

    run = _mark(
        run,
        "start",
        WorkflowNodeState.READY,
        WorkflowNodeState.RUNNING,
        WorkflowNodeState.COMPLETED,
    )
    after = _reason_map(graph, run)

    assert after["start"] is SchedulerDecisionReason.COMPLETED
    assert after["work"] is SchedulerDecisionReason.READY


def test_approval_node_waits_and_scheduler_does_not_approve_itself() -> None:
    graph = _graph()
    run = create_workflow_run(graph)
    for node_id in ("start", "work"):
        run = _mark(
            run,
            node_id,
            WorkflowNodeState.READY,
            WorkflowNodeState.RUNNING,
            WorkflowNodeState.COMPLETED,
        )

    first = make_scheduler_decision(graph, run)
    second = make_scheduler_decision(graph, run)
    reasons = {d.node_id: d for d in first.node_decisions}

    assert reasons["gate"].reason is SchedulerDecisionReason.WAITING_APPROVAL
    assert "does not approve" in reasons["gate"].detail
    # Deciding twice never flips the approval state: the scheduler is pure.
    assert first.node_decisions == second.node_decisions
    assert run.state.node_states["gate"] is WorkflowNodeState.NOT_STARTED

    # Only an explicit recorded approval mark makes the gate ready.
    run = _mark(run, "gate", WorkflowNodeState.WAITING_APPROVAL, WorkflowNodeState.READY)
    approved = _reason_map(graph, run)

    assert approved["gate"] is SchedulerDecisionReason.READY


def test_failed_prerequisite_blocks_dependent_node() -> None:
    graph = _graph()
    run = create_workflow_run(graph)
    run = _mark(
        run,
        "start",
        WorkflowNodeState.READY,
        WorkflowNodeState.RUNNING,
        WorkflowNodeState.COMPLETED,
    )
    run = _mark(
        run,
        "work",
        WorkflowNodeState.READY,
        WorkflowNodeState.RUNNING,
        WorkflowNodeState.FAILED,
    )
    decision = make_scheduler_decision(graph, run)
    reasons = {d.node_id: d for d in decision.node_decisions}

    assert reasons["work"].reason is SchedulerDecisionReason.FAILED
    assert reasons["gate"].reason is SchedulerDecisionReason.BLOCKED
    assert "work" in reasons["gate"].detail


def test_unavailable_node_is_labeled_unavailable() -> None:
    graph = build_workflow_graph(
        graph_id="g-unavail",
        name="unavailable graph",
        nodes=(
            WorkflowNode(node_id="start", node_type=WorkflowNodeType.START),
            WorkflowNode(node_id="future", node_type=WorkflowNodeType.UNAVAILABLE),
            WorkflowNode(node_id="end", node_type=WorkflowNodeType.END),
        ),
        edges=(
            WorkflowEdge(edge_id="e1", from_node_id="start", to_node_id="future"),
            WorkflowEdge(edge_id="e2", from_node_id="future", to_node_id="end"),
        ),
        entry_node_ids=("start",),
        exit_node_ids=("end",),
    )
    run = create_workflow_run(graph)
    reasons = _reason_map(graph, run)

    assert reasons["future"] is SchedulerDecisionReason.UNAVAILABLE

    # A recorded UNAVAILABLE prerequisite blocks the dependent with a reason.
    run = _mark(run, "future", WorkflowNodeState.UNAVAILABLE)
    decision = make_scheduler_decision(graph, run)
    blocked = {d.node_id: d for d in decision.node_decisions}

    assert blocked["end"].reason is SchedulerDecisionReason.BLOCKED
    assert "unavailable" in blocked["end"].detail


def test_every_decision_has_explicit_reason_and_detail() -> None:
    graph = _graph()
    run = create_workflow_run(graph)
    decision = make_scheduler_decision(graph, run)

    assert len(decision.node_decisions) == len(graph.nodes)
    assert all(d.reason for d in decision.node_decisions)
    assert all(d.detail for d in decision.node_decisions)
    assert decision.next_ready_node_id == "start"


def test_ready_queue_buckets_and_hash_are_deterministic() -> None:
    graph = _graph()
    run = create_workflow_run(graph)
    queue_a = calculate_ready_queue(graph, run)
    queue_b = calculate_ready_queue(graph, run)

    assert queue_a.ready_node_ids == ("start",)
    assert queue_a.waiting_dependency_node_ids == ("work", "gate", "end")
    assert queue_a.blocked_node_ids == ()
    assert [node.node_id for node in queue_a.schedulable_nodes] == ["start"]
    assert queue_a.queue_hash == queue_b.queue_hash
    assert queue_a.executes_nothing is True

    moved = _mark(
        run,
        "start",
        WorkflowNodeState.READY,
        WorkflowNodeState.RUNNING,
        WorkflowNodeState.COMPLETED,
    )
    queue_moved = calculate_ready_queue(graph, moved)

    assert queue_moved.queue_hash != queue_a.queue_hash
    assert queue_moved.completed_node_ids == ("start",)
    assert queue_moved.ready_node_ids == ("work",)


def test_scheduler_rejects_mismatched_graph_and_run() -> None:
    graph = _graph()
    other_graph = build_workflow_graph(
        graph_id="g-other",
        name="other graph",
        nodes=(WorkflowNode(node_id="only", node_type=WorkflowNodeType.START),),
        entry_node_ids=("only",),
        exit_node_ids=("only",),
    )
    run = create_workflow_run(graph)

    with pytest.raises(AurelFlowValidationError) as excinfo:
        make_scheduler_decision(other_graph, run)

    assert excinfo.value.code is AurelFlowErrorCode.GRAPH_RUN_MISMATCH
