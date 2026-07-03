"""P3-FLOW-J P4 handoff clarity behavior tests.

The handoff frame names what AurelExec may later consume and what is
deliberately absent; it is not P4 and wires nothing.
"""

from __future__ import annotations

import dataclasses

import pytest

from agentic_runtime.aurel_flow import (
    ABSENT_RUNTIME_SYSTEMS,
    AurelFlowValidationError,
    ServiceCapabilityKind,
    WorkflowAtomicUnitKind,
    bridge_scheduling_requirements,
    build_execution_resource_requirement_read_model,
    build_p4_handoff_clarity_frame,
    create_model_requirement_frame,
    create_service_capability_envelope,
    create_workflow_atomic_unit,
)


def _bridge_and_requirements():
    unit = create_workflow_atomic_unit(
        run_id="run-1",
        unit_kind=WorkflowAtomicUnitKind.SINGLE_NODE,
        node_ids=("n1",),
    )
    requirements = build_execution_resource_requirement_read_model(
        unit=unit,
        model_requirement=create_model_requirement_frame(
            unit=unit, model_required=True, model_class="frontier"
        ),
    )
    return bridge_scheduling_requirements(requirements=requirements), requirements


def test_handoff_names_consumable_refs_and_convertible_candidates() -> None:
    bridge, requirements = _bridge_and_requirements()
    envelope = create_service_capability_envelope(
        service_ref=bridge.matched_service_refs[0],
        capability_kinds=(ServiceCapabilityKind.CAN_GENERATE_TEXT_CANDIDATE,),
    )
    handoff = build_p4_handoff_clarity_frame(
        bridge=bridge,
        capability_envelopes=(envelope,),
        source_requirement_read_model_ids=(requirements.read_model_id,),
    )
    assert handoff.consumable_service_ref_ids == (
        bridge.matched_service_refs[0].service_ref_id,
    )
    assert handoff.convertible_routing_candidate_ids == (
        bridge.routing_candidates[0].routing_candidate_id,
    )
    assert handoff.candidate_only_capability_envelope_ids == (
        envelope.capability_envelope_id,
    )
    assert handoff.source_requirement_read_model_ids == (
        requirements.read_model_id,
    )
    assert handoff.future_p9_authority_required is True


def test_handoff_names_every_deliberately_absent_system() -> None:
    bridge, _requirements = _bridge_and_requirements()
    handoff = build_p4_handoff_clarity_frame(bridge=bridge)
    assert handoff.absent_runtime_systems == ABSENT_RUNTIME_SYSTEMS
    for absent in (
        "service_runtime",
        "service_discovery",
        "network_transport",
        "message_bus",
        "service_mesh",
        "persistence",
    ):
        assert absent in handoff.absent_runtime_systems
    # a handoff frame that omits the absent-system list is unconstructible
    with pytest.raises(AurelFlowValidationError):
        dataclasses.replace(handoff, absent_runtime_systems=("service_mesh",))


def test_handoff_is_not_p4_and_wires_nothing() -> None:
    bridge, _requirements = _bridge_and_requirements()
    handoff = build_p4_handoff_clarity_frame(bridge=bridge)
    for forbidden_field in (
        "p4_implemented",
        "runtime_submit_wired",
        "dispatch_available",
        "service_invoked",
        "execution_available",
        "invocation_available",
    ):
        assert getattr(handoff, forbidden_field) is False
        with pytest.raises(AurelFlowValidationError):
            dataclasses.replace(handoff, **{forbidden_field: True})


def test_handoff_is_deterministic() -> None:
    bridge, _requirements = _bridge_and_requirements()
    first = build_p4_handoff_clarity_frame(bridge=bridge)
    second = build_p4_handoff_clarity_frame(bridge=bridge)
    assert first.handoff_frame_id == second.handoff_frame_id
