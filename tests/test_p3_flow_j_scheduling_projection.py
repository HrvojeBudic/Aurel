"""P3-FLOW-J scheduling-topology bridge / projection behavior tests.

The bridge maps P3-FLOW-I requirement frames to candidate service refs and
routing candidates without dispatching; the projection is read-only and the
UI cannot route, invoke, or control topology.
"""

from __future__ import annotations

import dataclasses

import pytest

from agentic_runtime.aurel_flow import (
    AurelFlowValidationError,
    AutonomyDecisionClass,
    AutonomyScopeDimension,
    FlowTruthLabel,
    GovernedAutonomyLevel,
    RuntimeServiceKind,
    SchedulingIntentKind,
    SchedulingIntentReason,
    ServiceRoutingReason,
    WorkflowAtomicUnitKind,
    assess_topology_health,
    bridge_scheduling_requirements,
    build_compound_runtime_topology,
    build_compound_topology_projection,
    build_execution_resource_requirement_read_model,
    build_p4_handoff_clarity_frame,
    create_data_access_requirement_frame,
    create_model_requirement_frame,
    create_runtime_service_node,
    create_sandbox_requirement_frame,
    create_scheduling_action_boundary_check,
    create_scheduling_intent,
    create_scheduling_scope_check,
    create_tool_requirement_frame,
    create_workflow_atomic_unit,
    evaluate_autonomy_scheduling_gate,
)

_UI_FALSE_FIELDS = (
    "frontend_mutation_allowed",
    "ui_route_action_allowed",
    "ui_service_invocation_allowed",
    "ui_service_mesh_control_allowed",
    "api_server_implemented",
    "frontend_implemented",
)


def _unit():
    return create_workflow_atomic_unit(
        run_id="run-1",
        unit_kind=WorkflowAtomicUnitKind.SINGLE_NODE,
        node_ids=("n1",),
    )


def _requirements(unit):
    return build_execution_resource_requirement_read_model(
        unit=unit,
        model_requirement=create_model_requirement_frame(
            unit=unit, model_required=True, model_class="frontier"
        ),
        tool_requirement=create_tool_requirement_frame(
            unit=unit, tool_required=True, tool_names=("git",)
        ),
        sandbox_requirement=create_sandbox_requirement_frame(
            unit=unit, sandbox_required=True, sandbox_profile="restricted"
        ),
        data_access_requirement=create_data_access_requirement_frame(
            unit=unit, data_access_required=True, memory_required=True
        ),
    )


def test_bridge_maps_every_required_frame_to_a_service_kind() -> None:
    bridge = bridge_scheduling_requirements(requirements=_requirements(_unit()))
    matched_kinds = {
        ref.service_kind for ref in bridge.matched_service_refs
    }
    assert matched_kinds == {
        RuntimeServiceKind.MODEL_SERVICE,
        RuntimeServiceKind.TOOL_SERVICE,
        RuntimeServiceKind.SANDBOX_SERVICE,
        RuntimeServiceKind.DATA_SERVICE,
        RuntimeServiceKind.MEMORY_SERVICE,
    }
    reasons = {c.routing_reason for c in bridge.routing_candidates}
    assert ServiceRoutingReason.MODEL_REQUIREMENT_MATCH in reasons
    assert ServiceRoutingReason.MEMORY_REQUIREMENT_MATCH in reasons
    assert bridge.requires_p4_execution is True
    assert bridge.requires_p9_authority is True


def test_bridge_with_no_required_frames_matches_nothing() -> None:
    unit = _unit()
    bridge = bridge_scheduling_requirements(
        requirements=build_execution_resource_requirement_read_model(unit=unit)
    )
    assert bridge.matched_service_refs == ()
    assert bridge.routing_candidates == ()
    assert bridge.requires_p4_execution is True


def test_bridge_never_dispatches_or_invokes() -> None:
    bridge = bridge_scheduling_requirements(requirements=_requirements(_unit()))
    for forbidden_field in (
        "dispatch_available",
        "service_invoked",
        "execution_available",
    ):
        assert getattr(bridge, forbidden_field) is False
        with pytest.raises(AurelFlowValidationError):
            dataclasses.replace(bridge, **{forbidden_field: True})


