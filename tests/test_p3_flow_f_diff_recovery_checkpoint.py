"""P3-FLOW-F runtime diff / recovery checkpoint requirement tests.

A diff is a deterministic comparison — never proof, never replay, never
rollback. A recovery checkpoint requirement requires; it never executes
recovery, and a post-recovery comparison expectation is not verification.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from agentic_runtime.aurel_flow import (
    AurelFlowValidationError,
    GraphRealizationReason,
    RuntimeCheckpointKind,
    RuntimeCheckpointReason,
    WorkflowLifecycleStatus,
    WorkflowNodeState,
    build_checkpoint_diff_frame,
    build_checkpoint_state_envelope,
    build_commitment_diff_frame,
    build_diff_read_model,
    build_diff_truth_boundary,
    build_event_stream_diff_frame,
    build_flow_demo_bundle,
    build_post_recovery_comparison_frame,
    build_pre_recovery_checkpoint_ref,
    build_recovery_checkpoint_boundary,
    build_recovery_checkpoint_read_model,
    build_recovery_state_preservation_frame,
    build_runtime_state_diff_summary,
    build_runtime_topology_snapshot,
    build_topology_diff_frame,
    create_recovery_checkpoint_requirement,
    create_runtime_checkpoint_ref,
    create_workflow_run,
    create_workflow_template,
    lifecycle_transition,
    node_transition,
    realize_runtime_graph,
    transition_workflow_run,
)


def _two_state_points():
    """One run captured at two different state points (same run_id)."""

    bundle = build_flow_demo_bundle()
    early_run = create_workflow_run(bundle.graph, run_key="diff-run-0001")
    left_ref = create_runtime_checkpoint_ref(
        early_run,
        checkpoint_kind=RuntimeCheckpointKind.RUN_CREATED,
        checkpoint_reason=RuntimeCheckpointReason.SCHEDULED_BOUNDARY,
        created_by="test-operator",
    )
    left_envelope = build_checkpoint_state_envelope(early_run, left_ref)

    later_run = transition_workflow_run(
        early_run,
        lifecycle_transition(
            WorkflowLifecycleStatus.CREATED, WorkflowLifecycleStatus.READY, "test"
        ),
    )
    later_run = transition_workflow_run(
        later_run,
        node_transition(
            "start", WorkflowNodeState.NOT_STARTED, WorkflowNodeState.READY, "test"
        ),
    )
    right_ref = create_runtime_checkpoint_ref(
        later_run,
        checkpoint_kind=RuntimeCheckpointKind.MANUAL_OPERATOR_MARKER,
        checkpoint_reason=RuntimeCheckpointReason.DIAGNOSTIC_MARKER,
        created_by="test-operator",
    )
    right_envelope = build_checkpoint_state_envelope(later_run, right_ref)
    return bundle, left_ref, left_envelope, right_ref, right_envelope


def _diff():
    bundle, left_ref, left_env, right_ref, right_env = _two_state_points()
    diff = build_runtime_state_diff_summary(
        left_envelope=left_env,
        right_envelope=right_env,
        left_event_ids=("rtev-a", "rtev-b"),
        right_event_ids=("rtev-b", "rtev-c"),
        left_commitment_ids=("rtsc-1",),
        right_commitment_ids=("rtsc-2",),
    )
    return bundle, left_env, right_env, diff


def test_diff_is_deterministic() -> None:
    _b1, _l1, _r1, diff = _diff()
    _b2, _l2, _r2, diff_again = _diff()
    assert diff == diff_again
    assert diff.diff_id.startswith("fldif-")
    assert diff.diff_hash == diff_again.diff_hash


def test_diff_computes_node_changes() -> None:
    _bundle, _left, _right, diff = _diff()
    # Same graph, so no nodes added/removed; "start" changed NOT_STARTED->READY.
    assert diff.added_node_ids == ()
    assert diff.removed_node_ids == ()
    assert diff.changed_node_ids == ("start",)


def test_diff_computes_event_and_commitment_changes() -> None:
    _bundle, _left, _right, diff = _diff()
    assert diff.added_event_ids == ("rtev-c",)
    assert diff.omitted_event_ids == ("rtev-a",)
    assert diff.changed_commitment_ids == ("rtsc-1", "rtsc-2")


def test_diff_with_identical_topology_reports_no_edge_changes() -> None:
    bundle, left_ref, left_env, _right_ref, right_env = _two_state_points()
    template = create_workflow_template(bundle.graph)
    realized = realize_runtime_graph(
        template=template,
        run=bundle.run,
        realization_reason=GraphRealizationReason.RUN_CREATED,
    )
    topology = build_runtime_topology_snapshot(
        realized_graph=realized, graph=bundle.graph, run=bundle.run
    )
    diff = build_runtime_state_diff_summary(
        left_envelope=left_env,
        right_envelope=right_env,
        left_topology=topology,
        right_topology=topology,
    )
    assert diff.added_edge_ids == ()
    assert diff.removed_edge_ids == ()
    assert diff.changed_edge_ids == ()
    assert diff.left_topology_snapshot_id == topology.snapshot_id


def test_diff_rejects_envelopes_from_different_runs() -> None:
    bundle, left_ref, left_env, _right_ref, _right_env = _two_state_points()
    other_run = create_workflow_run(bundle.graph, run_key="a-third-run-key")
    other_ref = create_runtime_checkpoint_ref(
        other_run,
        checkpoint_kind=RuntimeCheckpointKind.RUN_CREATED,
        checkpoint_reason=RuntimeCheckpointReason.SCHEDULED_BOUNDARY,
        created_by="test-operator",
    )
    other_env = build_checkpoint_state_envelope(other_run, other_ref)
    with pytest.raises(AurelFlowValidationError):
        build_runtime_state_diff_summary(
            left_envelope=left_env, right_envelope=other_env
        )


def test_diff_cannot_claim_proof() -> None:
    _bundle, _left, _right, diff = _diff()
    assert diff.proof_available is False
    assert diff.trace_verified is False
    with pytest.raises(AurelFlowValidationError):
        replace(diff, proof_available=True)
    with pytest.raises(AurelFlowValidationError):
        replace(diff, trace_verified=True)


def test_diff_frames_summarize_each_dimension() -> None:
    _bundle, left_env, right_env, diff = _diff()
    checkpoint_frame = build_checkpoint_diff_frame(
        diff, left_envelope=left_env, right_envelope=right_env
    )
    assert checkpoint_frame.step_delta == right_env.step - left_env.step
    assert checkpoint_frame.lifecycle_changed is True
    assert checkpoint_frame.node_change_count == 1
    topology_frame = build_topology_diff_frame(diff)
    assert topology_frame.edge_change_count == 0
    event_frame = build_event_stream_diff_frame(diff)
    assert event_frame.added_event_count == 1
    assert event_frame.omitted_event_count == 1
    commitment_frame = build_commitment_diff_frame(diff)
    assert commitment_frame.changed_commitment_count == 2
    for frame in (checkpoint_frame, topology_frame, event_frame, commitment_frame):
        with pytest.raises(AurelFlowValidationError):
            replace(frame, proof_available=True)


def test_diff_read_model_and_truth_boundary() -> None:
    _bundle, _left, _right, diff = _diff()
    read_model = build_diff_read_model(diff)
    assert read_model.total_change_count == 5  # 1 node + 2 events + 2 commitments
    assert read_model.diff_is_not_proof is True
    with pytest.raises(AurelFlowValidationError):
        replace(read_model, diff_is_not_rollback=False)
    boundary = build_diff_truth_boundary()
    assert boundary.diff_is_not_replay is True
    with pytest.raises(AurelFlowValidationError):
        replace(boundary, diff_proves_correctness=True)


def test_recovery_requirement_requires_but_never_executes() -> None:
    bundle = build_flow_demo_bundle()
    requirement = create_recovery_checkpoint_requirement(run_id=bundle.run.run_id)
    assert requirement.required_checkpoint_kind is (
        RuntimeCheckpointKind.BEFORE_RECOVERY
    )
    for law_field in (
        "pre_recovery_checkpoint_required",
        "post_recovery_comparison_required",
        "state_preservation_required",
        "requires_operator_review",
        "requires_p4_execution_for_repair",
        "requires_p5_proof_for_verification",
        "requires_p9_authority_if_irreversible",
    ):
        assert getattr(requirement, law_field) is True
        with pytest.raises(AurelFlowValidationError):
            replace(requirement, **{law_field: False})
    with pytest.raises(AurelFlowValidationError):
        replace(requirement, recovery_executed=True)
    with pytest.raises(AurelFlowValidationError):
        replace(requirement, verification_available=True)


def test_pre_recovery_checkpoint_ref_matches_requirement_kind() -> None:
    bundle = build_flow_demo_bundle()
    requirement = create_recovery_checkpoint_requirement(run_id=bundle.run.run_id)
    matching_ref = create_runtime_checkpoint_ref(
        bundle.run,
        checkpoint_kind=RuntimeCheckpointKind.BEFORE_RECOVERY,
        checkpoint_reason=RuntimeCheckpointReason.RECOVERY_PREPARATION,
        created_by="test-operator",
    )
    bound = build_pre_recovery_checkpoint_ref(requirement, matching_ref)
    assert bound.satisfies_requirement is True
    other_ref = create_runtime_checkpoint_ref(
        bundle.run,
        checkpoint_kind=RuntimeCheckpointKind.AFTER_PAUSE,
        checkpoint_reason=RuntimeCheckpointReason.DIAGNOSTIC_MARKER,
        created_by="test-operator",
    )
    unbound = build_pre_recovery_checkpoint_ref(requirement, other_ref)
    assert unbound.satisfies_requirement is False
    with pytest.raises(AurelFlowValidationError):
        replace(bound, recovery_executed=True)


def test_pre_recovery_checkpoint_ref_rejects_mismatched_run() -> None:
    bundle = build_flow_demo_bundle()
    requirement = create_recovery_checkpoint_requirement(run_id=bundle.run.run_id)
    other_run = create_workflow_run(bundle.graph, run_key="recovery-other-run")
    other_ref = create_runtime_checkpoint_ref(
        other_run,
        checkpoint_kind=RuntimeCheckpointKind.BEFORE_RECOVERY,
        checkpoint_reason=RuntimeCheckpointReason.RECOVERY_PREPARATION,
        created_by="test-operator",
    )
    with pytest.raises(AurelFlowValidationError):
        build_pre_recovery_checkpoint_ref(requirement, other_ref)


def test_post_recovery_comparison_expectation_is_not_verification() -> None:
    bundle = build_flow_demo_bundle()
    requirement = create_recovery_checkpoint_requirement(run_id=bundle.run.run_id)
    frame = build_post_recovery_comparison_frame(requirement)
    assert frame.comparison_expected is True
    assert frame.comparison_is_not_verification is True
    with pytest.raises(AurelFlowValidationError):
        replace(frame, comparison_is_not_verification=False)
    with pytest.raises(AurelFlowValidationError):
        replace(frame, verification_available=True)
    with pytest.raises(AurelFlowValidationError):
        replace(frame, proof_available=True)


def test_recovery_state_preservation_frame_is_local_only() -> None:
    bundle = build_flow_demo_bundle()
    requirement = create_recovery_checkpoint_requirement(run_id=bundle.run.run_id)
    ref = create_runtime_checkpoint_ref(
        bundle.run,
        checkpoint_kind=RuntimeCheckpointKind.BEFORE_RECOVERY,
        checkpoint_reason=RuntimeCheckpointReason.RECOVERY_PREPARATION,
        created_by="test-operator",
    )
    pre_recovery = build_pre_recovery_checkpoint_ref(requirement, ref)
    frame = build_recovery_state_preservation_frame(requirement, pre_recovery)
    assert frame.pre_recovery_checkpoint_id == ref.checkpoint_id
    assert frame.preservation_is_local_only is True
    with pytest.raises(AurelFlowValidationError):
        replace(frame, external_persistence=True)
    with pytest.raises(AurelFlowValidationError):
        replace(frame, recovery_executed=True)
    other_requirement = create_recovery_checkpoint_requirement(
        run_id=bundle.run.run_id, failure_or_recovery_candidate_id="other"
    )
    with pytest.raises(AurelFlowValidationError):
        build_recovery_state_preservation_frame(other_requirement, pre_recovery)


def test_recovery_boundary_and_read_model() -> None:
    bundle = build_flow_demo_bundle()
    boundary = build_recovery_checkpoint_boundary()
    assert boundary.requirement_is_not_recovery_execution is True
    assert boundary.comparison_expectation_is_not_verification is True
    with pytest.raises(AurelFlowValidationError):
        replace(boundary, recovery_executes=True)
    with pytest.raises(AurelFlowValidationError):
        replace(boundary, recovery_verified=True)
    requirement = create_recovery_checkpoint_requirement(run_id=bundle.run.run_id)
    read_model = build_recovery_checkpoint_read_model((requirement,))
    assert read_model.requirement_ids == (requirement.requirement_id,)
    with pytest.raises(AurelFlowValidationError):
        replace(read_model, recovery_executed=True)
