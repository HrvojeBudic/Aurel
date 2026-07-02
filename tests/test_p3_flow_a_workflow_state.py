from __future__ import annotations

import pytest

from agentic_runtime.aurel_flow import (
    AurelFlowErrorCode,
    AurelFlowValidationError,
    PERSISTENCE_LABEL_UNAVAILABLE,
    WorkflowEdge,
    WorkflowLifecycleStatus,
    WorkflowNode,
    WorkflowNodeState,
    WorkflowNodeType,
    build_workflow_graph,
    create_workflow_run,
    lifecycle_transition,
    node_transition,
    snapshot_workflow_state,
    transition_workflow_run,
    validate_workflow_state_transition,
)


def _graph():
    return build_workflow_graph(
        graph_id="g-state",
        name="state graph",
        nodes=(
            WorkflowNode(node_id="start", node_type=WorkflowNodeType.START),
            WorkflowNode(node_id="work", node_type=WorkflowNodeType.TASK),
            WorkflowNode(node_id="end", node_type=WorkflowNodeType.END),
        ),
        edges=(
            WorkflowEdge(edge_id="e1", from_node_id="start", to_node_id="work"),
            WorkflowEdge(edge_id="e2", from_node_id="work", to_node_id="end"),
        ),
        entry_node_ids=("start",),
        exit_node_ids=("end",),
    )


def _invalid_graph():
    return build_workflow_graph(
        graph_id="g-broken",
        name="broken graph",
        nodes=(
            WorkflowNode(node_id="a", node_type=WorkflowNodeType.TASK),
            WorkflowNode(node_id="a", node_type=WorkflowNodeType.TASK),
        ),
        entry_node_ids=("a",),
        exit_node_ids=("a",),
    )


def test_run_created_from_valid_graph_with_deterministic_initial_state() -> None:
    graph = _graph()
    run = create_workflow_run(graph, run_key="run-42")
    rerun = create_workflow_run(graph, run_key="run-42")
    other = create_workflow_run(graph, run_key="run-43")

    assert run.run_id == rerun.run_id
    assert run.run_id != other.run_id
    assert run.graph_hash == graph.graph_hash
    assert run.state.lifecycle_status is WorkflowLifecycleStatus.CREATED
    assert run.state.step == 0
    assert run.history == ()
    assert set(run.state.node_states) == {"start", "work", "end"}
    assert all(
        state is WorkflowNodeState.NOT_STARTED for state in run.state.node_states.values()
    )


def test_run_cannot_be_created_from_invalid_graph() -> None:
    with pytest.raises(AurelFlowValidationError) as excinfo:
        create_workflow_run(_invalid_graph())

    assert excinfo.value.code is AurelFlowErrorCode.INVALID_GRAPH


def test_safe_lifecycle_transitions_pass() -> None:
    run = create_workflow_run(_graph())
    run = transition_workflow_run(
        run,
        lifecycle_transition(WorkflowLifecycleStatus.CREATED, WorkflowLifecycleStatus.READY),
    )
    run = transition_workflow_run(
        run,
        lifecycle_transition(WorkflowLifecycleStatus.READY, WorkflowLifecycleStatus.RUNNING),
    )
    run = transition_workflow_run(
        run,
        lifecycle_transition(
            WorkflowLifecycleStatus.RUNNING, WorkflowLifecycleStatus.COMPLETED
        ),
    )

    assert run.state.lifecycle_status is WorkflowLifecycleStatus.COMPLETED
    assert run.state.step == 3
    assert len(run.history) == 3


def test_invalid_lifecycle_transition_fails_closed() -> None:
    run = create_workflow_run(_graph())

    with pytest.raises(AurelFlowValidationError) as excinfo:
        transition_workflow_run(
            run,
            lifecycle_transition(
                WorkflowLifecycleStatus.CREATED, WorkflowLifecycleStatus.RUNNING
            ),
        )

    assert excinfo.value.code is AurelFlowErrorCode.INVALID_LIFECYCLE_TRANSITION


def test_completed_workflow_cannot_return_to_running() -> None:
    run = create_workflow_run(_graph())
    for from_status, to_status in (
        (WorkflowLifecycleStatus.CREATED, WorkflowLifecycleStatus.READY),
        (WorkflowLifecycleStatus.READY, WorkflowLifecycleStatus.RUNNING),
        (WorkflowLifecycleStatus.RUNNING, WorkflowLifecycleStatus.COMPLETED),
    ):
        run = transition_workflow_run(run, lifecycle_transition(from_status, to_status))

    with pytest.raises(AurelFlowValidationError) as excinfo:
        transition_workflow_run(
            run,
            lifecycle_transition(
                WorkflowLifecycleStatus.COMPLETED, WorkflowLifecycleStatus.RUNNING
            ),
        )

    assert excinfo.value.code is AurelFlowErrorCode.TERMINAL_LIFECYCLE_STATE


