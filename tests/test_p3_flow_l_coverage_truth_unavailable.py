"""P3-FLOW-L coverage summary / K consumption / truth-label audit /
unavailable ledger behavior tests.

A coverage summary is not proof, a K evaluation summary is not proof or
release approval, a truth-label audit is not Trace verification, and an
unavailable ledger implements nothing.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass

import pytest

from agentic_runtime.aurel_flow import (
    AurelFlowValidationError,
    BoundaryComplianceCategory,
    ContractCoverageArea,
    ContractCoverageStatus,
    FlowTruthLabel,
    HarnessScenarioKind,
    P3AuditStatus,
    P3FlowPack,
    P3PackCoverageStatus,
    P4HandoffReadinessCheck,
    QualityMetric,
    QualityMetricStatus,
    RuntimeInvariantKind,
    SchedulingIntentKind,
    SchedulingIntentReason,
    TruthLabelAuditCategory,
    UnavailableSystem,
    WorkflowAtomicUnitKind,
    assess_p4_handoff_readiness,
    audit_truth_labels,
    build_boundary_compliance_read_model,
    build_contract_coverage_matrix,
    build_default_p3_pack_coverage_items,
    build_harness_evaluation_suite,
    build_p3_coverage_summary,
    build_p3_seal_input_frame,
    build_runtime_invariant_read_model,
    build_runtime_quality_scorecard,
    build_unavailable_systems_ledger,
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
    summarize_k_evaluation,
)


def _k_seal_input_frame():
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
                status=ContractCoverageStatus.COVERED,
                evidence_note="tests/test_p3_flow_i_scheduling_intent.py",
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


def test_coverage_summary_counts_statuses_and_is_never_proof() -> None:
    items = tuple(
        item
        if item.pack is not P3FlowPack.P3_FLOW_K
        else create_p3_pack_coverage_item(
            pack=P3FlowPack.P3_FLOW_K,
            status=P3PackCoverageStatus.PARTIAL,
            evidence_note="hypothetical partial evidence",
        )
        for item in build_default_p3_pack_coverage_items()
    )
    summary = build_p3_coverage_summary(items)
    assert summary.covered_count == 11
    assert summary.partial_count == 1
    assert summary.missing_count == 0
    assert summary.fully_covered is False
    for forbidden_field in (
        "proof_available",
        "trace_verified",
        "production_ready",
    ):
        assert getattr(summary, forbidden_field) is False
        with pytest.raises(AurelFlowValidationError):
            dataclasses.replace(summary, **{forbidden_field: True})


def test_coverage_summary_must_be_total_over_a_to_l() -> None:
    items = build_default_p3_pack_coverage_items()
    with pytest.raises(AurelFlowValidationError) as excinfo:
        build_p3_coverage_summary(items[:-1])
    assert "P3-FLOW-L" in str(excinfo.value)
    with pytest.raises(AurelFlowValidationError):
        build_p3_coverage_summary(items + (items[0],))


def test_coverage_item_must_explain_itself() -> None:
    with pytest.raises(AurelFlowValidationError):
        create_p3_pack_coverage_item(
            pack=P3FlowPack.P3_FLOW_A,
            status=P3PackCoverageStatus.MISSING,
            evidence_note="   ",
        )


def test_k_evaluation_summary_consumes_the_frame_without_proof() -> None:
    frame = _k_seal_input_frame()
    summary = summarize_k_evaluation(frame)
    assert summary.seal_input_id == frame.seal_input_id
    assert summary.evaluation_run_id == frame.evaluation_run_id
    assert summary.readiness_finding_count == len(frame.readiness_findings)
    assert summary.blocking_risk_count == len(frame.blocking_risks)
    assert summary.seal_ready_candidate is frame.seal_ready_candidate
    assert summary.truth_label is FlowTruthLabel.READ_MODEL_ONLY
    for forbidden_field in (
        "evaluation_is_proof",
        "quality_score_approved_release",
        "p4_implemented",
        "final_seal_performed_by_k",
    ):
        assert getattr(summary, forbidden_field) is False
        with pytest.raises(AurelFlowValidationError):
            dataclasses.replace(summary, **{forbidden_field: True})


@dataclass(frozen=True)
class _OverclaimingFake:
    truth_label: FlowTruthLabel = FlowTruthLabel.LIVE
    production_ready: bool = True
    trace_verified: bool = True


def test_truth_label_audit_fails_fake_live_and_production_claims() -> None:
    read_model = audit_truth_labels((_OverclaimingFake(),))
    assert read_model.all_applicable_passed is False
    failing = set(read_model.failing_category_values)
    assert TruthLabelAuditCategory.NO_FAKE_LIVE.value in failing
    assert TruthLabelAuditCategory.NO_FAKE_TRACE_VERIFIED.value in failing
    assert TruthLabelAuditCategory.NO_FAKE_PRODUCTION_READY.value in failing
    fail_details = {
        finding.category: finding.detail
        for finding in read_model.findings
        if finding.status is P3AuditStatus.FAIL
    }
    assert "_OverclaimingFake" in fail_details[
        TruthLabelAuditCategory.NO_FAKE_LIVE
    ]


def test_truth_label_audit_passes_honest_l_objects() -> None:
    summary = build_p3_coverage_summary(
        build_default_p3_pack_coverage_items()
    )
    ledger = build_unavailable_systems_ledger()
    read_model = audit_truth_labels((summary, ledger, *ledger.entries))
    assert read_model.all_applicable_passed is True
    statuses = {
        finding.category: finding.status for finding in read_model.findings
    }
    assert (
        statuses[TruthLabelAuditCategory.NO_FAKE_LIVE] is P3AuditStatus.PASS
    )
    # ledger entries carry the UNAVAILABLE label explicitly
    assert (
        statuses[TruthLabelAuditCategory.UNAVAILABLE_EXPLICIT]
        is P3AuditStatus.PASS
    )
    # no audited subject uses DEV_FIXTURE here — honest NOT_APPLICABLE
    assert (
        statuses[TruthLabelAuditCategory.DEV_FIXTURE_EXPLICIT]
        is P3AuditStatus.NOT_APPLICABLE
    )
    for forbidden_field in (
        "live_claim_allowed",
        "trace_verified_claim_allowed",
        "production_ready_claim_allowed",
    ):
        with pytest.raises(AurelFlowValidationError):
            dataclasses.replace(read_model, **{forbidden_field: True})


def test_unavailable_ledger_is_total_and_implements_nothing() -> None:
    ledger = build_unavailable_systems_ledger()
    recorded = {entry.system for entry in ledger.entries}
    assert recorded == set(UnavailableSystem)
    for required in (
        UnavailableSystem.RUNTIME_SUBMIT_BRIDGE,
        UnavailableSystem.P4_EXECUTION,
        UnavailableSystem.P5_TRACE_VERIFICATION,
        UnavailableSystem.P9_CUSTOS_ENFORCEMENT,
        UnavailableSystem.PERSISTENCE,
        UnavailableSystem.REAL_WORKER_DISPATCH,
        UnavailableSystem.MODEL_INVOCATION,
        UnavailableSystem.TOOL_INVOCATION,
        UnavailableSystem.SANDBOX_EXECUTION,
        UnavailableSystem.API_SERVER,
        UnavailableSystem.DATABASE_EVENT_STORE,
    ):
        assert required in recorded
    for entry in ledger.entries:
        assert entry.truth_label is FlowTruthLabel.UNAVAILABLE
        assert entry.implemented is False
        assert entry.reason
        assert entry.future_owner
    with pytest.raises(AurelFlowValidationError):
        dataclasses.replace(ledger, entries=ledger.entries[:-1])
    for forbidden_field in (
        "unavailable_system_implemented",
        "runtime_submit_wired",
        "p4_implemented",
        "p5_implemented",
        "p9_implemented",
        "persistence_implemented",
    ):
        with pytest.raises(AurelFlowValidationError):
            dataclasses.replace(ledger, **{forbidden_field: True})


def test_unavailable_entry_cannot_claim_another_truth_label() -> None:
    ledger = build_unavailable_systems_ledger()
    with pytest.raises(AurelFlowValidationError):
        dataclasses.replace(
            ledger.entries[0], truth_label=FlowTruthLabel.LIVE
        )
    with pytest.raises(AurelFlowValidationError):
        dataclasses.replace(ledger.entries[0], implemented=True)
