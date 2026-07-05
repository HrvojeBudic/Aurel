"""P5.12 — Trace query read model reflects resolver decisions (read-only)."""

from __future__ import annotations

import pytest

from agentic_runtime.aurel_trace import (
    AurelTraceError,
    TraceQueryReadModel,
    resolve_trace_target,
)
from agentic_runtime.aurel_trace.trace_resolver import (
    TraceVerificationStatus,
    TraceVerificationTargetKind,
)
from agentic_runtime.aurel_trace.trace_demo import build_demo_trace_substrate


def _model():
    substrate = build_demo_trace_substrate()
    return TraceQueryReadModel(
        read_model_id="test-rm", decisions=substrate.decisions
    ), substrate


def test_summary_reflects_decision_status_exactly():
    model, substrate = _model()
    for decision in substrate.decisions:
        summary = model.summarize_verification(decision)
        assert summary.verification_status is decision.status
        assert summary.verified is decision.verified
        assert summary.decision_id == decision.decision_id


def test_query_model_cannot_upgrade_a_partial_decision():
    model, substrate = _model()
    partial = next(
        d for d in substrate.decisions if d.status is TraceVerificationStatus.PARTIAL
    )
    summary = model.summarize_trace_binding(partial)
    assert summary.verification_status is TraceVerificationStatus.PARTIAL
    assert summary.verified is False
    # missing evidence preserved
    assert summary.missing_evidence == partial.missing_evidence
    assert summary.missing_evidence


def test_audit_counts_are_deterministic():
    model, _ = _model()
    a = model.summarize_audit()
    b = model.summarize_audit()
    assert a.to_dict() == b.to_dict()
    assert a.targets_checked == 2
    assert a.verified_count == 1
    assert a.partial_count == 1


def test_blocking_findings_and_reason_surface_in_summary(demo_run_ref, demo_envelopes):
    from agentic_runtime.aurel_trace.trace_verify import (
        TraceFindingSeverity,
        TraceHashFinding,
        TraceHashFindingKind,
    )

    finding = TraceHashFinding(
        finding_id="f1",
        finding_kind=TraceHashFindingKind.ENTRY_HASH_MISMATCH,
        severity=TraceFindingSeverity.ERROR,
        message="entry hash mismatch",
    )
    decision = resolve_trace_target(
        target_kind=TraceVerificationTargetKind.TRACE_RUN,
        target_id="run-blocked",
        findings=[finding],
    )
    model = TraceQueryReadModel(read_model_id="rm", decisions=(decision,))
    summary = model.summarize_trace_run(decision)
    assert summary.verification_status is TraceVerificationStatus.DENIED
    assert "entry hash mismatch" in summary.blocking_findings


def test_read_model_is_read_only():
    with pytest.raises(AurelTraceError):
        TraceQueryReadModel(read_model_id="rm", decides_verification=True)
    with pytest.raises(AurelTraceError):
        TraceQueryReadModel(read_model_id="rm", mutates=True)