def test_stale_transition_source_fails_closed() -> None:
    run = create_workflow_run(_graph())
    result = validate_workflow_state_transition(
        run,
        lifecycle_transition(WorkflowLifecycleStatus.READY, WorkflowLifecycleStatus.RUNNING),
    )

    assert result.valid is False
    assert any(
        issue.code is AurelFlowErrorCode.STALE_TRANSITION_SOURCE for issue in result.issues
    )


def test_safe_node_transitions_pass_and_runs_are_immutable() -> None:
    original = create_workflow_run(_graph())
    run = transition_workflow_run(
        original,
        node_transition("start", WorkflowNodeState.NOT_STARTED, WorkflowNodeState.READY),
    )
    run = transition_workflow_run(
        run, node_transition("start", WorkflowNodeState.READY, WorkflowNodeState.RUNNING)
    )
    run = transition_workflow_run(
        run, node_transition("start", WorkflowNodeState.RUNNING, WorkflowNodeState.COMPLETED)
    )

    assert run.state.node_states["start"] is WorkflowNodeState.COMPLETED
    assert run.state.step == 3
    assert original.state.node_states["start"] is WorkflowNodeState.NOT_STARTED
    assert original.state.step == 0


def test_invalid_node_transition_and_unknown_target_fail_closed() -> None:
    run = create_workflow_run(_graph())

    with pytest.raises(AurelFlowValidationError) as skipped_states:
        transition_workflow_run(
            run,
            node_transition(
                "start", WorkflowNodeState.NOT_STARTED, WorkflowNodeState.COMPLETED
            ),
        )
    with pytest.raises(AurelFlowValidationError) as unknown_target:
        transition_workflow_run(
            run,
            node_transition("ghost", WorkflowNodeState.NOT_STARTED, WorkflowNodeState.READY),
        )

    assert skipped_states.value.code is AurelFlowErrorCode.INVALID_NODE_TRANSITION
    assert unknown_target.value.code is AurelFlowErrorCode.UNKNOWN_TRANSITION_TARGET


def test_terminal_node_state_rejects_further_transitions() -> None:
    run = create_workflow_run(_graph())
    run = transition_workflow_run(
        run,
        node_transition("work", WorkflowNodeState.NOT_STARTED, WorkflowNodeState.SKIPPED),
    )

    with pytest.raises(AurelFlowValidationError) as excinfo:
        transition_workflow_run(
            run, node_transition("work", WorkflowNodeState.SKIPPED, WorkflowNodeState.READY)
        )

    assert excinfo.value.code is AurelFlowErrorCode.TERMINAL_NODE_STATE


def test_snapshot_covers_all_nodes_and_is_deterministic() -> None:
    graph = _graph()
    run = create_workflow_run(graph, run_key="snap-run")
    snapshot_a = snapshot_workflow_state(run)
    snapshot_b = snapshot_workflow_state(create_workflow_run(graph, run_key="snap-run"))

    assert set(snapshot_a.node_states) == {node.node_id for node in graph.nodes}
    assert snapshot_a.snapshot_hash == snapshot_b.snapshot_hash
    assert snapshot_a.step == 0
    assert snapshot_a.transition_count == 0

    moved = transition_workflow_run(
        run,
        node_transition("start", WorkflowNodeState.NOT_STARTED, WorkflowNodeState.READY),
    )
    snapshot_moved = snapshot_workflow_state(moved)

    assert snapshot_moved.snapshot_hash != snapshot_a.snapshot_hash
    assert snapshot_moved.step == 1
    assert snapshot_moved.transition_count == 1


def test_persistence_truth_is_honest() -> None:
    run = create_workflow_run(_graph())
    snapshot = snapshot_workflow_state(run)

    assert run.persisted is False
    assert run.persistence_label == PERSISTENCE_LABEL_UNAVAILABLE
    assert "in-memory only" in run.persistence_reason
    assert snapshot.persisted is False
    assert snapshot.persistence_label == PERSISTENCE_LABEL_UNAVAILABLE


def test_empty_run_key_fails_closed() -> None:
    with pytest.raises(AurelFlowValidationError) as excinfo:
        create_workflow_run(_graph(), run_key="")

    assert excinfo.value.code is AurelFlowErrorCode.EMPTY_RUN_KEY
