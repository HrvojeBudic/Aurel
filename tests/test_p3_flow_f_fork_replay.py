"""P3-FLOW-F fork candidate / replay plan / counterfactual tests.

Fork is not execution; a replay plan is not replay execution; a replay
cursor is not a worker cursor; a counterfactual branch is not history.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from agentic_runtime.aurel_flow import (
    AurelFlowValidationError,
    CounterfactualBranchReason,
    GraphRealizationReason,
    ReplayAvailability,
    ReplayMode,
    RuntimeCheckpointKind,
    RuntimeCheckpointReason,
    RuntimeForkReason,
    build_checkpoint_state_envelope,
    build_counterfactual_comparison_frame,
    build_counterfactual_replay_read_model,
    build_counterfactual_truth_boundary,
    build_flow_demo_bundle,
    build_fork_safety_frame,
    build_replay_boundary,
    build_replay_read_model,
    build_runtime_checkpoint_snapshot,
    build_runtime_fork_boundary,
    build_runtime_fork_read_model,
    build_runtime_topology_snapshot,
    create_counterfactual_replay_candidate,
    create_runtime_checkpoint_ref,
    create_runtime_fork_candidate,
    create_runtime_replay_cursor,
    create_runtime_replay_plan,
    create_workflow_template,
    realize_runtime_graph,
)


def _fixture():
    bundle = build_flow_demo_bundle()
    template = create_workflow_template(bundle.graph)
    realized = realize_runtime_graph(
        template=template,
        run=bundle.run,
        realization_reason=GraphRealizationReason.RUN_CREATED,
    )
    topology = build_runtime_topology_snapshot(
        realized_graph=realized, graph=bundle.graph, run=bundle.run
    )
    ref = create_runtime_checkpoint_ref(
        bundle.run,
        checkpoint_kind=RuntimeCheckpointKind.BEFORE_GRAPH_REVISION,
        checkpoint_reason=RuntimeCheckpointReason.FORK_CANDIDATE_PREPARATION,
        created_by="test-operator",
    )
    envelope = build_checkpoint_state_envelope(bundle.run, ref)
    snapshot = build_runtime_checkpoint_snapshot(
        checkpoint_ref=ref,
        run=bundle.run,
        state_envelope=envelope,
        event_stream=bundle.event_stream,
        realized_graph=realized,
        topology_snapshot=topology,
        commitments=bundle.state_commitments,
    )
    return bundle, ref, snapshot


def _fork(ref, snapshot):
    return create_runtime_fork_candidate(
        checkpoint_ref=ref,
        snapshot=snapshot,
        fork_reason=RuntimeForkReason.RECOVERY_EXPLORATION,
        branch_label="recovery-alternative-a",
        expected_divergence_point="fetch",
    )


def test_fork_candidate_is_deterministic() -> None:
    _bundle, ref, snapshot = _fixture()
    fork = _fork(ref, snapshot)
    fork_again = _fork(ref, snapshot)
    assert fork == fork_again
    assert fork.fork_candidate_id.startswith("flfkc-")
    assert fork.topology_snapshot_id == snapshot.topology_snapshot_id


def test_fork_candidate_cannot_spawn_worker_or_duplicate_state() -> None:
    _bundle, ref, snapshot = _fixture()
    fork = _fork(ref, snapshot)
    for boundary_field in (
        "worker_spawned",
        "external_state_duplicated",
        "execution_available",
    ):
        assert getattr(fork, boundary_field) is False
        with pytest.raises(AurelFlowValidationError):
            replace(fork, **{boundary_field: True})


def test_fork_candidate_requires_future_review_execution_proof_authority() -> None:
    _bundle, ref, snapshot = _fixture()
    fork = _fork(ref, snapshot)
    for law_field in (
        "requires_operator_review",
        "requires_permission",
        "requires_future_p4_execution",
        "requires_future_p5_proof",
        "requires_future_p9_authority",
    ):
        assert getattr(fork, law_field) is True
        with pytest.raises(AurelFlowValidationError):
            replace(fork, **{law_field: False})


def test_fork_candidate_rejects_mismatched_snapshot() -> None:
    _bundle, ref, snapshot = _fixture()
    mismatched = replace(snapshot, checkpoint_ref_id="flckp-0000000000000000")
    with pytest.raises(AurelFlowValidationError):
        create_runtime_fork_candidate(
            checkpoint_ref=ref,
            snapshot=mismatched,
            fork_reason=RuntimeForkReason.RECOVERY_EXPLORATION,
            branch_label="bad",
        )


def test_fork_boundary_safety_frame_and_read_model() -> None:
    _bundle, ref, snapshot = _fixture()
    fork = _fork(ref, snapshot)
    boundary = build_runtime_fork_boundary()
    assert boundary.fork_is_not_execution is True
    with pytest.raises(AurelFlowValidationError):
        replace(boundary, fork_spawns_worker=True)
    frame = build_fork_safety_frame(fork)
    assert frame.safe_to_execute is False
    with pytest.raises(AurelFlowValidationError):
        replace(frame, safe_to_execute=True)
    read_model = build_runtime_fork_read_model((fork,))
    assert read_model.fork_candidate_ids == (fork.fork_candidate_id,)
    assert read_model.fork_reason_counts == {"RECOVERY_EXPLORATION": 1}
    with pytest.raises(AurelFlowValidationError):
        replace(read_model, worker_spawned=True)


def test_replay_plan_is_deterministic_with_enumerated_steps() -> None:
    bundle, ref, _snapshot = _fixture()
    event_ids = tuple(event.event_id for event in bundle.event_stream.events)
    plan = create_runtime_replay_plan(
        checkpoint_ref=ref,
        replay_mode=ReplayMode.READ_MODEL_REPLAY,
        included_event_ids=event_ids,
    )
    plan_again = create_runtime_replay_plan(
        checkpoint_ref=ref,
        replay_mode=ReplayMode.READ_MODEL_REPLAY,
        included_event_ids=event_ids,
    )
    assert plan == plan_again
    assert plan.availability is ReplayAvailability.PLAN_ONLY
    assert tuple(step.event_id for step in plan.steps) == event_ids
    assert tuple(step.step_index for step in plan.steps) == tuple(
        range(len(event_ids))
    )


def test_replay_plan_cannot_execute_or_prove() -> None:
    bundle, ref, _snapshot = _fixture()
    plan = create_runtime_replay_plan(
        checkpoint_ref=ref,
        replay_mode=ReplayMode.DIAGNOSTIC_REPLAY_CANDIDATE,
        included_event_ids=tuple(e.event_id for e in bundle.event_stream.events),
    )
    for boundary_field in (
        "execution_available",
        "worker_cursor_available",
        "proof_available",
    ):
        assert getattr(plan, boundary_field) is False
        with pytest.raises(AurelFlowValidationError):
            replace(plan, **{boundary_field: True})
    for law_field in (
        "requires_trace_verification",
        "requires_operator_review",
        "requires_p4_execution",
        "requires_p5_proof",
    ):
        assert getattr(plan, law_field) is True
        with pytest.raises(AurelFlowValidationError):
            replace(plan, **{law_field: False})


def test_replay_availability_is_closed_world() -> None:
    member_names = {member.name for member in ReplayAvailability}
    assert "EXECUTABLE" not in member_names
    assert "LIVE" not in member_names
    assert "EXECUTION" not in member_names


def test_replay_cursor_is_not_a_worker_cursor() -> None:
    bundle, ref, _snapshot = _fixture()
    event_ids = tuple(event.event_id for event in bundle.event_stream.events)
    plan = create_runtime_replay_plan(
        checkpoint_ref=ref,
        replay_mode=ReplayMode.EVENT_SEQUENCE_REPLAY,
        included_event_ids=event_ids,
    )
    cursor = create_runtime_replay_cursor(plan, position_index=1)
    assert cursor.current_event_id == event_ids[1]
    assert cursor.is_worker_cursor is False
    assert cursor.advances_execution is False
    with pytest.raises(AurelFlowValidationError):
        replace(cursor, is_worker_cursor=True)
    with pytest.raises(AurelFlowValidationError):
        replace(cursor, advances_execution=True)


def test_replay_cursor_rejects_out_of_window_position() -> None:
    bundle, ref, _snapshot = _fixture()
    plan = create_runtime_replay_plan(
        checkpoint_ref=ref,
        replay_mode=ReplayMode.READ_MODEL_REPLAY,
        included_event_ids=tuple(e.event_id for e in bundle.event_stream.events),
    )
    with pytest.raises(AurelFlowValidationError):
        create_runtime_replay_cursor(plan, position_index=-1)
    with pytest.raises(AurelFlowValidationError):
        create_runtime_replay_cursor(
            plan, position_index=len(plan.included_event_ids) + 1
        )


def test_replay_boundary_and_read_model() -> None:
    bundle, ref, _snapshot = _fixture()
    boundary = build_replay_boundary()
    assert boundary.replay_plan_is_not_execution is True
    assert boundary.replay_cursor_is_not_worker_cursor is True
    assert boundary.read_model_replay_is_not_trace_replay is True
    with pytest.raises(AurelFlowValidationError):
        replace(boundary, replay_executes=True)
    with pytest.raises(AurelFlowValidationError):
        replace(boundary, replay_proves=True)
    plan = create_runtime_replay_plan(
        checkpoint_ref=ref,
        replay_mode=ReplayMode.READ_MODEL_REPLAY,
        included_event_ids=tuple(e.event_id for e in bundle.event_stream.events),
    )
    read_model = build_replay_read_model((plan,))
    assert read_model.replay_mode_counts == {"READ_MODEL_REPLAY": 1}
    with pytest.raises(AurelFlowValidationError):
        replace(read_model, execution_available=True)


def test_counterfactual_is_structurally_never_actual_history() -> None:
    _bundle, ref, _snapshot = _fixture()
    candidate = create_counterfactual_replay_candidate(
        checkpoint_ref=ref,
        branch_reason=CounterfactualBranchReason.OPERATOR_WHAT_IF,
        branch_label="what-if-gate-rejected",
    )
    assert candidate.counterfactual is True
    assert candidate.actual_history is False
    with pytest.raises(AurelFlowValidationError):
        replace(candidate, actual_history=True)
    with pytest.raises(AurelFlowValidationError):
        replace(candidate, counterfactual=False)
    for boundary_field in ("trace_verified", "proof_available", "execution_available"):
        with pytest.raises(AurelFlowValidationError):
            replace(candidate, **{boundary_field: True})


def test_counterfactual_comparison_frame_cannot_prove_outcome() -> None:
    _bundle, ref, _snapshot = _fixture()
    candidate = create_counterfactual_replay_candidate(
        checkpoint_ref=ref,
        branch_reason=CounterfactualBranchReason.DIAGNOSIS,
        branch_label="diagnostic-branch",
    )
    frame = build_counterfactual_comparison_frame(
        candidate,
        compared_dimensions=("node_states", "event_stream"),
        divergence_summary="gate decision differs",
    )
    assert frame.baseline_checkpoint_id == ref.checkpoint_id
    assert frame.is_actual_history is False
    with pytest.raises(AurelFlowValidationError):
        replace(frame, proves_outcome=True)
    with pytest.raises(AurelFlowValidationError):
        replace(frame, is_actual_history=True)


def test_counterfactual_truth_boundary_and_read_model() -> None:
    _bundle, ref, _snapshot = _fixture()
    boundary = build_counterfactual_truth_boundary()
    assert boundary.counterfactual_is_not_history is True
    assert boundary.counterfactual_is_not_proof is True
    with pytest.raises(AurelFlowValidationError):
        replace(boundary, counterfactual_rewrites_history=True)
    candidate = create_counterfactual_replay_candidate(
        checkpoint_ref=ref,
        branch_reason=CounterfactualBranchReason.RECOVERY_PLANNING,
        branch_label="plan-branch",
    )
    read_model = build_counterfactual_replay_read_model((candidate,))
    assert read_model.branch_reason_counts == {"RECOVERY_PLANNING": 1}
    with pytest.raises(AurelFlowValidationError):
        replace(read_model, proof_available=True)


def test_fork_replay_construction_does_not_mutate_demo_run() -> None:
    bundle, ref, snapshot = _fixture()
    step_before = bundle.run.state.step
    history_before = len(bundle.run.history)
    _fork(ref, snapshot)
    create_runtime_replay_plan(
        checkpoint_ref=ref,
        replay_mode=ReplayMode.READ_MODEL_REPLAY,
        included_event_ids=tuple(e.event_id for e in bundle.event_stream.events),
    )
    create_counterfactual_replay_candidate(
        checkpoint_ref=ref,
        branch_reason=CounterfactualBranchReason.DIAGNOSIS,
        branch_label="no-mutation-check",
    )
    assert bundle.run.state.step == step_before
    assert len(bundle.run.history) == history_before
