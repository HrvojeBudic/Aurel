"""P1.5.11B evidence strength verification tests (P1.5.13 updated)."""
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


def _verifier():
    log = AurelTraceLog(trace_id="trace_evidence_strength_test")
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
        limitations=("Verifier is limited to evidence strength tests.",),
        evidence_refs=(evidence,),
        source_trace_event_ref=ref,
        created_at=CREATED_AT,
    )


def _context():
    binding = ContextBindingRef(
        context_id="context_001",
        context_type="test_context",
        created_at=CREATED_AT,
    )
    return ContextAdequacyReport(
        context_adequacy_id="context_adequacy_adequate_001",
        context_binding_ref=binding,
        status=ContextAdequacyStatus.ADEQUATE,
        safe_to_act=True,
        created_at=CREATED_AT,
    )


def _create(strength: EvidenceStrengthLevel):
    verifier = _verifier()
    context = _context()
    return create_verified_capability_evidence_record(
        capability_evidence_id="capability_evidence_001",
        capability_id="capability.test",
        source_trace_event_ref=verifier.source_trace_event_ref,
        source_event_hash=verifier.source_trace_event_ref.event_hash,
        evidence_refs=verifier.evidence_refs,
        verifier_result=verifier,
        context_binding_ref=context.context_binding_ref,
        context_adequacy_report=context,
        evidence_strength=strength,
        limitations=("context limitation",),
        created_at=CREATED_AT,
    )


def test_verified_capability_requires_strong_or_verified_evidence_strength():
    for invalid in (EvidenceStrengthLevel.NONE, EvidenceStrengthLevel.WEAK, EvidenceStrengthLevel.MODERATE):
        with pytest.raises(ValueError, match="evidence_strength"):
            _create(invalid)

    record = _create(EvidenceStrengthLevel.VERIFIED)
    assert record.evidence_strength == EvidenceStrengthLevel.VERIFIED
