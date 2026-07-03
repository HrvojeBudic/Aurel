"""P3-FLOW-J compound topology behavior tests.

A compound topology is a topology map, not a service mesh, and it never
runs, discovers, transports, dispatches, or executes.
"""

from __future__ import annotations

import dataclasses

import pytest

from agentic_runtime.aurel_flow import (
    AurelFlowValidationError,
    FlowTruthLabel,
    RuntimeServiceKind,
    build_compound_runtime_topology,
    create_logical_service_ref,
    create_runtime_service_node,
)


def _node(kind=RuntimeServiceKind.MODEL_SERVICE, name="frontier"):
    return create_runtime_service_node(
        service_ref=create_logical_service_ref(
            service_kind=kind, logical_name=name
        )
    )


def _topology():
    return build_compound_runtime_topology(
        run_id="run-1",
        service_nodes=(
            _node(),
            _node(RuntimeServiceKind.TOOL_SERVICE, "git"),
            _node(RuntimeServiceKind.VERIFIER_SERVICE, "verifier"),
        ),
    )


def test_topology_counts_service_kinds_deterministically() -> None:
    first = _topology()
    second = _topology()
    assert first.topology_id == second.topology_id
    assert first.service_kind_counts == (
        ("MODEL_SERVICE", 1),
        ("TOOL_SERVICE", 1),
        ("VERIFIER_SERVICE", 1),
    )
    assert first.truth_label is FlowTruthLabel.READ_MODEL_ONLY


def test_topology_is_not_a_service_mesh() -> None:
    topology = _topology()
    for forbidden_field in (
        "service_runtime_available",
        "service_discovery_performed",
        "network_transport_available",
        "dispatch_available",
        "execution_available",
    ):
        assert getattr(topology, forbidden_field) is False
        with pytest.raises(AurelFlowValidationError):
            dataclasses.replace(topology, **{forbidden_field: True})


def test_topology_rejects_duplicate_service_refs() -> None:
    node = _node()
    with pytest.raises(AurelFlowValidationError):
        build_compound_runtime_topology(
            run_id="run-1", service_nodes=(node, node)
        )


def test_contains_ref_answers_membership() -> None:
    topology = _topology()
    known = topology.service_nodes[0].service_ref.service_ref_id
    assert topology.contains_ref(known) is True
    assert topology.contains_ref("flsvr-unknown") is False


def test_service_kind_vocabulary_is_closed_world() -> None:
    values = {kind.value for kind in RuntimeServiceKind}
    assert "UNAVAILABLE" in values
    assert "ERROR" in values
    for forbidden in ("LIVE_SERVICE", "ENDPOINT", "TRANSPORT"):
        assert forbidden not in values
