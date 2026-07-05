"""P5.8 — Runtime submit trace canonical bridge (adapter over P5-B coverage)."""

from __future__ import annotations

import pytest

from agentic_runtime.aurel_trace import (
    AurelTraceError,
    EvidenceStatus,
    RuntimeSubmitTraceBinding,
    RuntimeSubmitTraceBridge,
    SubmitEvidenceRequirementKind,
    TraceBindingCoverageStatus,
    TraceTruthLabel,
    binding_from_submit_coverage_report,
    build_runtime_submit_trace_binding,
    build_submit_trace_coverage_audit,
    build_submit_trace_coverage_report,
    missing_evidence_from_coverage_report,
    runtime_submit_binding_status,
    summarize_binding_coverage,
)


def _report():
    return build_submit_trace_coverage_report(build_submit_trace_coverage_audit())


def test_binding_consumes_p5b_report():
    binding = build_runtime_submit_trace_binding(_report())
    assert isinstance(binding, RuntimeSubmitTraceBinding)
    # Every one of the 14 requirement kinds becomes an evidence ref.
    assert len(binding.evidence_refs) == len(list(SubmitEvidenceRequirementKind))


def test_binding_preserves_missing_and_partial_from_report():
    binding = build_runtime_submit_trace_binding(_report())
    assert len(binding.missing_evidence) == 2
    assert len(binding.partial_evidence) == 5
    for ref in binding.missing_evidence:
        assert ref.status is EvidenceStatus.MISSING
        assert ref.missing_reason


def test_binding_coverage_is_partial_not_verified():
    binding = build_runtime_submit_trace_binding(_report())
    assert binding.coverage_status is TraceBindingCoverageStatus.PARTIAL
    assert runtime_submit_binding_status(binding) is TraceBindingCoverageStatus.PARTIAL
    assert binding.truth_label is TraceTruthLabel.TRACE_BOUND
    assert binding.trace_verified is False


def test_named_slots_are_populated_by_kind():
    binding = build_runtime_submit_trace_binding(_report())
    assert binding.verifier_evidence_ref is not None
    assert binding.verifier_evidence_ref.status is EvidenceStatus.PRESENT
    assert binding.command_evidence_ref.status is EvidenceStatus.PARTIAL
    assert binding.rollback_evidence_ref.status is EvidenceStatus.MISSING


def test_binding_side_effect_booleans_unconstructible():
    binding = build_runtime_submit_trace_binding(_report())
    with pytest.raises(AurelTraceError):
        RuntimeSubmitTraceBinding(
            binding_id="b",
            coverage_status=TraceBindingCoverageStatus.PARTIAL,
            evidence_refs=binding.evidence_refs,
            submits_command=True,
        )


def test_complete_coverage_does_not_mean_trace_verified():
    # Force a report where every requirement is COVERED, then bind it.
    from agentic_runtime.aurel_trace.submit_coverage import (
        SubmitCoverageStatus,
        build_submit_trace_coverage_audit as _audit,
    )

    kinds = list(SubmitEvidenceRequirementKind)
    all_covered = {
        k: (SubmitCoverageStatus.COVERED, True, True, "P5-TRACE-A", "present")
        for k in kinds
    }
    audit = _audit(evidence_map=all_covered)
    report = build_submit_trace_coverage_report(audit)
    binding = build_runtime_submit_trace_binding(report)
    assert binding.coverage_status is TraceBindingCoverageStatus.COMPLETE
    # COMPLETE coverage is not a verification claim.
    assert binding.truth_label is TraceTruthLabel.TRACE_BOUND
    assert binding.trace_verified is False


def test_receipt_ids_promote_present_evidence_to_integrity_verified():
    report = _report()
    covered_kind = report.covered[0].requirement_kind
    binding = build_runtime_submit_trace_binding(
        report, receipt_ids={covered_kind: "trcpt-real-receipt"}
    )
    match = [
        r
        for r in binding.evidence_refs
        if r.source_object_id == covered_kind.value
    ][0]
    assert match.status is EvidenceStatus.TRACE_INTEGRITY_VERIFIED
    assert match.verification_receipt_id == "trcpt-real-receipt"


def test_missing_evidence_helper_lists_gaps():
    gaps = missing_evidence_from_coverage_report(_report())
    # 5 partial + 2 missing = 7 gap refs.
    assert len(gaps) == 7


def test_bridge_object_is_read_only_and_deterministic():
    bridge = RuntimeSubmitTraceBridge()
    assert bridge.calls_runtime_submit is False
    assert bridge.calls_tool_dispatch is False
    assert bridge.appends_trace is False
    a = bridge.build_binding(_report())
    b = binding_from_submit_coverage_report(_report())
    assert a.binding_id == b.binding_id


def test_bridge_side_effect_booleans_unconstructible():
    with pytest.raises(AurelTraceError):
        RuntimeSubmitTraceBridge(calls_runtime_submit=True)


def test_summary_counts_match_report():
    summary = summarize_binding_coverage(build_runtime_submit_trace_binding(_report()))
    assert summary.present_count == 7
    assert summary.partial_count == 5
    assert summary.missing_count == 2
    assert summary.total == 14
