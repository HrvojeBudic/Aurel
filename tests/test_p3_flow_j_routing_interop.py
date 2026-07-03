"""P3-FLOW-J routing candidate / interop layer ref behavior tests.

A routing candidate routes nothing; an interoperability layer ref is a
logical name, never a live protocol.
"""

from __future__ import annotations

import dataclasses

import pytest

from agentic_runtime.aurel_flow import (
    AurelFlowValidationError,
    InteropLayerKind,
    RuntimeServiceKind,
    ServiceRoutingReason,
    create_interoperability_layer_ref,
    create_logical_service_ref,
    create_service_routing_candidate,
)


def _candidate(reason=ServiceRoutingReason.TOOL_REQUIREMENT_MATCH):
    return create_service_routing_candidate(
        run_id="run-1",
        atomic_unit_id="flwau-1",
        service_ref=create_logical_service_ref(
            service_kind=RuntimeServiceKind.TOOL_SERVICE, logical_name="git"
        ),
        routing_reason=reason,
    )


def test_routing_candidate_routes_nothing() -> None:
    candidate = _candidate()
    assert candidate.routing_candidate_only is True
    assert candidate.requires_p4_execution is True
    for forbidden_field in (
        "message_sent",
        "network_called",
        "service_invoked",
        "dispatch_available",
        "execution_available",
    ):
        assert getattr(candidate, forbidden_field) is False
        with pytest.raises(AurelFlowValidationError):
            dataclasses.replace(candidate, **{forbidden_field: True})
    with pytest.raises(AurelFlowValidationError):
        dataclasses.replace(candidate, routing_candidate_only=False)


def test_routing_candidate_inherits_authority_future_from_ref() -> None:
    invocation_bound = _candidate()
    assert invocation_bound.requires_p9_authority is True
    review = create_service_routing_candidate(
        run_id="run-1",
        atomic_unit_id="flwau-1",
        service_ref=create_logical_service_ref(
            service_kind=RuntimeServiceKind.OPERATOR_REVIEW_SERVICE,
            logical_name="review",
        ),
        routing_reason=ServiceRoutingReason.AUTHORITY_REQUIRED,
    )
    assert review.requires_p9_authority is True


def test_routing_candidate_is_deterministic() -> None:
    assert _candidate().routing_candidate_id == _candidate().routing_candidate_id


def test_routing_reason_vocabulary_has_no_route_verb() -> None:
    values = {reason.value for reason in ServiceRoutingReason}
    for forbidden in ("ROUTED", "DISPATCHED", "SENT", "INVOKED"):
        assert forbidden not in values


def test_interop_layer_refs_are_not_live_protocols() -> None:
    for layer_kind in (
        InteropLayerKind.DISCOVERY_LAYER_REF,
        InteropLayerKind.ROUTING_LAYER_REF,
        InteropLayerKind.EXECUTION_LAYER_REF,
        InteropLayerKind.SECURITY_LAYER_REF,
        InteropLayerKind.OBSERVABILITY_LAYER_REF,
    ):
        ref = create_interoperability_layer_ref(layer_kind)
        for forbidden_field in (
            "discovery_performed",
            "routing_performed",
            "execution_performed",
            "security_enforced",
            "observability_active",
            "transport_bound",
            "network_called",
        ):
            assert getattr(ref, forbidden_field) is False
            with pytest.raises(AurelFlowValidationError):
                dataclasses.replace(ref, **{forbidden_field: True})


def test_interop_layer_refs_name_their_future_owners() -> None:
    assert (
        create_interoperability_layer_ref(
            InteropLayerKind.EXECUTION_LAYER_REF
        ).future_owner
        == "P4 AurelExec"
    )
    assert (
        create_interoperability_layer_ref(
            InteropLayerKind.SECURITY_LAYER_REF
        ).future_owner
        == "P9 Custos"
    )
    assert (
        create_interoperability_layer_ref(
            InteropLayerKind.OBSERVABILITY_LAYER_REF
        ).future_owner
        == "P5 AurelTrace"
    )
