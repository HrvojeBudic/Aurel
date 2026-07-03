"""P3-FLOW-K evaluation projection / P3 seal input behavior tests.

The projection is read-only (a UI quality score is not approval); the seal
input frame derives readiness findings and blocking risks deterministically
and is structurally not the final seal.
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
    RegressionGuardKind,
    RuntimeInvariantKind,
    SchedulingIntentKind,
    SchedulingIntentReason,
    WorkflowAtomicUnitKind,
    assess_p4_handoff_readiness,
    build_boundary_compliance_read_model,
    build_boundary_compliance_view_model,
    build_contract_coverage_matrix,
    build_coverage_matrix_view_model,
    build_evaluation_run_view_model,
    build_harness_evaluation_projection_envelope,
    build_harness_evaluation_suite,
    build_invariant_finding_view_model,
    build_p3_seal_input_frame,
    build_p3_seal_input_read_model,
    build_p4_handoff_readiness_view_model,
    build_quality_scorecard_view_model,
    build_regression_guard_read_model,
    build_regression_guard_view_model,
    build_runtime_invariant_read_model,
    build_runtime_quality_scorecard,
    create_contract_coverage_item,
    create_harness_evaluation_case,
    create_harness_scenario_fixture,
    create_quality_metric_item,
    create_scheduling_intent,
    create_workflow_atomic_unit,
    derive_harness_evaluation_run,
    evaluate_regression_guard_rail,
    probe_runtime_invariant,
    run_boundary_compliance_probe,
)

_UI_FALSE_FIELDS = (
    "frontend_mutation_allowed",
    "ui_quality_score_approval",
    "ui_harness_execution_allowed",
    "ui_production_ready_badge_authoritative",
    "api_server_implemented",
    "frontend_implemented",
)


def _bundle(*, clean: bool):
    fixture = create_harness_scenario_fixture(
        fixture_kind=HarnessScenarioKind.SCHEDULING_INTENT_FIXTURE,
        fixture_label="intent",
        target_contracts=("SchedulingIntent",),
    )
    run = derive_harness_evaluation_run(
        build_harness_evaluation_suite(
            suite_label="p3-eval",
            target_pack_range="P3.0-P3.18",
            cases=(
                create_harness_evaluation_case(case_label="c", fixture=fixture),
            ),
        )
    )
    coverage = build_contract_coverage_matrix(
        run=run,
        coverage_items=(
            create_contract_coverage_item(
                coverage_area=ContractCoverageArea.SCHEDULING_INTENT,
                status=ContractCoverageStatus.COVERED
                if clean
                else ContractCoverageStatus.MISSING,
                evidence_note="tests/test_p3_flow_i_scheduling_intent.py"
                if clean
                else "hypothetical gap",
            ),
        ),
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
    compliance = build_boundary_compliance_read_model(
        (
            run_boundary_compliance_probe(
                category=BoundaryComplianceCategory.NO_EXECUTION,
                subject=intent,
            ),
        )
    )
    invariants = build_runtime_invariant_read_model(
        (
            probe_runtime_invariant(
                invariant_kind=(
                    RuntimeInvariantKind.SCHEDULING_INTENT_IS_NOT_DISPATCH
                ),
                subject=intent,
            ),
        )
    )
    scorecard = build_runtime_quality_scorecard(
        run=run,
        metric_items=(
            create_quality_metric_item(
                metric=QualityMetric.SEAL_READINESS,
                status=QualityMetricStatus.PARTIAL,
                rationale="seal input prepared; L not run",
            ),
        ),
    )
    assessment = assess_p4_handoff_readiness(
        run=run,
        readiness_check_results=(
            (P4HandoffReadinessCheck.SCHEDULING_INTENT_EXISTS, True),
        ),
    )
    return run, coverage, compliance, invariants, scorecard, assessment


def _envelope():
    run, coverage, compliance, invariants, scorecard, assessment = _bundle(
        clean=True
    )
    guard_rm = build_regression_guard_read_model(
        (
            evaluate_regression_guard_rail(
                guard_kind=RegressionGuardKind.NO_NEW_EXECUTION_IN_P3
            ),
        )
    )
    return build_harness_evaluation_projection_envelope(
        run_view=build_evaluation_run_view_model(run),
        coverage_view=build_coverage_matrix_view_model(coverage),
        compliance_view=build_boundary_compliance_view_model(
            evaluation_run_id=run.evaluation_run_id, read_model=compliance
        ),
        invariant_view=build_invariant_finding_view_model(
            evaluation_run_id=run.evaluation_run_id, read_model=invariants
        ),
        scorecard_view=build_quality_scorecard_view_model(scorecard),
        p4_readiness_view=build_p4_handoff_readiness_view_model(assessment),
        guard_view=build_regression_guard_view_model(
            evaluation_run_id=run.evaluation_run_id, read_model=guard_rm
        ),
    )


def test_projection_envelope_is_deterministic_and_read_only() -> None:
    first = _envelope()
    second = _envelope()
    assert first.projection_envelope_id == second.projection_envelope_id
    assert first.truth_label is FlowTruthLabel.READ_MODEL_ONLY
    views = (
        first.run_view,
        first.coverage_view,
        first.compliance_view,
        first.invariant_view,
        first.scorecard_view,
        first.p4_readiness_view,
        first.guard_view,
    )
    for view in views:
        assert view is not None
        assert view.react_projection_only is True
        for forbidden_field in _UI_FALSE_FIELDS:
            assert getattr(view, forbidden_field) is False
            with pytest.raises(AurelFlowValidationError):
                dataclasses.replace(view, **{forbidden_field: True})


def test_projection_boundary_pins_score_is_not_approval() -> None:
    envelope = _envelope()
    boundary = envelope.boundary
    assert boundary.ui_quality_score_is_not_approval is True
    assert boundary.ui_harness_action_is_not_execution is True
    assert boundary.ui_readiness_badge_is_not_production_readiness is True
    assert boundary.runtime_source_of_truth == "python"
    with pytest.raises(AurelFlowValidationError):
        dataclasses.replace(boundary, ui_quality_score_is_not_approval=False)
    with pytest.raises(AurelFlowValidationError):
        dataclasses.replace(boundary, runtime_source_of_truth="react")


def _foreign_run():
    fixture = create_harness_scenario_fixture(
        fixture_kind=HarnessScenarioKind.P4_HANDOFF_FIXTURE,
        fixture_label="other",
        target_contracts=("P4HandoffClarityFrame",),
    )
    return derive_harness_evaluation_run(
        build_harness_evaluation_suite(
            suite_label="other-suite",
            target_pack_range="P3.18",
            cases=(
                create_harness_evaluation_case(case_label="o", fixture=fixture),
            ),
        )
    )


def test_projection_rejects_foreign_run_views() -> None:
    _run, coverage, *_rest = _bundle(clean=True)
    foreign = _foreign_run()
    assert foreign.evaluation_run_id != coverage.evaluation_run_id
    with pytest.raises(AurelFlowValidationError):
        build_harness_evaluation_projection_envelope(
            run_view=build_evaluation_run_view_model(foreign),
            coverage_view=build_coverage_matrix_view_model(coverage),
        )


def test_clean_inputs_yield_a_seal_ready_candidate_with_findings() -> None:
    run, coverage, compliance, invariants, scorecard, assessment = _bundle(
        clean=True
    )
    frame = build_p3_seal_input_frame(
        run=run,
        coverage_matrix=coverage,
        compliance_read_model=compliance,
        invariant_read_model=invariants,
        scorecard=scorecard,
        p4_assessment=assessment,
    )
    assert frame.seal_ready_candidate is True
    assert frame.blocking_risks == ()
    finding_labels = {f.finding_label for f in frame.readiness_findings}
    assert "COVERAGE_REPRESENTED" in finding_labels
    assert "BOUNDARY_COMPLIANCE_CLEAN" in finding_labels
    assert "INVARIANTS_SATISFIED" in finding_labels
    assert "P4_HANDOFF_READY_CANDIDATE" in finding_labels


def test_missing_coverage_becomes_a_blocking_risk() -> None:
    run, coverage, compliance, invariants, scorecard, assessment = _bundle(
        clean=False
    )
    frame = build_p3_seal_input_frame(
        run=run,
        coverage_matrix=coverage,
        compliance_read_model=compliance,
        invariant_read_model=invariants,
        scorecard=scorecard,
        p4_assessment=assessment,
    )
    assert frame.seal_ready_candidate is False
    assert {r.risk_label for r in frame.blocking_risks} == {"COVERAGE_GAPS"}
    for risk in frame.blocking_risks:
        assert risk.final_seal_performed is False


def test_seal_input_is_not_the_final_seal() -> None:
    run, coverage, compliance, invariants, scorecard, assessment = _bundle(
        clean=True
    )
    frame = build_p3_seal_input_frame(
        run=run,
        coverage_matrix=coverage,
        compliance_read_model=compliance,
        invariant_read_model=invariants,
        scorecard=scorecard,
        p4_assessment=assessment,
    )
    assert frame.requires_p3_flow_l is True
    for forbidden_field in (
        "final_seal_performed",
        "production_ready",
        "trace_verified",
    ):
        with pytest.raises(AurelFlowValidationError):
            dataclasses.replace(frame, **{forbidden_field: True})
    with pytest.raises(AurelFlowValidationError):
        dataclasses.replace(frame, requires_p3_flow_l=False)
    # a seal-ready candidate with blocking risks is contradictory
    read_model = build_p3_seal_input_read_model(frame)
    assert read_model.seal_ready_candidate is True
    assert read_model.blocking_risk_count == 0
    assert read_model.final_seal_performed is False


def test_seal_input_rejects_foreign_run_sources() -> None:
    run, _coverage, compliance, invariants, scorecard, assessment = _bundle(
        clean=True
    )
    foreign_coverage = build_contract_coverage_matrix(
        run=_foreign_run(),
        coverage_items=(
            create_contract_coverage_item(
                coverage_area=ContractCoverageArea.P4_HANDOFF_CLARITY,
                status=ContractCoverageStatus.COVERED,
                evidence_note="x",
            ),
        ),
    )
    assert foreign_coverage.evaluation_run_id != run.evaluation_run_id
    with pytest.raises(AurelFlowValidationError):
        build_p3_seal_input_frame(
            run=run,
            coverage_matrix=foreign_coverage,
            compliance_read_model=compliance,
            invariant_read_model=invariants,
            scorecard=scorecard,
            p4_assessment=assessment,
        )