def test_review_requiring_gate_adds_operator_review_candidate() -> None:
    unit = _unit()
    intent = create_scheduling_intent(
        unit=unit,
        intent_kind=SchedulingIntentKind.SCHEDULE_READY_NODE_CANDIDATE,
        intent_reason=SchedulingIntentReason.DEPENDENCIES_SATISFIED,
    )
    gate = evaluate_autonomy_scheduling_gate(
        intent=intent,
        scope_check=create_scheduling_scope_check(
            unit=unit,
            envelope=None,
            required_dimensions=(AutonomyScopeDimension.RUN_SCOPE,),
        ),
        boundary_check=create_scheduling_action_boundary_check(
            unit=unit,
            level=GovernedAutonomyLevel.A2_PREPARE_CANDIDATES,
            decision_class=AutonomyDecisionClass.PREPARE_PLAN,
        ),
    )
    assert gate.requires_operator_review is True
    bridge = bridge_scheduling_requirements(
        requirements=_requirements(unit), scheduling_gate=gate
    )
    assert ServiceRoutingReason.OPERATOR_REVIEW_REQUIRED in {
        c.routing_reason for c in bridge.routing_candidates
    }


def test_bridge_rejects_gate_for_a_different_unit() -> None:
    unit = _unit()
    other = create_workflow_atomic_unit(
        run_id="run-1",
        unit_kind=WorkflowAtomicUnitKind.SINGLE_NODE,
        node_ids=("n2",),
    )
    intent = create_scheduling_intent(
        unit=other,
        intent_kind=SchedulingIntentKind.SCHEDULE_READY_NODE_CANDIDATE,
        intent_reason=SchedulingIntentReason.DEPENDENCIES_SATISFIED,
    )
    gate = evaluate_autonomy_scheduling_gate(
        intent=intent,
        scope_check=create_scheduling_scope_check(
            unit=other, envelope=None, required_dimensions=()
        ),
        boundary_check=create_scheduling_action_boundary_check(
            unit=other,
            level=GovernedAutonomyLevel.A2_PREPARE_CANDIDATES,
            decision_class=AutonomyDecisionClass.PREPARE_PLAN,
        ),
    )
    with pytest.raises(AurelFlowValidationError):
        bridge_scheduling_requirements(
            requirements=_requirements(unit), scheduling_gate=gate
        )


def _projection():
    unit = _unit()
    bridge = bridge_scheduling_requirements(requirements=_requirements(unit))
    topology = build_compound_runtime_topology(
        run_id="run-1",
        service_nodes=tuple(
            create_runtime_service_node(service_ref=ref)
            for ref in bridge.matched_service_refs
        ),
    )
    health = assess_topology_health(
        topology=topology, routing_candidates=bridge.routing_candidates
    )
    handoff = build_p4_handoff_clarity_frame(bridge=bridge)
    return build_compound_topology_projection(
        topology=topology,
        routing_candidates=bridge.routing_candidates,
        health_frame=health,
        bridge=bridge,
        p4_handoff=handoff,
    )


def test_projection_mirrors_topology_truth_read_only() -> None:
    projection = _projection()
    assert projection.truth_label is FlowTruthLabel.READ_MODEL_ONLY
    assert projection.p4_consumable_ref_count == 5
    assert "MODEL_SERVICE" in projection.scheduling_matched_service_kind_values
    assert "persistence" in projection.absent_runtime_systems
    assert projection.topology_ready_candidate is False  # no capability envelopes


def test_projection_preserves_ui_powerlessness() -> None:
    projection = _projection()
    assert projection.react_projection_only is True
    for forbidden_field in _UI_FALSE_FIELDS:
        assert getattr(projection, forbidden_field) is False
        with pytest.raises(AurelFlowValidationError):
            dataclasses.replace(projection, **{forbidden_field: True})


def test_projection_rejects_foreign_run_sources() -> None:
    unit = _unit()
    bridge = bridge_scheduling_requirements(requirements=_requirements(unit))
    foreign_topology = build_compound_runtime_topology(
        run_id="run-2", service_nodes=()
    )
    with pytest.raises(AurelFlowValidationError):
        build_compound_topology_projection(
            topology=foreign_topology, bridge=bridge
        )
