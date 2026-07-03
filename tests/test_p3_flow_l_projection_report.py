"""P3-FLOW-L seal projection behavior tests.

React is projection only: a UI seal badge is not production readiness, a
UI release approval is not authority, and a UI P4 handoff action is not
runtime.submit. The envelope recommends P4-EXEC-A as the next task.
"""

from __future__ import annotations

import dataclasses

import pytest

from agentic_runtime.aurel_flow import (
    AurelFlowValidationError,
    BoundaryComplianceCategory,
    ContractCoverageArea,
    ContractCoverageStatus,
    FlowTruthLabel,
    HarnessScenarioKind,
    P4HandoffReadinessCheck,
    QualityMetric,
    QualityMetricStatus,
    RuntimeInvariantKind,
    RuntimeSubmitBoundaryStatus,
    SchedulingIntentKind,
    SchedulingIntentReason,
    WorkflowAtomicUnitKind,
    assess_p4_handoff_readiness,
    audit_truth_labels,
    build_boundary_compliance_read_model,
    build_contract_coverage_matrix,
    build_default_p3_pack_coverage_items,
    build_harness_evaluation_suite,
    build_p3_audit_view_model,
    build_p3_coverage_summary,
    build_p3_coverage_summary_view_model,
    build_p3_seal_input_frame,
    build_p3_seal_projection_envelope,
    build_p3_seal_react_projection_boundary,
    build_p3_seal_status_view_model,
    build_p4_execution_handoff_package,
    build_p4_handoff_view_model,
    build_runtime_invariant_read_model,
    build_runtime_quality_scorecard,
    build_unavailable_systems_ledger,
    create_contract_coverage_item,
    create_harness_evaluation_case,
    create_harness_scenario_fixture,
    create_quality_metric_item,
    create_scheduling_intent,
    create_workflow_atomic_unit,
    derive_harness_evaluation_run,
    map_runtime_submit_boundary,
    probe_runtime_invariant,
    run_boundary_compliance_probe,
    run_boundary_exit_audit,
    seal_p3_domain,
    summarize_k_evaluation,
)

_UI_FALSE_FIELDS = (
    "frontend_mutation_allowed",
    "ui_release_approval_authority",
    "ui_runtime_submit_allowed",
    "ui_execution_allowed",
    "ui_production_ready_badge_authoritative",
    "api_server_implemented",
    "frontend_implemented",
)


def _k_summary():
    fixture = create_harness_scenario_fixture(
        fixture_kind=HarnessScenarioKind.SCHEDULING_INTENT_FIXTURE,
        fixture_label="intent",
        target_contracts=("SchedulingIntent",),
    )
    run = derive_harness_evaluation_run(
        build_harness_evaluation_suite(
            suite_label="p3-final-eval",
            target_pack_range="P3.0-P3.19",
            cases=(
                create_harness_evaluation_case(case_label="c", fixture=fixture),
            ),
        )
    )
    unit = create_workflow_atomic_unit(
        run_id="run-1",
        unit_kind=WorkflowAtomicUnitKind.SINGLE_NODE,
        node_ids=("n1",),
    )
    intent = create_scheduling_intent(
        unit=unit,
        intent_kind=SchedulingIntentKind.SCHEDULE_READY_NODE_CANDIDATE,
        intent_reason=SchedulingIntentReason.DEPENDENCIES_SATISFIED,
    )
    frame = build_p3_seal_input_frame(
        run=run,
        coverage_matrix=build_contract_coverage_matrix(
            run=run,
            coverage_items=(
                create_contract_coverage_item(
                    coverage_area=ContractCoverageArea.SCHEDULING_INTENT,
                    status=ContractCoverageStatus.COVERED,
                    evidence_note="tests/test_p3_flow_i_scheduling_intent.py",
                ),
            ),
        ),
        compliance_read_model=build_boundary_compliance_read_model(
            (
                run_boundary_compliance_probe(
                    category=BoundaryComplianceCategory.NO_EXECUTION,
                    subject=intent,
                ),
            )
        ),
        invariant_read_model=build_runtime_invariant_read_model(
            (
                probe_runtime_invariant(
                    invariant_kind=(
                        RuntimeInvariantKind.SCHEDULING_INTENT_IS_NOT_DISPATCH
                    ),
                    subject=intent,
                ),
            )
        ),
        scorecard=build_runtime_quality_scorecard(
            run=run,
            metric_items=(
                create_quality_metric_item(
                    metric=QualityMetric.SEAL_READINESS,
                    status=QualityMetricStatus.PARTIAL,
                    rationale="seal input prepared for L",
                ),
            ),
        ),
        p4_assessment=assess_p4_handoff_readiness(
            run=run,
            readiness_check_results=(
                (P4HandoffReadinessCheck.SCHEDULING_INTENT_EXISTS, True),
            ),
        ),
    )
    return summarize_k_evaluation(frame)


