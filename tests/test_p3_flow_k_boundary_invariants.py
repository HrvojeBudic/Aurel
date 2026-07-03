"""P3-FLOW-K boundary compliance / invariant probe behavior tests.

Probes are read-only detection over real P3 objects: a compliance probe is
not enforcement, an invariant finding is not repair, and probes never
mutate the probed contract.
"""

from __future__ import annotations

import dataclasses

import pytest

from agentic_runtime.aurel_flow import (
    AurelFlowValidationError,
    AutonomyModeSource,
    BoundaryComplianceCategory,
    BoundaryComplianceStatus,
    GovernedAutonomyLevel,
    RuntimeInvariantKind,
    RuntimeInvariantStatus,
    RuntimeServiceKind,
    SchedulingIntentKind,
    SchedulingIntentReason,
    WorkflowAtomicUnitKind,
    assess_topology_health,
    build_boundary_compliance_read_model,
    build_compound_runtime_topology,
    build_runtime_invariant_read_model,
    create_logical_service_ref,
    create_runtime_service_node,
    create_scheduling_intent,
    create_workflow_atomic_unit,
    probe_runtime_invariant,
    run_boundary_compliance_probe,
    select_autonomy_mode,
)


def _intent():
    unit = create_workflow_atomic_unit(
        run_id="run-1",
        unit_kind=WorkflowAtomicUnitKind.SINGLE_NODE,
        node_ids=("n1",),
    )
    return create_scheduling_intent(
        unit=unit,
        intent_kind=SchedulingIntentKind.SCHEDULE_READY_NODE_CANDIDATE,
        intent_reason=SchedulingIntentReason.DEPENDENCIES_SATISFIED,
    )


def _service_ref():
    return create_logical_service_ref(
        service_kind=RuntimeServiceKind.TOOL_SERVICE, logical_name="git"
    )


def test_compliance_probe_passes_on_fail_closed_p3_objects() -> None:
    for category, subject in (
        (BoundaryComplianceCategory.NO_EXECUTION, _intent()),
        (BoundaryComplianceCategory.NO_DISPATCH, _intent()),
        (BoundaryComplianceCategory.NO_FAKE_LIVE, _intent()),
        (BoundaryComplianceCategory.NO_FAKE_TRACE_VERIFIED, _service_ref()),
        (BoundaryComplianceCategory.NO_NETWORK, _service_ref()),
    ):
        probe = run_boundary_compliance_probe(
            category=category, subject=subject
        )
        assert probe.status is BoundaryComplianceStatus.PASS
        assert probe.read_only is True
        assert probe.findings == ()


def test_compliance_probe_detects_runtime_submit_category_on_topology() -> None:
    topology = build_compound_runtime_topology(
        run_id="run-1",
        service_nodes=(create_runtime_service_node(service_ref=_service_ref()),),
    )
    runtime_probe = run_boundary_compliance_probe(
        category=BoundaryComplianceCategory.NO_SERVICE_RUNTIME,
        subject=topology,
    )
    assert runtime_probe.status is BoundaryComplianceStatus.PASS
    submit_probe = run_boundary_compliance_probe(
        category=BoundaryComplianceCategory.NO_RUNTIME_SUBMIT, subject=_intent()
    )
    # scheduling intent carries no runtime_submit_wired field: honest N/A
    assert submit_probe.status is BoundaryComplianceStatus.NOT_APPLICABLE


def test_compliance_probe_fails_on_a_violating_object() -> None:
    class FakeOverclaim:
        production_ready = True
        release_approved = False

    probe = run_boundary_compliance_probe(
        category=BoundaryComplianceCategory.NO_PRODUCTION_CLAIM,
        subject=FakeOverclaim(),
    )
    assert probe.status is BoundaryComplianceStatus.FAIL
    assert len(probe.findings) == 1
    assert "production_ready" in probe.findings[0].detail
    assert probe.findings[0].enforcement_performed is False
    assert probe.findings[0].punishment_applied is False


