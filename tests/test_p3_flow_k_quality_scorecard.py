"""P3-FLOW-K quality scorecard / regression guard rail behavior tests.

A quality score is advisory — never proof, release approval, or production
readiness; a regression guard reports risk and never enforces CI.
"""

from __future__ import annotations

import dataclasses

import pytest

from agentic_runtime.aurel_flow import (
    AurelFlowValidationError,
    HarnessScenarioKind,
    QualityMetric,
    QualityMetricStatus,
    RegressionGuardKind,
    RegressionGuardSeverity,
    RegressionGuardStatus,
    build_harness_evaluation_suite,
    build_quality_scorecard_read_model,
    build_regression_guard_read_model,
    build_runtime_quality_scorecard,
    create_harness_evaluation_case,
    create_harness_scenario_fixture,
    create_quality_metric_item,
    create_regression_guard_finding,
    derive_harness_evaluation_run,
    evaluate_regression_guard_rail,
)


def _run():
    fixture = create_harness_scenario_fixture(
        fixture_kind=HarnessScenarioKind.READY_NODE_FIXTURE,
        fixture_label="ready",
        target_contracts=("WorkflowGraph",),
    )
    return derive_harness_evaluation_run(
        build_harness_evaluation_suite(
            suite_label="s",
            target_pack_range="P3",
            cases=(
                create_harness_evaluation_case(case_label="c", fixture=fixture),
            ),
        )
    )


def _scorecard():
    return build_runtime_quality_scorecard(
        run=_run(),
        metric_items=(
            create_quality_metric_item(
                metric=QualityMetric.BOUNDARY_CLARITY,
                status=QualityMetricStatus.STRONG,
                rationale="every pack carries fail-closed boundary booleans",
            ),
            create_quality_metric_item(
                metric=QualityMetric.TEST_COVERAGE,
                status=QualityMetricStatus.ACCEPTABLE,
                rationale="behavior-first tests per pack",
            ),
            create_quality_metric_item(
                metric=QualityMetric.SEAL_READINESS,
                status=QualityMetricStatus.PARTIAL,
                rationale="seal input exists; L not run",
            ),
        ),
    )


def test_scorecard_is_deterministic_and_advisory_only() -> None:
    first = _scorecard()
    second = _scorecard()
    assert first.scorecard_id == second.scorecard_id
    assert first.advisory_only is True
    for forbidden_field in (
        "score_is_proof",
        "release_approved",
        "production_ready",
        "operator_approval_granted",
    ):
        assert getattr(first, forbidden_field) is False
        with pytest.raises(AurelFlowValidationError):
            dataclasses.replace(first, **{forbidden_field: True})
    with pytest.raises(AurelFlowValidationError):
        dataclasses.replace(first, advisory_only=False)


def test_metric_item_requires_rationale_and_unique_metrics() -> None:
    with pytest.raises(AurelFlowValidationError):
        create_quality_metric_item(
            metric=QualityMetric.DETERMINISM,
            status=QualityMetricStatus.STRONG,
            rationale="",
        )
    item = create_quality_metric_item(
        metric=QualityMetric.DETERMINISM,
        status=QualityMetricStatus.STRONG,
        rationale="stable-hash ids everywhere",
    )
    with pytest.raises(AurelFlowValidationError):
        build_runtime_quality_scorecard(run=_run(), metric_items=(item, item))


def test_quality_status_vocabulary_has_no_approval_member() -> None:
    values = {status.value for status in QualityMetricStatus}
    for forbidden in ("APPROVED", "RELEASED", "PRODUCTION_READY", "PROVEN"):
        assert forbidden not in values


def test_scorecard_read_model_surfaces_weak_metrics() -> None:
    scorecard = build_runtime_quality_scorecard(
        run=_run(),
        metric_items=(
            create_quality_metric_item(
                metric=QualityMetric.REPORT_COVERAGE,
                status=QualityMetricStatus.WEAK,
                rationale="one report section thin",
            ),
            create_quality_metric_item(
                metric=QualityMetric.DX_COMPLEXITY_RISK,
                status=QualityMetricStatus.MISSING,
                rationale="not yet rated",
            ),
        ),
    )
    read_model = build_quality_scorecard_read_model(scorecard)
    assert read_model.weak_or_missing_metric_values == (
        "DX_COMPLEXITY_RISK",
        "REPORT_COVERAGE",
    )
    assert read_model.advisory_only is True
    assert read_model.release_approved is False


def test_guard_rail_status_derives_from_finding_severity() -> None:
    clean = evaluate_regression_guard_rail(
        guard_kind=RegressionGuardKind.NO_NEW_EXECUTION_IN_P3
    )
    assert clean.status is RegressionGuardStatus.PASS
    warned = evaluate_regression_guard_rail(
        guard_kind=RegressionGuardKind.NO_BROAD_DSL_EXPANSION_IN_K,
        findings=(
            create_regression_guard_finding(
                guard_kind=RegressionGuardKind.NO_BROAD_DSL_EXPANSION_IN_K,
                severity=RegressionGuardSeverity.WARNING,
                detail="K added ~50 exports; watch object growth",
            ),
        ),
    )
    assert warned.status is RegressionGuardStatus.WARNING
    failed = evaluate_regression_guard_rail(
        guard_kind=RegressionGuardKind.NO_FAKE_LIVE_LABEL,
        findings=(
            create_regression_guard_finding(
                guard_kind=RegressionGuardKind.NO_FAKE_LIVE_LABEL,
                severity=RegressionGuardSeverity.FAIL,
                detail="hypothetical LIVE label detected",
            ),
        ),
    )
    assert failed.status is RegressionGuardStatus.FAIL


def test_guard_rail_reports_only_and_never_enforces_ci() -> None:
    rail = evaluate_regression_guard_rail(
        guard_kind=RegressionGuardKind.NO_NEW_AUTHORITY_IN_P3
    )
    assert rail.report_only is True
    for forbidden_field in ("ci_enforced", "git_blocked", "runtime_mutated"):
        assert getattr(rail, forbidden_field) is False
        with pytest.raises(AurelFlowValidationError):
            dataclasses.replace(rail, **{forbidden_field: True})
    with pytest.raises(AurelFlowValidationError):
        dataclasses.replace(rail, report_only=False)


def test_guard_rail_rejects_foreign_kind_findings() -> None:
    finding = create_regression_guard_finding(
        guard_kind=RegressionGuardKind.NO_FAKE_LIVE_LABEL,
        severity=RegressionGuardSeverity.FAIL,
        detail="x",
    )
    with pytest.raises(AurelFlowValidationError):
        evaluate_regression_guard_rail(
            guard_kind=RegressionGuardKind.NO_NEW_NETWORK_IN_P3,
            findings=(finding,),
        )


def test_guard_read_model_aggregates_failures() -> None:
    rails = (
        evaluate_regression_guard_rail(
            guard_kind=RegressionGuardKind.NO_NEW_EXECUTION_IN_P3
        ),
        evaluate_regression_guard_rail(
            guard_kind=RegressionGuardKind.NO_PRODUCTION_READY_CLAIM,
            findings=(
                create_regression_guard_finding(
                    guard_kind=RegressionGuardKind.NO_PRODUCTION_READY_CLAIM,
                    severity=RegressionGuardSeverity.FAIL,
                    detail="hypothetical claim",
                ),
            ),
        ),
    )
    read_model = build_regression_guard_read_model(rails)
    assert read_model.guard_rail_count == 2
    assert read_model.failing_guard_kind_values == (
        "NO_PRODUCTION_READY_CLAIM",
    )
    assert read_model.all_passed is False
    assert read_model.ci_enforced is False
