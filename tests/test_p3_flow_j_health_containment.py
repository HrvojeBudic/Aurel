"""P3-FLOW-J topology health / failure containment behavior tests.

Topology health is diagnostic readiness over declared contracts — never a
live probe, never proof; a containment boundary executes no containment.
"""

from __future__ import annotations

import dataclasses

import pytest

from agentic_runtime.aurel_flow import (
    AurelFlowValidationError,
    RuntimeServiceKind,
    ServiceCapabilityKind,
    ServiceDependencyKind,
    ServiceRoutingReason,
    TopologyHealthSignalKind,
    assess_topology_health,
    build_compound_runtime_topology,
    build_service_dependency_graph,
    create_failure_containment_boundary,
    create_logical_service_ref,
    create_runtime_service_node,
    create_service_capability_envelope,
    create_service_dependency_edge,
    create_service_routing_candidate,
)


def _ref(kind, name):
    return create_logical_service_ref(service_kind=kind, logical_name=name)


def _topology(refs):
    return build_compound_runtime_topology(
        run_id="run-1",
        service_nodes=tuple(
            create_runtime_service_node(service_ref=ref) for ref in refs
        ),
    )


def test_cycle_in_dependency_graph_raises_cycle_risk_signal() -> None:
    a = _ref(RuntimeServiceKind.AGENT_SERVICE, "a")
    b = _ref(RuntimeServiceKind.VERIFIER_SERVICE, "b")
    topology = _topology((a, b))
    graph = build_service_dependency_graph(
        topology=topology,
        edges=(
            create_service_dependency_edge(
                from_service_ref=a,
                to_service_ref=b,
                dependency_kind=ServiceDependencyKind.REQUIRES_VERIFIER,
            ),
            create_service_dependency_edge(
                from_service_ref=b,
                to_service_ref=a,
                dependency_kind=ServiceDependencyKind.REQUIRES_AGENT,
            ),
        ),
    )
    health = assess_topology_health(topology=topology, dependency_graph=graph)
    assert TopologyHealthSignalKind.TOPOLOGY_CYCLE_RISK in health.signal_kinds
    assert health.topology_ready_candidate is False


def test_missing_capability_envelope_raises_capability_missing_signal() -> None:
    tool = _ref(RuntimeServiceKind.TOOL_SERVICE, "git")
    topology = _topology((tool,))
    candidate = create_service_routing_candidate(
        run_id="run-1",
        atomic_unit_id="flwau-1",
        service_ref=tool,
        routing_reason=ServiceRoutingReason.TOOL_REQUIREMENT_MATCH,
    )
    uncovered = assess_topology_health(
        topology=topology, routing_candidates=(candidate,)
    )
    assert (
        TopologyHealthSignalKind.SERVICE_CAPABILITY_MISSING
        in uncovered.signal_kinds
    )
    covered = assess_topology_health(
        topology=topology,
        capability_envelopes=(
            create_service_capability_envelope(
                service_ref=tool,
                capability_kinds=(
                    ServiceCapabilityKind.CAN_CALL_TOOL_CANDIDATE,
                ),
            ),
        ),
        routing_candidates=(candidate,),
    )
    assert covered.signal_kinds == ()
    assert covered.topology_ready_candidate is True


def test_routing_target_outside_topology_is_unknown_boundary() -> None:
    inside = _ref(RuntimeServiceKind.MODEL_SERVICE, "frontier")
    outside = _ref(RuntimeServiceKind.DATA_SERVICE, "warehouse")
    health = assess_topology_health(
        topology=_topology((inside,)),
        routing_candidates=(
            create_service_routing_candidate(
                run_id="run-1",
                atomic_unit_id="flwau-1",
                service_ref=outside,
                routing_reason=ServiceRoutingReason.DATA_REQUIREMENT_MATCH,
            ),
        ),
    )
    assert (
        TopologyHealthSignalKind.UNKNOWN_SERVICE_BOUNDARY in health.signal_kinds
    )


def test_empty_topology_is_an_unavailability_candidate() -> None:
    health = assess_topology_health(
        topology=build_compound_runtime_topology(
            run_id="run-1", service_nodes=()
        )
    )
    assert (
        TopologyHealthSignalKind.SERVICE_UNAVAILABLE_CANDIDATE
        in health.signal_kinds
    )


def test_health_frame_is_diagnostic_only_never_probe_or_proof() -> None:
    health = assess_topology_health(
        topology=_topology((_ref(RuntimeServiceKind.MODEL_SERVICE, "m"),))
    )
    assert health.diagnostic_only is True
    for forbidden_field in (
        "proof_available",
        "trace_verified",
        "recovery_executed",
        "service_health_checked",
        "telemetry_active",
    ):
        assert getattr(health, forbidden_field) is False
        with pytest.raises(AurelFlowValidationError):
            dataclasses.replace(health, **{forbidden_field: True})
    with pytest.raises(AurelFlowValidationError):
        dataclasses.replace(health, diagnostic_only=False)


def test_containment_boundary_executes_nothing() -> None:
    boundary = create_failure_containment_boundary(
        run_id="run-1",
        contained_service_ref_ids=("flsvr-a", "flsvr-b"),
        containment_rationale="tool failures must not cascade to the model",
    )
    assert boundary.diagnostic_only is True
    for forbidden_field in (
        "recovery_executed",
        "service_invoked",
        "execution_available",
    ):
        with pytest.raises(AurelFlowValidationError):
            dataclasses.replace(boundary, **{forbidden_field: True})
    with pytest.raises(AurelFlowValidationError):
        create_failure_containment_boundary(
            run_id="run-1",
            contained_service_ref_ids=(),
            containment_rationale="empty",
        )
