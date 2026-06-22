"""P1.5.11A verified capability evidence invariant tests (P1.5.13 updated)."""
from __future__ import annotations

import pytest

from agentic_runtime.contracts.capability import (
    CapabilityEvidenceRecord,
    CapabilityEvidenceStatus,
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
    log = AurelTraceLog(trace_id="trace_capability_contract_test")
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
        limitations=("Verifier is limited to deterministic Golden Thread A stub output.",),
        evidence_refs=(evidence,),
        source_trace_event_ref=evidence.source_trace_event_ref,
        created_at=CREATED_AT,
    )


def _context_report(status: ContextAdequacyStatus = ContextAdequacyStatus.ADEQUATE):
    context = ContextBindingRef(
        context_id="context_001",
        context_type="test_context",
        source_refs=("source_ref_001",),
        assumptions=("deterministic test context",),
        created_at=CREATED_AT,
    )
    return ContextAdequacyReport(
        context_adequacy_id=f"context_adequacy_{status.value}_001",
        context_binding_ref=context,
        status=status,
        missing_context_flags=("missing detail",) if status == ContextAdequacyStatus.INSUFFICIENT else (),
        uncertainty_notes=("partial context",) if status == ContextAdequacyStatus.PARTIAL else (),
        safe_to_act=status != ContextAdequacyStatus.UNSAFE,
        requires_operator_clarification=status == ContextAdequacyStatus.INSUFFICIENT,
        created_at=CREATED_AT,
        adequacy_score=1.0 if status == ContextAdequacyStatus.ADEQUATE else 0.5,
    )


def _create_verified(verifier: VerifierResult, **overrides):
    context_report = overrides.pop("context_adequacy_report", _context_report())
    source_trace_event_ref = overrides.pop("source_trace_event_ref", verifier.source_trace_event_ref)
    source_event_hash = overrides.pop("source_event_hash", source_trace_event_ref.event_hash if source_trace_event_ref else None)
    evidence_refs = overrides.pop("evidence_refs", verifier.evidence_refs)
    limitations = overrides.pop("limitations", ("stub capability context limitation",))
    evidence_strength = overrides.pop("evidence_strength", EvidenceStrengthLevel.VERIFIED)
    return create_verified_capability_evidence_record(
        capability_evidence_id="capability_evidence_001",
        capability_id="capability.test",
        source_trace_event_ref=source_trace_event_ref,
        source_event_hash=source_event_hash,
        evidence_refs=evidence_refs,
        verifier_result=overrides.pop("verifier_result", verifier),
        context_binding_ref=context_report.context_binding_ref if context_report else None,
        context_adequacy_report=context_report,
        evidence_strength=evidence_strength,
        limitations=limitations,
        created_at=CREATED_AT,
    )


def test_verified_capability_requires_trace_event_ref():
    verifier = _verifier()
    with pytest.raises(ValueError, match="source_trace_event_ref"):
        _create_verified(verifier, source_trace_event_ref=None, source_event_hash=verifier.source_trace_event_ref.event_hash)


def test_verified_capability_requires_evidence_ref():
    verifier = _verifier()
    with pytest.raises(ValueError, match="EvidenceRef"):
        _create_verified(verifier, evidence_refs=())


def test_verified_capability_requires_verifier_result():
    evidence = _evidence_ref()
    with pytest.raises(ValueError, match="verifier_result_ref"):
        create_verified_capability_evidence_record(
            capability_evidence_id="capability_evidence_001",
            capability_id="capability.test",
            source_trace_event_ref=evidence.source_trace_event_ref,
            source_event_hash=evidence.source_trace_event_ref.event_hash,
            evidence_refs=(evidence,),
            verifier_result=None,
            context_binding_ref=_context_report().context_binding_ref,
            context_adequacy_report=_context_report(),
            evidence_strength=EvidenceStrengthLevel.VERIFIED,
            limitations=("stub capability limitation",),
            created_at=CREATED_AT,
        )


def test_verified_capability_requires_verifier_pass():
    verifier = _verifier(status=VerifierResultStatus.FAIL)
    with pytest.raises(ValueError, match="verifier status pass"):
        _create_verified(verifier)


def test_verified_capability_requires_limitations():
    verifier = _verifier()
    with pytest.raises(ValueError, match="limitations"):
        _create_verified(verifier, limitations=())


def test_failed_verifier_cannot_create_verified_capability():
    verifier = _verifier(status=VerifierResultStatus.FAIL)
    with pytest.raises(ValueError, match="verifier status pass"):
        _create_verified(verifier)


def test_unverified_capability_can_exist_without_verifier_but_not_as_verified():
    record = CapabilityEvidenceRecord(
        capability_evidence_id="capability_evidence_unverified_001",
        capability_id="capability.test",
        status=CapabilityEvidenceStatus.UNVERIFIED,
        source_trace_event_ref=None,
        source_event_hash=None,
        evidence_refs=(),
        verifier_result_ref=None,
        limitations=(),
        created_at=CREATED_AT,
    )
    assert record.status == CapabilityEvidenceStatus.UNVERIFIED

    verifier = _verifier()
    verified = _create_verified(verifier)
    assert verified.status == CapabilityEvidenceStatus.VERIFIED


def test_operator_feedback_stub_cannot_auto_promote_capability():
    operator_feedback = {"operator_feedback": "looks good"}
    assert operator_feedback["operator_feedback"] == "looks good"

    evidence = _evidence_ref()
    with pytest.raises(ValueError, match="factory"):
        CapabilityEvidenceRecord(
            capability_evidence_id="capability_evidence_bad_promotion_001",
            capability_id="capability.test",
            status=CapabilityEvidenceStatus.VERIFIED,
            source_trace_event_ref=evidence.source_trace_event_ref,
            source_event_hash=evidence.source_trace_event_ref.event_hash,
            evidence_refs=(evidence,),
            verifier_result_ref="operator_feedback_only",
            evidence_strength=EvidenceStrengthLevel.VERIFIED,
            limitations=("operator feedback is not a verifier result",),
            created_at=CREATED_AT,
        )
