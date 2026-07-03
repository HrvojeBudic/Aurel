"""P3-FLOW-J capability envelope / dependency graph behavior tests.

A capability is candidate-only and never permission; a dependency edge is
not a transport route; the dependency graph detects declared cycles without
executing anything.
"""

from __future__ import annotations

import dataclasses

import pytest

from agentic_runtime.aurel_flow import (
    AurelFlowValidationError,
    RuntimeServiceKind,
    ServiceCapabilityKind,
    ServiceDependencyKind,
    build_compound_runtime_topology,
    build_service_dependency_graph,
    create_logical_service_ref,
    create_runtime_service_node,
    create_service_capability_envelope,
    create_service_dependency_edge,
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


def test_invocation_capability_is_candidate_only_and_p4_p9_bound() -> None:
    envelope = create_service_capability_envelope(
        service_ref=_ref(RuntimeServiceKind.TOOL_SERVICE, "git"),
        capability_kinds=(
            ServiceCapabilityKind.CAN_CALL_TOOL_CANDIDATE,
            ServiceCapabilityKind.CAN_EXECUTE_SANDBOX_CANDIDATE,
        ),
    )
    assert envelope.candidate_only is True
    assert envelope.requires_p4_execution is True
    assert envelope.requires_p9_authority is True
    for forbidden_field in (
        "permission_granted",
        "authority_granted",
        "service_invoked",
        "execution_available",
    ):
        assert getattr(envelope, forbidden_field) is False
        with pytest.raises(AurelFlowValidationError):
            dataclasses.replace(envelope, **{forbidden_field: True})
    with pytest.raises(AurelFlowValidationError):
        dataclasses.replace(envelope, requires_p4_execution=False)


def test_projection_capability_is_not_invocation_bound() -> None:
    envelope = create_service_capability_envelope(
        service_ref=_ref(RuntimeServiceKind.PROJECTION_SERVICE, "shell"),
        capability_kinds=(
            ServiceCapabilityKind.CAN_PROJECT_READ_MODEL_CANDIDATE,
        ),
    )
    assert envelope.requires_p4_execution is False
    assert envelope.requires_p9_authority is False


def test_capability_envelope_requires_capabilities() -> None:
    with pytest.raises(AurelFlowValidationError):
        create_service_capability_envelope(
            service_ref=_ref(RuntimeServiceKind.TOOL_SERVICE, "git"),
            capability_kinds=(),
        )


def test_dependency_edge_is_not_transport_and_not_self_referential() -> None:
    agent = _ref(RuntimeServiceKind.AGENT_SERVICE, "coder")
    model = _ref(RuntimeServiceKind.MODEL_SERVICE, "frontier")
    edge = create_service_dependency_edge(
        from_service_ref=agent,
        to_service_ref=model,
        dependency_kind=ServiceDependencyKind.REQUIRES_MODEL,
    )
    for forbidden_field in (
        "transport_route",
        "message_sent",
        "service_invoked",
        "execution_available",
    ):
        assert getattr(edge, forbidden_field) is False
        with pytest.raises(AurelFlowValidationError):
            dataclasses.replace(edge, **{forbidden_field: True})
    with pytest.raises(AurelFlowValidationError):
        create_service_dependency_edge(
            from_service_ref=agent,
            to_service_ref=agent,
            dependency_kind=ServiceDependencyKind.REQUIRES_MODEL,
        )


def test_dependency_graph_detects_declared_cycles() -> None:
    a = _ref(RuntimeServiceKind.AGENT_SERVICE, "a")
    b = _ref(RuntimeServiceKind.VERIFIER_SERVICE, "b")
    topology = _topology((a, b))
    acyclic = build_service_dependency_graph(
        topology=topology,
        edges=(
            create_service_dependency_edge(
                from_service_ref=a,
                to_service_ref=b,
                dependency_kind=ServiceDependencyKind.REQUIRES_VERIFIER,
            ),
        ),
    )
    assert acyclic.cycle_detected is False
    cyclic = build_service_dependency_graph(
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
    assert cyclic.cycle_detected is True
    assert cyclic.dependency_graph_id != acyclic.dependency_graph_id


def test_dependency_graph_rejects_edges_outside_the_topology() -> None:
    a = _ref(RuntimeServiceKind.AGENT_SERVICE, "a")
    b = _ref(RuntimeServiceKind.MODEL_SERVICE, "b")
    outsider = _ref(RuntimeServiceKind.TOOL_SERVICE, "outsider")
    topology = _topology((a, b))
    with pytest.raises(AurelFlowValidationError):
        build_service_dependency_graph(
            topology=topology,
            edges=(
                create_service_dependency_edge(
                    from_service_ref=a,
                    to_service_ref=outsider,
                    dependency_kind=ServiceDependencyKind.REQUIRES_TOOL,
                ),
            ),
        )


def test_dependency_graph_is_deterministic() -> None:
    a = _ref(RuntimeServiceKind.AGENT_SERVICE, "a")
    b = _ref(RuntimeServiceKind.MODEL_SERVICE, "b")

    def make():
        return build_service_dependency_graph(
            topology=_topology((a, b)),
            edges=(
                create_service_dependency_edge(
                    from_service_ref=a,
                    to_service_ref=b,
                    dependency_kind=ServiceDependencyKind.REQUIRES_MODEL,
                ),
            ),
        )

    assert make().dependency_graph_id == make().dependency_graph_id