def _envelope():
    coverage_summary = build_p3_coverage_summary(
        build_default_p3_pack_coverage_items()
    )
    k_summary = _k_summary()
    seal = seal_p3_domain(
        coverage_summary=coverage_summary,
        k_evaluation_summary=k_summary,
    )
    ledger = build_unavailable_systems_ledger()
    package = build_p4_execution_handoff_package()
    boundary_map = map_runtime_submit_boundary()
    subjects = (seal, coverage_summary, ledger, package, boundary_map)
    return build_p3_seal_projection_envelope(
        seal_view=build_p3_seal_status_view_model(seal),
        coverage_view=build_p3_coverage_summary_view_model(coverage_summary),
        audit_view=build_p3_audit_view_model(
            truth_label_audit=audit_truth_labels(subjects),
            boundary_exit_audit=run_boundary_exit_audit(subjects),
            unavailable_ledger=ledger,
        ),
        handoff_view=build_p4_handoff_view_model(
            package=package, boundary_map=boundary_map
        ),
        k_evaluation_summary=k_summary,
    )


def test_envelope_is_deterministic_and_read_only() -> None:
    first = _envelope()
    second = _envelope()
    assert first.projection_envelope_id == second.projection_envelope_id
    assert first.truth_label is FlowTruthLabel.READ_MODEL_ONLY
    views = (
        first.seal_view,
        first.coverage_view,
        first.audit_view,
        first.handoff_view,
    )
    for view in views:
        assert view.react_projection_only is True
        assert view.read_only is True
        for forbidden_field in _UI_FALSE_FIELDS:
            assert getattr(view, forbidden_field) is False
            with pytest.raises(AurelFlowValidationError):
                dataclasses.replace(view, **{forbidden_field: True})
    for forbidden_field in _UI_FALSE_FIELDS:
        with pytest.raises(AurelFlowValidationError):
            dataclasses.replace(first, **{forbidden_field: True})


def test_envelope_reflects_the_seal_and_handoff_truth() -> None:
    envelope = _envelope()
    assert envelope.seal_view.p3_control_plane_sealed is True
    assert envelope.seal_view.sealed_pack_count == 12
    assert envelope.seal_view.production_ready is False
    assert envelope.coverage_view.covered_count == 12
    assert envelope.audit_view.truth_label_failing_category_values == ()
    assert envelope.audit_view.boundary_exit_failing_category_values == ()
    assert envelope.audit_view.unavailable_system_count == 19
    assert envelope.handoff_view.handoff_surface_count == 13
    assert envelope.handoff_view.runtime_submit_primary_status_value == (
        RuntimeSubmitBoundaryStatus.NOT_WIRED_FUTURE_P4.value
    )


def test_envelope_recommends_p4_exec_a_next() -> None:
    envelope = _envelope()
    assert "P4-EXEC-A" in envelope.next_task_recommendation
    assert "runtime.submit" in envelope.next_task_recommendation


def test_seal_badge_is_not_production_readiness() -> None:
    boundary = build_p3_seal_react_projection_boundary()
    assert boundary.ui_seal_badge_is_not_production_readiness is True
    assert boundary.ui_release_approval_is_not_authority is True
    assert boundary.ui_handoff_action_is_not_runtime_submit is True
    assert boundary.runtime_source_of_truth == "python"
    with pytest.raises(AurelFlowValidationError):
        dataclasses.replace(
            boundary, ui_seal_badge_is_not_production_readiness=False
        )
    with pytest.raises(AurelFlowValidationError):
        dataclasses.replace(boundary, runtime_source_of_truth="react")
    envelope = _envelope()
    assert envelope.boundary.boundary_id == boundary.boundary_id


def test_seal_view_cannot_claim_production_or_release() -> None:
    envelope = _envelope()
    with pytest.raises(AurelFlowValidationError):
        dataclasses.replace(envelope.seal_view, production_ready=True)
    with pytest.raises(AurelFlowValidationError):
        dataclasses.replace(envelope.seal_view, release_approved=True)
