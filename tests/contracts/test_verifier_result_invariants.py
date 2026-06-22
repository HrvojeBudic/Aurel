"""P1.5.11A VerifierResult invariant tests (P1.5.13 updated)."""
from __future__ import annotations

import pytest

from agentic_runtime.contracts.evidence import build_evidence_ref
from agentic_runtime.contracts.trace import AurelTraceLog, TraceEventType, trace_event_ref
from agentic_runtime.contracts.verifier import (
    VerifierKind,
    VerifierResult,
    VerifierResultStatus,
)

CREATED_AT = "2026-06-22T00:00:00+00:00"


def _trace_ref():
    log = AurelTraceLog(trace_id="trace_verifier_contract_test")
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


def test_verifier_pass_requires_evidence_refs():
    ref = _trace_ref()
    with pytest.raises(ValueError, match="evidence_refs"):
        VerifierResult(
            verifier_id="verifier_001",
            verifier_kind=VerifierKind.DETERMINISTIC,
            target_ref="execution_001",
            status=VerifierResultStatus.PASS,
            confidence=1.0,
            reason="pass without evidence is invalid",
            limitations=("stub limitation",),
            evidence_refs=(),
            source_trace_event_ref=ref,
            created_at=CREATED_AT,
        )


def test_verifier_pass_requires_limitations():
    evidence = _evidence_ref()
    with pytest.raises(ValueError, match="limitations"):
        VerifierResult(
            verifier_id="verifier_001",
            verifier_kind=VerifierKind.DETERMINISTIC,
            target_ref="execution_001",
            status=VerifierResultStatus.PASS,
            confidence=1.0,
            reason="pass without limitations is invalid",
            limitations=(),
            evidence_refs=(evidence,),
            source_trace_event_ref=evidence.source_trace_event_ref,
            created_at=CREATED_AT,
        )


def test_verifier_confidence_range():
    evidence = _evidence_ref()
    with pytest.raises(ValueError, match="confidence"):
        VerifierResult(
            verifier_id="verifier_001",
            verifier_kind=VerifierKind.DETERMINISTIC,
            target_ref="execution_001",
            status=VerifierResultStatus.PASS,
            confidence=1.5,
            reason="confidence out of range",
            limitations=("stub limitation",),
            evidence_refs=(evidence,),
            source_trace_event_ref=evidence.source_trace_event_ref,
            created_at=CREATED_AT,
        )


def test_failed_verifier_can_exist_with_limitations_without_evidence():
    ref = _trace_ref()
    result = VerifierResult(
        verifier_id="verifier_failed_001",
        verifier_kind=VerifierKind.DETERMINISTIC,
        target_ref="execution_001",
        status=VerifierResultStatus.FAIL,
        confidence=0.0,
        reason="stub failure",
        limitations=("failure is still limited to deterministic stub verifier",),
        evidence_refs=(),
        source_trace_event_ref=ref,
        created_at=CREATED_AT,
    )
    assert result.status == VerifierResultStatus.FAIL


def test_verifier_requires_reason():
    ref = _trace_ref()
    with pytest.raises(ValueError, match="reason"):
        VerifierResult(
            verifier_id="verifier_no_reason",
            verifier_kind=VerifierKind.DETERMINISTIC,
            target_ref="execution_001",
            status=VerifierResultStatus.PASS,
            confidence=1.0,
            reason="",
            limitations=("stub limitation",),
            evidence_refs=(_evidence_ref(),),
            source_trace_event_ref=ref,
            created_at=CREATED_AT,
        )


def test_verifier_serialization_includes_verifier_kind():
    from agentic_runtime.contracts.verifier import verifier_result_to_dict

    evidence = _evidence_ref()
    result = VerifierResult(
        verifier_id="verifier_serial_001",
        verifier_kind=VerifierKind.EVIDENCE_INTEGRITY,
        target_ref="execution_001",
        status=VerifierResultStatus.PASS,
        confidence=1.0,
        reason="test serialization",
        limitations=("stub limitation",),
        evidence_refs=(evidence,),
        source_trace_event_ref=evidence.source_trace_event_ref,
        created_at=CREATED_AT,
    )
    d = verifier_result_to_dict(result)
    assert d["verifier_kind"] == "evidence_integrity"
    assert d["status"] == "pass"
