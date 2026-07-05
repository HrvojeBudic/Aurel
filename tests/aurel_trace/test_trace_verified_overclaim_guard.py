"""P5.11 — Overclaim guard: prove what is NOT enough for TRACE_VERIFIED."""

from __future__ import annotations

from agentic_runtime.aurel_trace import (
    EvidenceKind,
    TraceBindingCoverageStatus,
    TraceHashVerificationRequest,
    TraceVerificationScope,
    make_evidence_ref,
    resolve_trace_target,
    verify_canonical_trace_hash_chain,
)
from agentic_runtime.aurel_trace.trace_receipts import build_trace_verification_receipt
from agentic_runtime.aurel_trace.trace_resolver import (
    TraceVerificationStatus,
    TraceVerificationTargetKind,
)
from agentic_runtime.aurel_trace.trace_schema import (
    TraceSchemaCompatibility,
    TraceSchemaCompatibilityDecision,
)


def _pass_result_and_receipt(demo_run_ref, demo_envelopes):
    request = TraceHashVerificationRequest(
        verification_request_id="vr-oc",
        trace_run_ref=demo_run_ref,
        scope=TraceVerificationScope.FULL_CHAIN,
    )
    result = verify_canonical_trace_hash_chain(request, demo_envelopes)
    return result, build_trace_verification_receipt(result, request)


def test_hash_pass_alone_is_not_trace_verified(demo_run_ref, demo_envelopes):
    result, _receipt = _pass_result_and_receipt(demo_run_ref, demo_envelopes)
    decision = resolve_trace_target(
        target_kind=TraceVerificationTargetKind.TRACE_RUN,
        target_id=demo_run_ref.trace_run_id,
        hash_result=result,  # no receipt
    )
    assert decision.status is not TraceVerificationStatus.TRACE_VERIFIED
    assert decision.status is TraceVerificationStatus.TRACE_BOUND


def test_receipt_alone_is_not_trace_verified(demo_run_ref, demo_envelopes):
    _result, receipt = _pass_result_and_receipt(demo_run_ref, demo_envelopes)
    decision = resolve_trace_target(
        target_kind=TraceVerificationTargetKind.TRACE_RUN,
        target_id=demo_run_ref.trace_run_id,
        receipt=receipt,  # no evidence, no binding
    )
    assert decision.status is not TraceVerificationStatus.TRACE_VERIFIED
    assert decision.status is TraceVerificationStatus.TRACE_BOUND


def test_evidence_ref_present_alone_is_not_trace_verified():
    # PRESENT evidence but no integrity proof (no receipt/hash result).
    ref = make_evidence_ref(
        evidence_kind=EvidenceKind.SANDBOX_EVIDENCE,
        source_domain="runtime.submit",
        source_object_id="s-1",
    )
    decision = resolve_trace_target(
        target_kind=TraceVerificationTargetKind.EVIDENCE_SET,
        target_id="es-1",
        evidence_refs=(ref,),
        required_evidence_kinds=[EvidenceKind.SANDBOX_EVIDENCE.value],
    )
    assert decision.status is not TraceVerificationStatus.TRACE_VERIFIED
    assert decision.status is TraceVerificationStatus.UNAVAILABLE


def test_binding_complete_alone_is_not_trace_verified():
    # COMPLETE coverage but no integrity proof.
    decision = resolve_trace_target(
        target_kind=TraceVerificationTargetKind.RUNTIME_SUBMIT_BINDING,
        target_id="rsbind-x",
        binding_coverage=TraceBindingCoverageStatus.COMPLETE,
    )
    assert decision.status is not TraceVerificationStatus.TRACE_VERIFIED
    assert decision.status is TraceVerificationStatus.UNAVAILABLE


def test_unknown_schema_is_not_trace_verified(demo_run_ref, demo_envelopes):
    _result, receipt = _pass_result_and_receipt(demo_run_ref, demo_envelopes)
    unknown_schema = TraceSchemaCompatibilityDecision(
        decision_id="dec-unknown",
        record_type="MadeUp",
        schema_version=None,
        decision=TraceSchemaCompatibility.UNKNOWN,
        reason="not in registry",
    )
    decision = resolve_trace_target(
        target_kind=TraceVerificationTargetKind.TRACE_RUN,
        target_id=demo_run_ref.trace_run_id,
        receipt=receipt,
        schema_decision=unknown_schema,
    )
    assert decision.status is not TraceVerificationStatus.TRACE_VERIFIED
    assert decision.status is TraceVerificationStatus.DENIED
