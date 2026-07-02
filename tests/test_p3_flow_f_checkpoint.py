"""P3-FLOW-F checkpoint reference / snapshot / state envelope tests.

A checkpoint names a runtime state point; it is not persistence, not Trace,
not Ledger, not proof, and not execution.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from agentic_runtime.aurel_flow import (
    AurelFlowValidationError,
    CheckpointTruthLabel,
    GraphRealizationReason,
    RuntimeCheckpointKind,
    RuntimeCheckpointReason,
    build_checkpoint_serialization_contract,
    build_checkpoint_state_envelope,
    build_flow_demo_bundle,
    build_runtime_checkpoint_boundary,
    build_runtime_checkpoint_snapshot,
    build_runtime_checkpoint_snapshot_read_model,
    build_runtime_topology_snapshot,
    create_runtime_checkpoint_ref,
    create_workflow_run,
    create_workflow_template,
    realize_runtime_graph,
    runtime_checkpoint_snapshot_ref,
)


def _checkpoint_fixture():
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
        source_topology_snapshot_id=topology.snapshot_id,
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
    return bundle, realized, topology, ref, envelope, snapshot


def test_checkpoint_ref_is_deterministic() -> None:
    _bundle, _realized, topology, ref, _envelope, _snapshot = _checkpoint_fixture()
    _b2, _r2, _t2, ref_again, _e2, _s2 = _checkpoint_fixture()
    assert ref.checkpoint_id == ref_again.checkpoint_id
    assert ref == ref_again
    assert ref.checkpoint_id.startswith("flckp-")
    assert ref.source_topology_snapshot_id == topology.snapshot_id


def test_checkpoint_ref_logical_sequence_is_run_step_not_wall_clock() -> None:
    bundle, _realized, _topology, ref, _envelope, _snapshot = _checkpoint_fixture()
    assert ref.created_at_logical_sequence == bundle.run.state.step


def test_checkpoint_ref_cannot_claim_persistence_trace_ledger_or_execution() -> None:
    _bundle, _realized, _topology, ref, _envelope, _snapshot = _checkpoint_fixture()
    for boundary_field in (
        "persisted",
        "external_persistence",
        "trace_verified",
        "ledger_written",
        "execution_available",
    ):
        assert getattr(ref, boundary_field) is False
        with pytest.raises(AurelFlowValidationError):
            replace(ref, **{boundary_field: True})


def test_checkpoint_truth_label_is_closed_world() -> None:
    member_names = {label.name for label in CheckpointTruthLabel}
    assert "LIVE" not in member_names
    assert "TRACE_VERIFIED" not in member_names


def test_checkpoint_boundary_laws_fail_closed() -> None:
    boundary = build_runtime_checkpoint_boundary()
    assert boundary.checkpoint_is_not_persistence is True
    assert boundary.checkpoint_is_not_trace is True
    assert boundary.checkpoint_is_not_proof is True
    with pytest.raises(AurelFlowValidationError):
        replace(boundary, checkpoint_is_not_persistence=False)
    with pytest.raises(AurelFlowValidationError):
        replace(boundary, checkpoint_writes_trace=True)
    with pytest.raises(AurelFlowValidationError):
        replace(boundary, checkpoint_writes_ledger=True)
    with pytest.raises(AurelFlowValidationError):
        replace(boundary, checkpoint_executes=True)


def test_state_envelope_captures_run_state_read_only() -> None:
    bundle, _realized, _topology, _ref, envelope, _snapshot = _checkpoint_fixture()
    assert envelope.step == bundle.run.state.step
    assert envelope.lifecycle_status == bundle.run.state.lifecycle_status.value
    assert envelope.node_states == {
        node_id: state.value
        for node_id, state in bundle.run.state.node_states.items()
    }
    assert envelope.read_only is True
    with pytest.raises(AurelFlowValidationError):
        replace(envelope, read_only=False)
    with pytest.raises(AurelFlowValidationError):
        replace(envelope, mutation_available=True)
    with pytest.raises(AurelFlowValidationError):
        replace(envelope, external_persistence=True)


def test_state_envelope_rejects_mismatched_run() -> None:
    bundle, _realized, _topology, ref, _envelope, _snapshot = _checkpoint_fixture()
    other_run = create_workflow_run(bundle.graph, run_key="a-different-run-key")
    assert other_run.run_id != ref.run_id
    with pytest.raises(AurelFlowValidationError):
        build_checkpoint_state_envelope(other_run, ref)


def test_snapshot_binds_run_event_commitment_graph_and_topology() -> None:
    bundle, realized, topology, ref, envelope, snapshot = _checkpoint_fixture()
    assert snapshot.run_id == bundle.run.run_id
    assert snapshot.checkpoint_ref_id == ref.checkpoint_id
    assert snapshot.state_envelope_id == envelope.state_envelope_id
    assert snapshot.runtime_event_stream_id == bundle.event_stream.stream_id
    assert snapshot.realized_graph_id == realized.realized_graph_id
    assert snapshot.topology_snapshot_id == topology.snapshot_id
    assert snapshot.topology_version_number == topology.topology_version.version_number
    assert snapshot.event_count == len(bundle.event_stream.events)
    assert snapshot.commitment_count == len(bundle.state_commitments)
    assert snapshot.node_state_count == len(bundle.run.state.node_states)


def test_snapshot_is_deterministic() -> None:
    _b1, _r1, _t1, _ref1, _e1, snapshot = _checkpoint_fixture()
    _b2, _r2, _t2, _ref2, _e2, snapshot_again = _checkpoint_fixture()
    assert snapshot.snapshot_id == snapshot_again.snapshot_id
    assert snapshot.snapshot_hash == snapshot_again.snapshot_hash


def test_snapshot_cannot_claim_persistence_or_proof() -> None:
    _bundle, _realized, _topology, _ref, _envelope, snapshot = _checkpoint_fixture()
    for boundary_field in (
        "persisted",
        "external_persistence",
        "proof_available",
        "trace_verified",
    ):
        assert getattr(snapshot, boundary_field) is False
        with pytest.raises(AurelFlowValidationError):
            replace(snapshot, **{boundary_field: True})


def test_snapshot_rejects_mismatched_run_and_graph() -> None:
    bundle, realized, topology, ref, envelope, _snapshot = _checkpoint_fixture()
    other_run = create_workflow_run(bundle.graph, run_key="another-run-key")
    with pytest.raises(AurelFlowValidationError):
        build_runtime_checkpoint_snapshot(
            checkpoint_ref=ref,
            run=other_run,
            state_envelope=envelope,
            realized_graph=realized,
            topology_snapshot=topology,
        )


def test_snapshot_ref_and_read_model() -> None:
    _bundle, _realized, _topology, ref, _envelope, snapshot = _checkpoint_fixture()
    snap_ref = runtime_checkpoint_snapshot_ref(snapshot)
    assert snap_ref.snapshot_id == snapshot.snapshot_id
    assert snap_ref.checkpoint_ref_id == ref.checkpoint_id
    read_model = build_runtime_checkpoint_snapshot_read_model(snapshot, ref)
    assert read_model.checkpoint_kind == ref.checkpoint_kind.value
    assert read_model.has_topology_binding is True
    assert read_model.snapshot_is_not_persistence is True
    with pytest.raises(AurelFlowValidationError):
        replace(read_model, snapshot_is_not_proof=False)
    with pytest.raises(AurelFlowValidationError):
        replace(read_model, trace_verified=True)


def test_serialization_contract_is_ready_but_not_storage() -> None:
    contract = build_checkpoint_serialization_contract()
    assert contract.deterministic_serialization is True
    assert contract.stable_ids_required is True
    assert contract.canonical_json is True
    with pytest.raises(AurelFlowValidationError):
        replace(contract, deterministic_serialization=False)
    with pytest.raises(AurelFlowValidationError):
        replace(contract, external_persistence=True)
    with pytest.raises(AurelFlowValidationError):
        replace(contract, database_backend=True)
    with pytest.raises(AurelFlowValidationError):
        replace(contract, event_store_backend=True)


def test_checkpoint_construction_does_not_mutate_demo_run() -> None:
    bundle, _realized, _topology, _ref, _envelope, _snapshot = _checkpoint_fixture()
    step_before = bundle.run.state.step
    lifecycle_before = bundle.run.state.lifecycle_status
    history_before = len(bundle.run.history)
    _checkpoint_fixture()
    assert bundle.run.state.step == step_before
    assert bundle.run.state.lifecycle_status is lifecycle_before
    assert len(bundle.run.history) == history_before