def test_compliance_probe_is_read_only_and_never_enforces() -> None:
    probe = run_boundary_compliance_probe(
        category=BoundaryComplianceCategory.NO_EXECUTION, subject=_intent()
    )
    for forbidden_field in (
        "enforcement_performed",
        "mutation_performed",
        "runtime_policy_changed",
        "punishment_applied",
    ):
        with pytest.raises(AurelFlowValidationError):
            dataclasses.replace(probe, **{forbidden_field: True})
    with pytest.raises(AurelFlowValidationError):
        dataclasses.replace(probe, read_only=False)
    # a FAIL status without findings is unconstructible
    with pytest.raises(AurelFlowValidationError):
        dataclasses.replace(probe, status=BoundaryComplianceStatus.FAIL)


def test_invariant_probes_encode_the_flow_laws() -> None:
    autonomy_mode = select_autonomy_mode(
        run_id="run-1",
        level=GovernedAutonomyLevel.A2_PREPARE_CANDIDATES,
        mode_source=AutonomyModeSource.OPERATOR_SELECTED,
        selected_by="op-1",
    )
    for invariant_kind, subject in (
        (RuntimeInvariantKind.SCHEDULING_INTENT_IS_NOT_DISPATCH, _intent()),
        (RuntimeInvariantKind.AUTONOMY_LEVEL_IS_NOT_AUTHORITY, autonomy_mode),
        (RuntimeInvariantKind.SERVICE_REF_IS_NOT_ENDPOINT, _service_ref()),
        (
            RuntimeInvariantKind.TOPOLOGY_HEALTH_IS_NOT_PROOF,
            assess_topology_health(
                topology=build_compound_runtime_topology(
                    run_id="run-1",
                    service_nodes=(
                        create_runtime_service_node(service_ref=_service_ref()),
                    ),
                )
            ),
        ),
    ):
        probe = probe_runtime_invariant(
            invariant_kind=invariant_kind, subject=subject
        )
        assert probe.status is RuntimeInvariantStatus.SATISFIED, invariant_kind
        assert probe.read_only is True


def test_react_projection_is_not_control_invariant_over_dummy_view() -> None:
    class FakeControllingView:
        projection_id = "view-1"
        frontend_mutation_allowed = True
        ui_dispatch_allowed = False

    probe = probe_runtime_invariant(
        invariant_kind=RuntimeInvariantKind.REACT_PROJECTION_IS_NOT_CONTROL,
        subject=FakeControllingView(),
    )
    assert probe.status is RuntimeInvariantStatus.VIOLATED
    assert probe.findings[0].repair_executed is False
    assert probe.findings[0].contract_rewritten is False


def test_invariant_probe_is_not_applicable_without_law_attributes() -> None:
    probe = probe_runtime_invariant(
        invariant_kind=RuntimeInvariantKind.REVERT_CANDIDATE_IS_NOT_ROLLBACK_EXECUTION,
        subject=object(),
    )
    assert probe.status is RuntimeInvariantStatus.NOT_APPLICABLE


def test_probe_read_models_aggregate_deterministically() -> None:
    compliance_probes = (
        run_boundary_compliance_probe(
            category=BoundaryComplianceCategory.NO_EXECUTION, subject=_intent()
        ),
        run_boundary_compliance_probe(
            category=BoundaryComplianceCategory.NO_FAKE_LIVE, subject=_intent()
        ),
    )
    compliance_rm = build_boundary_compliance_read_model(compliance_probes)
    assert compliance_rm.probe_count == 2
    assert compliance_rm.all_applicable_passed is True
    assert compliance_rm.failing_probe_ids == ()
    invariant_probes = (
        probe_runtime_invariant(
            invariant_kind=RuntimeInvariantKind.SCHEDULING_INTENT_IS_NOT_DISPATCH,
            subject=_intent(),
        ),
    )
    invariant_rm = build_runtime_invariant_read_model(invariant_probes)
    assert invariant_rm.all_applicable_satisfied is True
    assert (
        build_runtime_invariant_read_model(invariant_probes).read_model_id
        == invariant_rm.read_model_id
    )
