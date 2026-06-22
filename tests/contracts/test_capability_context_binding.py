"""P1.5.11B capability evidence trace/context binding tests (P1.5.13 updated)."""
from __future__ import annotations

import pytest

from agentic_runtime.contracts.capability import (
    EvidenceStrengthLevel,
    create_verified_capability_evidence_record,
)
from agentic_runtime.contracts.context import (
    ContextAdequacyReport,
    ContextAdequacyStatus,
    ContextBindingRef,
)
from agentic_runtime.contracts.evidence import build_evidence_ref
from agentic_runtime.contracts.trace import AurelTraceLog, TraceEventType, trace_event_ref
from agentic_runtime.contracts.verifier import VerifierKind, VerifierResult, VerifierResultStatus


CREATED_AT = "2026-06-22T00:00:00+00:00"


def _trace_ref():
    log = AurelTraceLog(trace_id="trace_context_binding_test")
    event = log.append(
        event_type=TraceEventType.STUB_EXECUTION_COMPLETED,
        actor_type="test",
        actor_id="tester",
        payload_json={"execution_id": "execution_001", "status": "success"},
        timestamp=CREATED_AT,
    )
    return trace_event_ref(event)


def _evidence_ref():
    ref = _trace_ref()
    return build_evidence_ref(
        evidence_id="evidence_001",
        source_trace_event_ref=ref,
        evidence_type="stub_execution",
        content={"execution_id": "execution_001", "status": "success"},
        summary="stub execution evidence",
    )


def _verifier(status: VerifierResultStatus = VerifierResultStatus.PASS):
    evidence = _evidence_ref()
    return VerifierResult(
        verifier_id=f"verifier_{status.value}_001",
        verifier_kind=VerifierKind.DETERMINISTIC,
        target_ref="execution_001",
        status=status,
        confidence=1.0 if status == VerifierResultStatus.PASS else 0.0,
        reason=f"stub verifier {status.value}",
        limitations=("Verifier is limited to deterministic context binding tests.",),
        evidence_refs=(evidence,),
        source_trace_event_ref=evidence.source_trace_event_ref,
        created_at=CREATED_AT,
    )


def _context(status: ContextAdequacyStatus = ContextAdequacyStatus.ADEQUATE):
    binding = ContextBindingRef(
        context_id="context_001",
        context_type="test_context",
        source_refs=("source_ref_001",),
        assumptions=("test context",),
        created_at=CREATED_AT,
    )
    return ContextAdequacyReport(
        context_adequacy_id=f"context_adequacy_{status.value}_001",
        context_binding_ref=binding,
        status=status,
        missing_context_flags=("missing source",) if status == ContextAdequacyStatus.INSUFFICIENT else (),
        safe_to_act=status != ContextAdequacyStatus.UNSAFE,
        requires_operator_clarification=status == ContextAdequacyStatus.INSUFFICIENT,
        created_at=CREATED_AT,
        adequacy_score=1.0,
    )


def _create(verifier: VerifierResult, context_report: ContextAdequacyReport | None = None, **kw):
    context_report = context_report or _context()
    source_trace_event_ref = kw.pop("source_trace_event_ref", verifier.source_trace_event_ref)
    source_event_hash = kw.pop("source_event_hash", source_trace_event_ref.event_hash if source_trace_event_ref else None)
    return create_verified_capability_evidence_record(
        capability_evidence_id="capability_evidence_001",
        capability_id="capability.test",
        source_trace_event_ref=source_trace_event_ref,
        source_event_hash=source_event_hash,
        evidence_refs=kw.pop("evidence_refs", verifier.evidence_refs),
        verifier_result=kw.pop("verifier_result", verifier),
        context_binding_ref=context_report.context_binding_ref if context_report else None,
        context_adequacy_report=context_report,
        evidence_strength=kw.pop("evidence_strength", EvidenceStrengthLevel.VERIFIED),
        limitations=kw.pop("limitations", ("stub capability context limitation",)),
        created_at=CREATED_AT,
    )


def test_verified_capability_requires_source_event_hash():
    verifier = _verifier()
    with pytest.raises(ValueError, match="source_event_hash"):
        _create(verifier, source_event_hash=None)


def test_source_event_hash_must_match_trace_event_ref():
    verifier = _verifier()
    with pytest.raises(ValueError, match="source_event_hash"):
        _create(verifier, source_event_hash="wrong_hash")


def test_verified_capability_requires_context_limitations_when_context_partial():
    verifier = _verifier()
    report = _context(ContextAdequacyStatus.PARTIAL)
    with pytest.raises(ValueError, match="partial context"):
        _create(verifier, context_report=report, limitations=("no relevant caveat",))

    record = _create(
        verifier,
        context_report=report,
        limitations=("partial context limitation acknowledged",),
    )
    assert record.context_adequacy_ref == report.context_adequacy_id


def test_unsafe_context_blocks_verified_capability():
    verifier = _verifier()
    with pytest.raises(ValueError, match="unsafe context"):
        _create(verifier, context_report=_context(ContextAdequacyStatus.UNSAFE))


def test_insufficient_context_blocks_verified_capability():
    verifier = _verifier()
    with pytest.raises(ValueError, match="insufficient context"):
        _create(verifier, context_report=_context(ContextAdequacyStatus.INSUFFICIENT))


def test_projection_only_source_cannot_verify_capability():
    verifier = _verifier()
    with pytest.raises(ValueError, match="source_trace_event_ref"):
        _create(
            verifier,
            source_trace_event_ref=None,
            source_event_hash=verifier.source_trace_event_ref.event_hash,
        )
