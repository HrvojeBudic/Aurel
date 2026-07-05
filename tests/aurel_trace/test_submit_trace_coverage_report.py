"""P5.7 — Submit trace coverage report and P5-C recommendations."""

from __future__ import annotations

import pytest

from agentic_runtime.aurel_trace import (
    AurelTraceError,
    SubmitCoverageStatus,
    SubmitTraceCoverageReport,
    build_submit_trace_coverage_audit,
    build_submit_trace_coverage_report,
)


def _report():
    return build_submit_trace_coverage_report(build_submit_trace_coverage_audit())


def test_report_lists_all_status_buckets():
    report = _report()
    assert report.covered
    assert report.partial
    assert report.missing
    # unsupported may be empty for the default map; the field must still exist.
    assert isinstance(report.unsupported, tuple)


def test_missing_and_partial_become_p5c_recommendations():
    report = _report()
    recommended_kinds = {
        gap.requirement.requirement_kind for gap in report.p5c_recommendations
    }
    gap_kinds = {
        r.requirement_kind for r in report.partial + report.missing + report.unsupported
    }
    assert recommended_kinds == gap_kinds
    for gap in report.p5c_recommendations:
        assert gap.p5c_recommendation.strip()
        assert gap.reason.strip()


def test_report_does_not_claim_complete_coverage():
    report = _report()
    assert report.claims_complete_coverage is False


def test_report_cannot_claim_complete_while_required_gap_remains():
    report = _report()
    with pytest.raises(AurelTraceError):
        SubmitTraceCoverageReport(
            report_id="r",
            covered=report.covered,
            partial=report.partial,
            missing=report.missing,
            unsupported=report.unsupported,
            p5c_recommendations=report.p5c_recommendations,
            claims_complete_coverage=True,
        )


def test_coverage_percent_is_deterministic_and_bounded():
    a = _report()
    b = _report()
    assert a.coverage_percent == b.coverage_percent
    assert a.coverage_percent is not None
    assert 0.0 <= a.coverage_percent <= 100.0
    # Gaps in required evidence mean coverage is honestly below 100%.
    assert a.coverage_percent < 100.0


def test_recommendations_reference_p5c_owner():
    report = _report()
    p5c_gaps = [
        gap
        for gap in report.p5c_recommendations
        if gap.requirement.current_status
        in (SubmitCoverageStatus.PARTIAL, SubmitCoverageStatus.MISSING)
    ]
    assert p5c_gaps
    for gap in p5c_gaps:
        assert "P5-TRACE-C" in gap.p5c_recommendation
