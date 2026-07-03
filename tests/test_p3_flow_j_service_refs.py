"""P3-FLOW-J logical service ref / service node behavior tests.

A service ref is not a live handle, endpoint, or transport; a service node
is not a live process; invocation-bound kinds stay future-bound to P4+P9.
"""

from __future__ import annotations

import dataclasses

import pytest

from agentic_runtime.aurel_flow import (
    INVOCATION_BOUND_SERVICE_KINDS,
    AurelFlowValidationError,
    RuntimeServiceKind,
    create_logical_service_ref,
    create_runtime_service_node,
)


def test_service_ref_is_never_a_live_handle() -> None:
    ref = create_logical_service_ref(
        service_kind=RuntimeServiceKind.MODEL_SERVICE, logical_name="frontier"
    )
    for forbidden_field in (
        "live_handle",
        "endpoint_available",
        "transport_available",
        "invocation_available",
        "service_invoked",
        "network_called",
    ):
        assert getattr(ref, forbidden_field) is False
        with pytest.raises(AurelFlowValidationError):
            dataclasses.replace(ref, **{forbidden_field: True})


def test_invocation_bound_kinds_stay_future_bound_to_p4_and_p9() -> None:
    for kind in INVOCATION_BOUND_SERVICE_KINDS:
        ref = create_logical_service_ref(
            service_kind=kind, logical_name="svc"
        )
        assert ref.future_p4_required is True
        assert ref.future_p9_required is True
        with pytest.raises(AurelFlowValidationError):
            dataclasses.replace(ref, future_p4_required=False)
        with pytest.raises(AurelFlowValidationError):
            dataclasses.replace(ref, future_p9_required=False)


def test_verifier_and_trace_refs_are_p5_bound() -> None:
    verifier = create_logical_service_ref(
        service_kind=RuntimeServiceKind.VERIFIER_SERVICE,
        logical_name="verifier",
    )
    trace = create_logical_service_ref(
        service_kind=RuntimeServiceKind.TRACE_SERVICE_REF, logical_name="trace"
    )
    assert verifier.future_p5_required is True
    assert trace.future_p5_required is True


def test_projection_service_ref_carries_no_invocation_future() -> None:
    ref = create_logical_service_ref(
        service_kind=RuntimeServiceKind.PROJECTION_SERVICE,
        logical_name="shell-projection",
    )
    assert ref.future_p4_required is False
    assert ref.future_p9_required is False


def test_service_ref_requires_a_logical_name_and_is_deterministic() -> None:
    with pytest.raises(AurelFlowValidationError):
        create_logical_service_ref(
            service_kind=RuntimeServiceKind.TOOL_SERVICE, logical_name=""
        )
    first = create_logical_service_ref(
        service_kind=RuntimeServiceKind.TOOL_SERVICE, logical_name="git"
    )
    second = create_logical_service_ref(
        service_kind=RuntimeServiceKind.TOOL_SERVICE, logical_name="git"
    )
    assert first.service_ref_id == second.service_ref_id


def test_service_node_is_not_a_live_process() -> None:
    node = create_runtime_service_node(
        service_ref=create_logical_service_ref(
            service_kind=RuntimeServiceKind.SANDBOX_SERVICE,
            logical_name="restricted",
        )
    )
    assert node.display_name == "restricted"
    for forbidden_field in (
        "live_process",
        "live_endpoint",
        "endpoint_available",
        "transport_bound",
        "service_invoked",
        "execution_available",
        "authority_granted",
    ):
        assert getattr(node, forbidden_field) is False
        with pytest.raises(AurelFlowValidationError):
            dataclasses.replace(node, **{forbidden_field: True})
