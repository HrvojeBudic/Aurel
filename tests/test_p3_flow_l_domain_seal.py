"""P3-FLOW-L domain seal behavior tests.

The P3 domain seal closes AurelFlow as a non-executing control-plane
grammar: sealing is fail-closed over coverage gaps and K blocking risks,
and a sealed P3 is never production-ready, release-approved, proven, or
authorized.
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
    P3FlowPack,
    P3PackCoverageStatus,
    P4HandoffReadinessCheck,
    QualityMetric,
    QualityMetricStatus,
    RuntimeInvariantKind,
    SchedulingIntentKind,
    SchedulingIntentReason,
    WorkflowAtomicUnitKind,
    assess_p4_handoff_readiness,
    build_boundary_compliance_read_model,
    build_contract_coverage_matrix,
    build_default_p3_pack_coverage_items,
    build_harness_evaluation_suite,
    build_p3_coverage_summary,
    build_p3_seal_input_frame,
    build_runtime_invariant_read_model,
    build_runtime_quality_scorecard,
    create_contract_coverage_item,
    create_harness_evaluation_case,
    create_harness_scenario_fixture,
    create_p3_pack_coverage_item,
    create_quality_metric_item,
    create_scheduling_intent,
    create_workflow_atomic_unit,
    derive_harness_evaluation_run,
    probe_runtime_invariant,
    run_boundary_compliance_probe,
    seal_p3_domain,
    summarize_k_evaluation,
)

_SEAL_FALSE_FIELDS = (
    "production_ready",
    "release_approved",
    "live_path_available",
    "trace_verified",
    "proof_available",
    "authority_granted",
    "permission_granted",
    "p4_implemented",
    "p5_implemented",
    "p9_implemented",
    "runtime_submit_wired",
    "execution_available",
    "workflow_executed",
    "dispatch_available",
    "persistence_implemented",
)


def _k_seal_input_frame(*, clean: bool):
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
                rationale="seal input prepared for L",
            ),
        ),
    )
    assessment = assess_p4_handoff_readiness(
        run=run,
        readiness_check_results=(
            (P4HandoffReadinessCheck.SCHEDULING_INTENT_EXISTS, True),
        ),
    )
    return build_p3_seal_input_frame(
        run=run,
        coverage_matrix=coverage,
        compliance_read_model=compliance,
        invariant_read_model=invariants,
        scorecard=scorecard,
        p4_assessment=assessment,
    )


def _clean_seal():
    coverage_summary = build_p3_coverage_summary(
        build_default_p3_pack_coverage_items()
    )
    k_summary = summarize_k_evaluation(_k_seal_input_frame(clean=True))
    return seal_p3_domain(
        coverage_summary=coverage_summary,
        k_evaluation_summary=k_summary,
    )


def test_clean_inputs_seal_p3_as_control_plane_only() -> None:
    seal = _clean_seal()
    assert seal.p3_control_plane_sealed is True
    assert seal.truth_label is FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE
    assert seal.sealed_pack_values == tuple(
        pack.value for pack in P3FlowPack
    )
    assert seal.sealed_pack_values[0] == "P3-FLOW-A"
    assert seal.sealed_pack_values[-1] == "P3-FLOW-L"
    for forbidden_field in _SEAL_FALSE_FIELDS:
        assert getattr(seal, forbidden_field) is False


def test_seal_is_deterministic() -> None:
    assert _clean_seal().seal_id == _clean_seal().seal_id


def test_seal_boundary_booleans_fail_closed() -> None:
    seal = _clean_seal()
    with pytest.raises(AurelFlowValidationError):
        dataclasses.replace(seal, p3_control_plane_sealed=False)
    for forbidden_field in _SEAL_FALSE_FIELDS:
        with pytest.raises(AurelFlowValidationError):
            dataclasses.replace(seal, **{forbidden_field: True})


def test_missing_pack_coverage_rejects_the_seal() -> None:
    items = tuple(
        item
        if item.pack is not P3FlowPack.P3_FLOW_F
        else create_p3_pack_coverage_item(
            pack=P3FlowPack.P3_FLOW_F,
            status=P3PackCoverageStatus.MISSING,
            evidence_note="hypothetical missing pack",
        )
        for item in build_default_p3_pack_coverage_items()
    )
    coverage_summary = build_p3_coverage_summary(items)
    assert coverage_summary.missing_count == 1
    k_summary = summarize_k_evaluation(_k_seal_input_frame(clean=True))
    with pytest.raises(AurelFlowValidationError) as excinfo:
        seal_p3_domain(
            coverage_summary=coverage_summary,
            k_evaluation_summary=k_summary,
        )
    assert "P3-FLOW-F=MISSING" in str(excinfo.value)


def test_k_blocking_risks_reject_the_seal() -> None:
    coverage_summary = build_p3_coverage_summary(
        build_default_p3_pack_coverage_items()
    )
    risky_summary = summarize_k_evaluation(_k_seal_input_frame(clean=False))
    assert risky_summary.blocking_risk_count > 0
    assert risky_summary.seal_ready_candidate is False
    with pytest.raises(AurelFlowValidationError):
        seal_p3_domain(
            coverage_summary=coverage_summary,
            k_evaluation_summary=risky_summary,
        )


def test_unavailable_coverage_is_explicit_but_does_not_block_the_seal() -> None:
    items = tuple(
        item
        if item.pack is not P3FlowPack.P3_FLOW_L
        else create_p3_pack_coverage_item(
            pack=P3FlowPack.P3_FLOW_L,
            status=P3PackCoverageStatus.UNAVAILABLE,
            evidence_note="future system honestly absent",
        )
        for item in build_default_p3_pack_coverage_items()
    )
    coverage_summary = build_p3_coverage_summary(items)
    assert coverage_summary.unavailable_count == 1
    assert coverage_summary.fully_covered is False
    seal = seal_p3_domain(
        coverage_summary=coverage_summary,
        k_evaluation_summary=summarize_k_evaluation(
            _k_seal_input_frame(clean=True)
        ),
    )
    assert seal.p3_control_plane_sealed is True
    assert seal.production_ready is False
