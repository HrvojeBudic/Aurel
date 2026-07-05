"""P5.11 — TRACE_VERIFIED resolver core."""

from __future__ import annotations

import dataclasses

import pytest

from agentic_runtime.aurel_trace import (
    AurelTraceError,
    EvidenceKind,
    TraceHashVerificationRequest,
    TraceVerificationDecision,
    TraceVerificationScope,
    TraceVerifiedResolver,
    make_evidence_ref,
    resolve_trace_target,
    verify_canonical_trace_hash_chain,
)
from agentic_runtime.aurel_trace.evidence_ref import EvidenceStatus
from agentic_runtime.aurel_trace.trace_receipts import build_trace_verification_receipt
from agentic_runtime.aurel_trace.trace_resolver import (
    TraceVerificationStatus,
    TraceVerificationTargetKind,
)
from agentic_runtime.aurel_trace.trace_verify import (
    TraceFindingSeverity,
    TraceHashFinding,
    TraceHashFindingKind,
)


def _pass_receipt(demo_run_ref, demo_envelopes):
    request = TraceHashVerificationRequest(
        verification_request_id="vr-res",
        trace_run_ref=demo_run_ref,
        scope=TraceVerificationScope.FULL_CHAIN,
    )
    result = verify_canonical_trace_hash_chain(request, demo_envelopes)
    return result, build_trace_verification_receipt(result, request)


def _present_evidence(kinds, receipt_id):
    return tuple(
        make_evidence_ref(
            evidence_kind=k,
            source_domain="runtime.submit",
            source_object_id=f"{k.value}-1",
            verification_receipt_id=receipt_id,
        )
        for k in kinds
    )


def test_valid_full_input_is_trace_verified(demo_run_ref, demo_envelopes):
    result, receipt = _pass_receipt(demo_run_ref, demo_envelopes)
    kinds = (EvidenceKind.SANDBOX_EVIDENCE, EvidenceKind.VERIFIER_EVIDENCE)
    decision = resolve_trace_target(
        target_kind=TraceVerificationTargetKind.CHAIN_HEAD,
        target_id=demo_run_ref.trace_run_id,
        receipt=receipt,
        hash_result=result,
        evidence_refs=_present_evidence(kinds, receipt.receipt_id),
        required_evidence_kinds=[k.value for k in kinds],
    )
    assert decision.status is TraceVerificationStatus.TRACE_VERIFIED
    assert decision.verified is True
    assert decision.missing_evidence == ()


def test_decision_id_is_deterministic(demo_run_ref, demo_envelopes):
    result, receipt = _pass_receipt(demo_run_ref, demo_envelopes)
    kinds = (EvidenceKind.SANDBOX_EVIDENCE,)
    kwargs = dict(
        target_kind=TraceVerificationTargetKind.CHAIN_HEAD,
        target_id=demo_run_ref.trace_run_id,
        receipt=receipt,
        evidence_refs=_present_evidence(kinds, receipt.receipt_id),
        required_evidence_kinds=[k.value for k in kinds],
    )
    a = resolve_trace_target(**kwargs)
    b = resolve_trace_target(**kwargs)
    assert a.decision_id == b.decision_id
    assert a.status is TraceVerificationStatus.TRACE_VERIFIED


def test_unknown_target_kind_fails_closed():
    decision = resolve_trace_target(
        target_kind="NOT_A_KIND",  # type: ignore[arg-type]
        target_id="x",
    )
    assert decision.status is TraceVerificationStatus.ERROR
    assert decision.verified is False


def test_missing_evidence_yields_partial(demo_run_ref, demo_envelopes):
    _result, receipt = _pass_receipt(demo_run_ref, demo_envelopes)
    decision = resolve_trace_target(
        target_kind=TraceVerificationTargetKind.EVIDENCE_SET,
        target_id="es-1",
        receipt=receipt,
        evidence_refs=_present_evidence((EvidenceKind.SANDBOX_EVIDENCE,), receipt.receipt_id),
        required_evidence_kinds=[
            EvidenceKind.SANDBOX_EVIDENCE.value,
            EvidenceKind.MEMORY_EVIDENCE.value,
        ],
    )
    assert decision.status is TraceVerificationStatus.PARTIAL
    assert EvidenceKind.MEMORY_EVIDENCE.value in decision.missing_evidence


def test_blocking_finding_denies(demo_run_ref, demo_envelopes):
    _result, receipt = _pass_receipt(demo_run_ref, demo_envelopes)
    finding = TraceHashFinding(
        finding_id="f1",
        finding_kind=TraceHashFindingKind.BROKEN_PREVIOUS_HASH,
        severity=TraceFindingSeverity.CRITICAL,
        message="prev hash broken",
    )
    decision = resolve_trace_target(
        target_kind=TraceVerificationTargetKind.TRACE_RUN,
        target_id=demo_run_ref.trace_run_id,
        receipt=receipt,
        findings=[finding],
    )
    assert decision.status is TraceVerificationStatus.DENIED
    assert decision.blocking_findings


def test_no_integrity_input_is_unavailable():
    decision = resolve_trace_target(
        target_kind=TraceVerificationTargetKind.TRACE_RUN,
        target_id="run-x",
    )
    assert decision.status is TraceVerificationStatus.UNAVAILABLE


def test_evidence_error_yields_error():
    err_ref = make_evidence_ref(
        evidence_kind=EvidenceKind.COMMAND_EVIDENCE,
        source_domain="runtime.submit",
        source_object_id="c-1",
    )
    err_ref = dataclasses.replace(err_ref, status=EvidenceStatus.ERROR, missing_reason="boom")
    decision = resolve_trace_target(
        target_kind=TraceVerificationTargetKind.EVIDENCE_SET,
        target_id="es-err",
        evidence_refs=(err_ref,),
    )
    assert decision.status is TraceVerificationStatus.ERROR


def test_verified_flag_must_match_status():
    with pytest.raises(AurelTraceError):
        TraceVerificationDecision(
            decision_id="d",
            target_kind=TraceVerificationTargetKind.TRACE_RUN,
            target_id="t",
            status=TraceVerificationStatus.TRACE_BOUND,
            verified=True,
            reason="mismatch",
        )


def test_failing_receipt_denies(demo_run_ref, demo_envelopes):
    tampered = dataclasses.replace(demo_envelopes[1], payload_hash="dead" * 16)
    envelopes = (demo_envelopes[0], tampered) + demo_envelopes[2:]
    request = TraceHashVerificationRequest(
        verification_request_id="vr-fail",
        trace_run_ref=demo_run_ref,
        scope=TraceVerificationScope.FULL_CHAIN,
    )
    fail_result = verify_canonical_trace_hash_chain(request, envelopes)
    fail_receipt = build_trace_verification_receipt(fail_result, request)
    decision = resolve_trace_target(
        target_kind=TraceVerificationTargetKind.TRACE_RUN,
        target_id=demo_run_ref.trace_run_id,
        receipt=fail_receipt,
    )
    assert decision.status is TraceVerificationStatus.DENIED
    assert decision.verified is False


def test_resolver_object_is_pure():
    resolver = TraceVerifiedResolver()
    assert resolver.mutates is False
    assert resolver.appends_trace is False
    assert resolver.executes is False
    with pytest.raises(AurelTraceError):
        TraceVerifiedResolver(mutates=True)
