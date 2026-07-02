"""P3-FLOW-E runtime topology snapshot tests (P3.13.5-P3.13.9)."""

from __future__ import annotations

import pytest

from agentic_runtime.aurel_flow import (
    AurelFlowValidationError,
    EdgeActivationState,
    EdgeReliabilityRole,
    FlowTruthLabel,
    GraphRealizationReason,
    RuntimeTopologyEdge,
    RuntimeTopologyNode,
    RuntimeTopologySnapshot,
    RuntimeTopologySnapshotRef,
    RuntimeTopologyVersion,
    TopologySnapshotReadModel,
    build_flow_demo_bundle,
    build_runtime_topology_snapshot,
    build_topology_snapshot_read_model,
    create_workflow_run,
    create_workflow_template,
    realize_runtime_graph,
    runtime_topology_snapshot_ref,
)


def _snapshot():
    bundle = build_flow_demo_bundle()
    template = create_workflow_template(bundle.graph)
    realized = realize_runtime_graph(
        template=template, run=bundle.run, realization_reason=GraphRealizationReason.RUN_CREATED
    )
    snapshot = build_runtime_topology_snapshot(
        realized_graph=realized, graph=bundle.graph, run=bundle.run
    )
    return bundle, realized, snapshot


def test_snapshot_represents_nodes_and_edges() -> None:
    bundle, _, snapshot = _snapshot()
    assert isinstance(snapshot, RuntimeTopologySnapshot)
    assert len(snapshot.nodes) == len(bundle.graph.nodes)
    assert len(snapshot.edges) == len(bundle.graph.edges)
    assert all(isinstance(node, RuntimeTopologyNode) for node in snapshot.nodes)
    assert all(isinstance(edge, RuntimeTopologyEdge) for edge in snapshot.edges)


def test_snapshot_edges_carry_reliability_roles() -> None:
    _, _, snapshot = _snapshot()
    roles = {edge.reliability_role for edge in snapshot.edges}
    assert roles <= set(EdgeReliabilityRole)
    # the demo graph declares a rollback-candidate edge -> RECOVERY_FLOW role.
    assert EdgeReliabilityRole.RECOVERY_FLOW in roles
    # the demo graph's remaining edges are default flow -> PRIMARY_FLOW role.
    assert EdgeReliabilityRole.PRIMARY_FLOW in roles


def test_snapshot_version_references_realized_graph() -> None:
    _, realized, snapshot = _snapshot()
    assert isinstance(snapshot.topology_version, RuntimeTopologyVersion)
    assert snapshot.topology_version.based_on_realized_graph_id == realized.realized_graph_id


def test_snapshot_is_deterministic() -> None:
    bundle = build_flow_demo_bundle()
    template = create_workflow_template(bundle.graph)
    realized = realize_runtime_graph(
        template=template, run=bundle.run, realization_reason=GraphRealizationReason.RUN_CREATED
    )
    snapshot_a = build_runtime_topology_snapshot(
        realized_graph=realized, graph=bundle.graph, run=bundle.run
    )
    snapshot_b = build_runtime_topology_snapshot(
        realized_graph=realized, graph=bundle.graph, run=bundle.run
    )
    assert snapshot_a.snapshot_id == snapshot_b.snapshot_id
    assert snapshot_a.snapshot_hash == snapshot_b.snapshot_hash


def test_snapshot_is_not_trace_and_not_proof() -> None:
    _, _, snapshot = _snapshot()
    assert snapshot.trace_verified is False
    assert snapshot.proof_available is False
    assert snapshot.execution_available is False


def test_snapshot_rejects_mismatched_run() -> None:
    bundle, realized, _ = _snapshot()
    other_run = create_workflow_run(bundle.graph, run_key="a-genuinely-different-run-key")
    assert other_run.run_id != realized.run_id
    # realized graph belongs to bundle.run; passing a different run must fail.
    with pytest.raises(AurelFlowValidationError):
        build_runtime_topology_snapshot(
            realized_graph=realized, graph=bundle.graph, run=other_run
        )


def test_snapshot_ref_matches_snapshot() -> None:
    _, _, snapshot = _snapshot()
    ref = runtime_topology_snapshot_ref(snapshot)
    assert isinstance(ref, RuntimeTopologySnapshotRef)
    assert ref.snapshot_id == snapshot.snapshot_id
    assert ref.run_id == snapshot.run_id


def test_read_model_is_deterministic_and_not_trace() -> None:
    _, _, snapshot = _snapshot()
    read_model_a = build_topology_snapshot_read_model(snapshot)
    read_model_b = build_topology_snapshot_read_model(snapshot)
    assert isinstance(read_model_a, TopologySnapshotReadModel)
    assert read_model_a.read_model_hash == read_model_b.read_model_hash
    assert read_model_a.snapshot_is_not_trace is True
    assert read_model_a.snapshot_is_not_proof is True
    assert read_model_a.trace_verified is False
    assert read_model_a.node_count == len(snapshot.nodes)
    assert read_model_a.edge_count == len(snapshot.edges)


def test_edge_activation_state_default_is_active() -> None:
    _, _, snapshot = _snapshot()
    assert all(edge.activation_state is EdgeActivationState.ACTIVE for edge in snapshot.edges)
    assert all(not edge.proposed and not edge.pruned for edge in snapshot.edges)


def test_snapshot_construction_does_not_mutate_demo_run() -> None:
    bundle, _, _ = _snapshot()
    step_before = bundle.run.state.step
    history_before = len(bundle.run.history)
    build_runtime_topology_snapshot(
        realized_graph=realize_runtime_graph(
            template=create_workflow_template(bundle.graph),
            run=bundle.run,
            realization_reason=GraphRealizationReason.RUN_CREATED,
        ),
        graph=bundle.graph,
        run=bundle.run,
    )
    assert bundle.run.state.step == step_before
    assert len(bundle.run.history) == history_before


def test_snapshot_truth_label_is_read_model_only() -> None:
    _, _, snapshot = _snapshot()
    assert snapshot.truth_label is FlowTruthLabel.READ_MODEL_ONLY
