"""P1.5.11B context adequacy contract tests (P1.5.13 updated)."""
from __future__ import annotations

import pytest

from agentic_runtime.contracts.capability import create_verified_capability_evidence_record
from agentic_runtime.contracts.context import (
    ContextAdequacyReport,
    ContextAdequacyStatus,
    ContextBindingRef,
)
from agentic_runtime.contracts.evidence import build_evidence_ref
from agentic_runtime.contracts.trace import AurelTraceLog, TraceEventType, trace_event_ref
from agentic_runtime.contracts.verifier import VerifierKind, VerifierResult, VerifierResultStatus


CREATED_AT = "2026-06-22T00:00:00+00:00"


def _binding():
    return ContextBindingRef(
        context_id="context_001",
        context_type="test_context",
        source_refs=("source_ref_001",),
        assumptions=("test assumption",),
        created_at=CREATED_AT,
    )


def _report(status: ContextAdequacyStatus, *, score: float | None = None):
    return ContextAdequacyReport(
        context_adequacy_id=f"context_adequacy_{status.value}_001",
        context_binding_ref=_binding(),
        status=status,
        missing_context_flags=("missing source",) if status == ContextAdequacyStatus.INSUFFICIENT else (),
        uncertainty_notes=("partial context",) if status == ContextAdequacyStatus.PARTIAL else (),
        safe_to_act=status != ContextAdequacyStatus.UNSAFE,
        requires_operator_clarification=status == ContextAdequacyStatus.INSUFFICIENT,
        created_at=CREATED_AT,
        adequacy_score=score,
    )


def _verifier():
    log = AurelTraceLog(trace_id="trace_context_adequacy_test")
    event = log.append(
        event_type=TraceEventType.STUB_EXECUTION_COMPLETED,
        actor_type="test",
        actor_id="tester",
        payload_json={"execution_id": "execution_001", "status": "success"},
        timestamp=CREATED_AT,
    )
    ref = trace_event_ref(event)
    evidence = build_evidence_ref(
        evidence_id="evidence_001",
        source_trace_event_ref=ref,
        evidence_type="stub_execution",
        content={"execution_id": "execution_001", "status": "success"},
        summary="stub evidence",
    )
    return VerifierResult(
        verifier_id="verifier_pass_001",
        verifier_kind=VerifierKind.DETERMINISTIC,
        target_ref="execution_001",
        status=VerifierResultStatus.PASS,
        confidence=1.0,
        reason="stub verifier pass",
        limitations=("Verifier is limited to context adequacy tests.",),
        evidence_refs=(evidence,),
        source_trace_event_ref=ref,
        created_at=CREATED_AT,
    )


def _create_with_report(report: ContextAdequacyReport, limitations=("context limitation",)):
    verifier = _verifier()
    return create_verified_capability_evidence_record(
        capability_evidence_id="capability_evidence_001",
        capability_id="capability.test",
        source_trace_event_ref=verifier.source_trace_event_ref,
        source_event_hash=verifier.source_trace_event_ref.event_hash,
        evidence_refs=verifier.evidence_refs,
        verifier_result=verifier,
        context_binding_ref=report.context_binding_ref,
        context_adequacy_report=report,
        limitations=limitations,
        created_at=CREATED_AT,
    )


def test_unsafe_context_block_verified():
    report = _report(ContextAdequacyStatus.UNSAFE)
    with pytest.raises(ValueError, match="unsafe context"):
        _create_with_report(report)


def test_insufficient_context_block_verified():
    report = _report(ContextAdequacyStatus.INSUFFICIENT)
    with pytest.raises(ValueError, match="insufficient context"):
        _create_with_report(report, limitations=("acknowledge insufficient context",))


def test_partial_context_requires_limitations():
    report = _report(ContextAdequacyStatus.PARTIAL)
    with pytest.raises(ValueError, match="partial context"):
        _create_with_report(report, limitations=("irrelevant limitation",))

    record = _create_with_report(report, limitations=("partial context acknowledged",))
    assert record.context_adequacy_ref == report.context_adequacy_id


def test_adequate_context_allows_capability():
    report = _report(ContextAdequacyStatus.ADEQUATE)
    record = _create_with_report(report)
    assert record.context_adequacy_ref == report.context_adequacy_id
