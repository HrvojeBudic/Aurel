"""P3-FLOW-F React/Python hybrid projection + migration readiness tests.

Python runtime is source of truth; React is projection only; a UI replay or
rollback button executes nothing; migration readiness is not migration.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from agentic_runtime.aurel_flow import (
    FORBIDDEN_FLOW_TRUTH_LABELS,
    AurelFlowValidationError,
    CheckpointTimelineEntryViewModel,
    CounterfactualBranchReason,
    GraphRealizationReason,
    ReplayMode,
    ReversibleStateReadinessStatus,
    RuntimeCheckpointKind,
    RuntimeCheckpointReason,
    RuntimeForkReason,
    build_checkpoint_snapshot_view_model,
    build_checkpoint_state_envelope,
    build_checkpoint_timeline_view_model,
    build_counterfactual_branch_view_model,
    build_flow_demo_bundle,
    build_fork_candidate_view_model,
    build_hybrid_serialization_contract,
    build_migration_projection_readiness_matrix,
    build_projection_compatibility_read_model,
    build_python_runtime_source_of_truth,
    build_react_projection_boundary,
    build_recovery_checkpoint_requirement_view_model,
    build_replay_plan_view_model,
    build_reversible_state_migration_readiness,
    build_reversible_state_projection_envelope,
    build_revert_candidate_view_model,
    build_runtime_checkpoint_snapshot,
    build_runtime_diff_view_model,
    build_runtime_state_diff_summary,
    build_runtime_topology_snapshot,
    create_counterfactual_replay_candidate,
    create_recovery_checkpoint_requirement,
    create_runtime_checkpoint_ref,
    create_runtime_fork_candidate,
    create_runtime_replay_plan,
    create_runtime_revert_candidate,
    create_workflow_template,
    realize_runtime_graph,
)


def _reversible_state_fixture():
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
        checkpoint_kind=RuntimeCheckpointKind.BEFORE_RECOVERY,
        checkpoint_reason=RuntimeCheckpointReason.RECOVERY_PREPARATION,
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
    fork = create_runtime_fork_candidate(
        checkpoint_ref=ref,
        snapshot=snapshot,
        fork_reason=RuntimeForkReason.OPERATOR_REVIEW_ALTERNATIVE,
        branch_label="alt",
    )
    plan = create_runtime_replay_plan(
        checkpoint_ref=ref,
        replay_mode=ReplayMode.READ_MODEL_REPLAY,
        included_event_ids=tuple(e.event_id for e in bundle.event_stream.events),
    )
    counterfactual = create_counterfactual_replay_candidate(
        checkpoint_ref=ref,
        branch_reason=CounterfactualBranchReason.OPERATOR_WHAT_IF,
        branch_label="what-if",
    )
    revert = create_runtime_revert_candidate(target_checkpoint=ref)
    diff = build_runtime_state_diff_summary(
        left_envelope=envelope, right_envelope=envelope
    )
    requirement = create_recovery_checkpoint_requirement(run_id=bundle.run.run_id)
    envelope_projection = build_reversible_state_projection_envelope(
        run_id=bundle.run.run_id,
        checkpoint_refs=(ref,),
        checkpoint_snapshots=(snapshot,),
        fork_candidates=(fork,),
        replay_plans=(plan,),
        counterfactual_candidates=(counterfactual,),
        revert_candidates=(revert,),
        runtime_diffs=(diff,),
        recovery_checkpoint_requirements=(requirement,),
    )
    return (
        bundle,
        snapshot,
        fork,
        plan,
        counterfactual,
        revert,
        diff,
        requirement,
        envelope_projection,
    )


def test_projection_envelope_is_read_only_and_grants_no_ui_authority() -> None:
    *_parts, envelope_projection = _reversible_state_fixture()
    assert envelope_projection.read_only is True
    assert envelope_projection.frontend_mutation_allowed is False
    assert envelope_projection.ui_authority_granted is False
    with pytest.raises(AurelFlowValidationError):
        replace(envelope_projection, read_only=False)
    with pytest.raises(AurelFlowValidationError):
        replace(envelope_projection, frontend_mutation_allowed=True)
    with pytest.raises(AurelFlowValidationError):
        replace(envelope_projection, ui_authority_granted=True)


def test_projection_envelope_is_deterministic_and_complete() -> None:
    (
        bundle,
        snapshot,
        fork,
        plan,
        counterfactual,
        revert,
        diff,
        requirement,
        envelope_projection,
    ) = _reversible_state_fixture()
    *_again, envelope_again = _reversible_state_fixture()
    assert envelope_projection.envelope_id == envelope_again.envelope_id
    assert envelope_projection.envelope_hash == envelope_again.envelope_hash
    assert envelope_projection.checkpoint_snapshots == (snapshot,)
    assert envelope_projection.fork_candidates == (fork,)
    assert envelope_projection.replay_plans == (plan,)
    assert envelope_projection.counterfactual_candidates == (counterfactual,)
    assert envelope_projection.revert_candidates == (revert,)
    assert envelope_projection.runtime_diffs == (diff,)
    assert envelope_projection.recovery_checkpoint_requirements == (requirement,)
    assert "frontend" in envelope_projection.unavailable_reasons


def test_all_view_models_are_projection_only() -> None:
    (
        bundle,
        snapshot,
        fork,
        plan,
        counterfactual,
        revert,
        diff,
        requirement,
        _envelope,
    ) = _reversible_state_fixture()
    view_models = (
        build_checkpoint_snapshot_view_model(snapshot),
        build_fork_candidate_view_model(fork),
        build_replay_plan_view_model(plan),
        build_counterfactual_branch_view_model(counterfactual),
        build_revert_candidate_view_model(revert),
        build_runtime_diff_view_model(diff),
        build_recovery_checkpoint_requirement_view_model(requirement),
        build_checkpoint_timeline_view_model(run_id=bundle.run.run_id),
    )
    for view_model in view_models:
        assert view_model.projection_only is True
        with pytest.raises(AurelFlowValidationError):
            replace(view_model, projection_only=False)


def test_timeline_view_model_carries_entries_without_mutating_anything() -> None:
    bundle, *_rest = _reversible_state_fixture()
    entries = (
        CheckpointTimelineEntryViewModel(
            sequence=0, entry_kind="run_created", ref_id=bundle.run.run_id, label="Run"
        ),
        CheckpointTimelineEntryViewModel(
            sequence=1, entry_kind="checkpoint", ref_id="flckp-x", label="Checkpoint"
        ),
    )
    timeline = build_checkpoint_timeline_view_model(
        run_id=bundle.run.run_id, entries=entries
    )
    assert timeline.entries == entries
    with pytest.raises(AurelFlowValidationError):
        replace(timeline, mutation_available=True)


def test_ui_replay_and_rollback_buttons_execute_nothing() -> None:
    (
        _bundle,
        _snapshot,
        _fork,
        plan,
        _counterfactual,
        revert,
        *_rest,
    ) = _reversible_state_fixture()
    replay_view = build_replay_plan_view_model(plan)
    assert replay_view.ui_replay_button_executes is False
    with pytest.raises(AurelFlowValidationError):
        replace(replay_view, ui_replay_button_executes=True)
    revert_view = build_revert_candidate_view_model(revert)
    assert revert_view.ui_rollback_button_executes is False
    assert revert_view.safe_to_execute is False
    with pytest.raises(AurelFlowValidationError):
        replace(revert_view, ui_rollback_button_executes=True)
    with pytest.raises(AurelFlowValidationError):
        replace(revert_view, safe_to_execute=True)


def test_react_projection_boundary_blocks_frontend_authority() -> None:
    boundary = build_react_projection_boundary()
    assert boundary.react_projection_only is True
    assert boundary.future_react_required_for_display_only is True
    for boundary_field in (
        "frontend_mutation_allowed",
        "ui_authority_granted",
        "ui_replay_execution_allowed",
        "ui_rollback_execution_allowed",
    ):
        assert getattr(boundary, boundary_field) is False
        with pytest.raises(AurelFlowValidationError):
            replace(boundary, **{boundary_field: True})
    with pytest.raises(AurelFlowValidationError):
        replace(boundary, react_projection_only=False)


def test_python_runtime_remains_source_of_truth() -> None:
    contract = build_python_runtime_source_of_truth()
    assert contract.runtime_source_of_truth == "python"
    assert contract.python_owns_runtime_state is True
    assert contract.react_owns_runtime_state is False
    assert contract.react_is_projection_only is True
    with pytest.raises(AurelFlowValidationError):
        replace(contract, runtime_source_of_truth="react")
    with pytest.raises(AurelFlowValidationError):
        replace(contract, react_owns_runtime_state=True)
    with pytest.raises(AurelFlowValidationError):
        replace(contract, python_owns_runtime_state=False)


def test_hybrid_serialization_contract_is_ready_without_api_server() -> None:
    contract = build_hybrid_serialization_contract()
    assert contract.deterministic_serialization is True
    assert contract.canonical_json is True
    assert contract.api_contract_ready is True
    assert contract.api_server_implemented is False
    assert contract.generated_schema_tooling is False
    with pytest.raises(AurelFlowValidationError):
        replace(contract, api_server_implemented=True)
    with pytest.raises(AurelFlowValidationError):
        replace(contract, generated_schema_tooling=True)
    with pytest.raises(AurelFlowValidationError):
        replace(contract, deterministic_serialization=False)


def test_migration_readiness_marks_migration_not_started() -> None:
    readiness = build_reversible_state_migration_readiness()
    assert ReversibleStateReadinessStatus.MIGRATION_NOT_STARTED in readiness.statuses
    assert (
        ReversibleStateReadinessStatus.FRONTEND_NOT_IMPLEMENTED in readiness.statuses
    )
    assert (
        ReversibleStateReadinessStatus.PYTHON_SOURCE_OF_TRUTH in readiness.statuses
    )
    for boundary_field in (
        "migration_started",
        "frontend_implemented",
        "rust_core_active",
        "external_store_active",
    ):
        assert getattr(readiness, boundary_field) is False
        with pytest.raises(AurelFlowValidationError):
            replace(readiness, **{boundary_field: True})


def test_migration_projection_readiness_matrix_is_honest() -> None:
    matrix = build_migration_projection_readiness_matrix()
    assert matrix.rows["python_runtime"] == "PYTHON_SOURCE_OF_TRUTH"
    assert matrix.rows["frontend"] == "FRONTEND_NOT_IMPLEMENTED"
    assert matrix.rows["migration"] == "MIGRATION_NOT_STARTED"
    assert matrix.rows["persistence"] == "PERSISTENCE_UNAVAILABLE"
    assert matrix.rows["rust_core"] == "RUST_CORE_NOT_ACTIVE"
    assert matrix.rows["external_store"] == "EXTERNAL_STORE_NOT_ACTIVE"
    assert matrix.python_source_of_truth is True
    with pytest.raises(AurelFlowValidationError):
        replace(matrix, python_source_of_truth=False)
    with pytest.raises(AurelFlowValidationError):
        replace(matrix, migration_started=True)
    with pytest.raises(AurelFlowValidationError):
        replace(matrix, api_server_implemented=True)
    with pytest.raises(AurelFlowValidationError):
        replace(matrix, frontend_implemented=True)


def test_projection_compatibility_read_model() -> None:
    *_parts, envelope_projection = _reversible_state_fixture()
    read_model = build_projection_compatibility_read_model(
        envelope_projection, view_model_count=8
    )
    assert read_model.envelope_id == envelope_projection.envelope_id
    assert read_model.view_model_count == 8
    assert read_model.all_view_models_projection_only is True
    with pytest.raises(AurelFlowValidationError):
        replace(read_model, frontend_mutation_allowed=True)
    with pytest.raises(AurelFlowValidationError):
        replace(read_model, all_view_models_projection_only=False)


def test_no_forbidden_truth_labels_in_projection_outputs() -> None:
    (
        bundle,
        snapshot,
        fork,
        plan,
        counterfactual,
        revert,
        diff,
        requirement,
        envelope_projection,
    ) = _reversible_state_fixture()
    forbidden = {label.value for label in FORBIDDEN_FLOW_TRUTH_LABELS}
    outputs = (
        fork,
        plan,
        counterfactual,
        revert,
        diff,
        requirement,
        envelope_projection,
        build_checkpoint_snapshot_view_model(snapshot),
        build_react_projection_boundary(),
        build_python_runtime_source_of_truth(),
        build_hybrid_serialization_contract(),
        build_reversible_state_migration_readiness(),
        build_migration_projection_readiness_matrix(),
    )
    for output in outputs:
        assert output.truth_label.value not in forbidden
