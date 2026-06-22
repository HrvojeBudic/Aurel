"""P1.5.13 Verifier normalization layer.

Every verifier result used by capability evidence or evaluation cases
must pass through a normalizer. Raw verifier output must never feed
directly into CapabilityEvidenceRecord, EvaluationCase, or RegressionCandidate.

Stub verifiers demonstrate normalized output shapes without real LLMs,
operator UI, benchmark runners, or policy engines.
"""
from __future__ import annotations

import uuid

from agentic_runtime.contracts.context import ContextAdequacyReport, ContextAdequacyStatus
from agentic_runtime.contracts.evidence import EvidenceRef
from agentic_runtime.contracts.trace import TraceEventRef
from agentic_runtime.contracts.verifier import (
    NormalizationStatus,
    VerifierKind,
    VerifierNormalizationReport,
    VerifierResult,
    VerifierResultStatus,
)

_NORMALIZATION_TIMESTAMP = "2026-06-22T00:00:00+00:00"


def _new_normalization_id() -> str:
    return f"norm_{uuid.uuid4().hex[:12]}"


def _new_verifier_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


# ---------------------------------------------------------------------------
# DeterministicVerifierStub
# ---------------------------------------------------------------------------


def normalize_deterministic_result(
    *,
    condition_passed: bool,
    condition_description: str,
    source_trace_event_ref: TraceEventRef,
    evidence_refs: tuple[EvidenceRef, ...] = (),
    target_ref: str = "",
) -> tuple[VerifierNormalizationReport, VerifierResult]:
    """Normalize a deterministic condition check into a VerifierResult.

    condition_passed = True  → PASS
    condition_passed = False → FAIL
    """
    normalization_id = _new_normalization_id()
    verifier_id = _new_verifier_id("deterministic")

    if condition_passed:
        status = VerifierResultStatus.PASS
        confidence = 1.0
        reason = f"Deterministic condition passed: {condition_description}"
    else:
        status = VerifierResultStatus.FAIL
        confidence = 1.0
        reason = f"Deterministic condition failed: {condition_description}"

    limitations = (
        "Only verifies the explicit deterministic condition supplied to this verifier.",
    )

    result = VerifierResult(
        verifier_id=verifier_id,
        verifier_kind=VerifierKind.DETERMINISTIC,
        target_ref=target_ref or "deterministic_condition",
        status=status,
        confidence=confidence,
        reason=reason,
        limitations=limitations,
        evidence_refs=evidence_refs,
        source_trace_event_ref=source_trace_event_ref,
        normalized_from=None,
        created_at=_NORMALIZATION_TIMESTAMP,
    )

    report = VerifierNormalizationReport(
        normalization_id=normalization_id,
        verifier_kind=VerifierKind.DETERMINISTIC,
        raw_input_ref=None,
        normalized_verifier_result_ref=verifier_id,
        normalization_status=NormalizationStatus.NORMALIZED,
        reason="Deterministic condition normalized into VerifierResult.",
        warnings=(),
        errors=(),
        created_at=_NORMALIZATION_TIMESTAMP,
    )
    return report, result


# ---------------------------------------------------------------------------
# OperatorReviewVerifierStub
# ---------------------------------------------------------------------------


def normalize_operator_review(
    *,
    approved: bool,
    reviewer_id: str,
    review_notes: str,
    source_trace_event_ref: TraceEventRef,
    evidence_refs: tuple[EvidenceRef, ...] = (),
    target_ref: str = "",
) -> tuple[VerifierNormalizationReport, VerifierResult]:
    """Normalize an operator/human review into a VerifierResult.

    Operator approval is evidence, not automatic truth.
    Approved is NOT the same as task correctness.
    """
    normalization_id = _new_normalization_id()
    verifier_id = _new_verifier_id("operator_review")

    if approved:
        status = VerifierResultStatus.PASS
        confidence = 0.85
        reason = f"Operator {reviewer_id} approved: {review_notes}"
    else:
        status = VerifierResultStatus.FAIL
        confidence = 0.85
        reason = f"Operator {reviewer_id} rejected: {review_notes}"

    limitations = (
        "Operator review reflects human judgment for this case and does not generalize automatically.",
    )

    result = VerifierResult(
        verifier_id=verifier_id,
        verifier_kind=VerifierKind.OPERATOR_REVIEW,
        target_ref=target_ref or f"operator_review_{reviewer_id}",
        status=status,
        confidence=confidence,
        reason=reason,
        limitations=limitations,
        evidence_refs=evidence_refs,
        source_trace_event_ref=source_trace_event_ref,
        normalized_from=None,
        created_at=_NORMALIZATION_TIMESTAMP,
    )

    report = VerifierNormalizationReport(
        normalization_id=normalization_id,
        verifier_kind=VerifierKind.OPERATOR_REVIEW,
        raw_input_ref=None,
        normalized_verifier_result_ref=verifier_id,
        normalization_status=NormalizationStatus.NORMALIZED,
        reason="Operator review normalized into VerifierResult.",
        warnings=(),
        errors=(),
        created_at=_NORMALIZATION_TIMESTAMP,
    )
    return report, result


# ---------------------------------------------------------------------------
# PolicyCheckVerifierStub
# ---------------------------------------------------------------------------


def normalize_policy_check(
    *,
    policy_passed: bool,
    policy_name: str,
    policy_description: str,
    source_trace_event_ref: TraceEventRef,
    evidence_refs: tuple[EvidenceRef, ...] = (),
    target_ref: str = "",
) -> tuple[VerifierNormalizationReport, VerifierResult]:
    """Normalize a policy compliance check into a VerifierResult.

    Policy check verifies declared policy constraints only, not task correctness.
    A policy_pass must never claim task correctness.
    """
    normalization_id = _new_normalization_id()
    verifier_id = _new_verifier_id("policy_check")

    if policy_passed:
        status = VerifierResultStatus.PASS
        confidence = 1.0
        reason = f"Policy '{policy_name}' passed: {policy_description}"
    else:
        status = VerifierResultStatus.FAIL
        confidence = 1.0
        reason = f"Policy '{policy_name}' failed: {policy_description}"

    limitations = (
        "Policy check verifies declared policy constraints only, not task correctness.",
    )

    result = VerifierResult(
        verifier_id=verifier_id,
        verifier_kind=VerifierKind.POLICY_CHECK,
        target_ref=target_ref or f"policy_{policy_name}",
        status=status,
        confidence=confidence,
        reason=reason,
        limitations=limitations,
        evidence_refs=evidence_refs,
        source_trace_event_ref=source_trace_event_ref,
        normalized_from=None,
        created_at=_NORMALIZATION_TIMESTAMP,
    )

    report = VerifierNormalizationReport(
        normalization_id=normalization_id,
        verifier_kind=VerifierKind.POLICY_CHECK,
        raw_input_ref=None,
        normalized_verifier_result_ref=verifier_id,
        normalization_status=NormalizationStatus.NORMALIZED,
        reason="Policy check normalized into VerifierResult.",
        warnings=(),
        errors=(),
        created_at=_NORMALIZATION_TIMESTAMP,
    )
    return report, result


# ---------------------------------------------------------------------------
# LLMJudgeVerifierStub
# ---------------------------------------------------------------------------


def normalize_llm_judge_stub(
    *,
    condition_description: str,
    pass_condition: bool = True,
    source_trace_event_ref: TraceEventRef,
    evidence_refs: tuple[EvidenceRef, ...] = (),
    target_ref: str = "",
) -> tuple[VerifierNormalizationReport, VerifierResult]:
    """Normalize a stub LLM-as-judge result WITHOUT calling a real LLM.

    Must not call a real LLM.
    Must not require API keys.
    Must not make network calls.
    Must not claim production-grade judgment.
    """
    normalization_id = _new_normalization_id()
    verifier_id = _new_verifier_id("llm_judge_stub")

    if pass_condition:
        status = VerifierResultStatus.PASS
        confidence = 0.7
        reason = f"LLM judge stub condition passed: {condition_description}"
    else:
        status = VerifierResultStatus.FAIL
        confidence = 0.7
        reason = f"LLM judge stub condition failed: {condition_description}"

    limitations = (
        "LLM judge stub is not a real model judgment and must not be used as production verification.",
    )

    result = VerifierResult(
        verifier_id=verifier_id,
        verifier_kind=VerifierKind.LLM_JUDGE_STUB,
        target_ref=target_ref or "llm_judge_stub_condition",
        status=status,
        confidence=confidence,
        reason=reason,
        limitations=limitations,
        evidence_refs=evidence_refs,
        source_trace_event_ref=source_trace_event_ref,
        normalized_from=None,
        created_at=_NORMALIZATION_TIMESTAMP,
    )

    report = VerifierNormalizationReport(
        normalization_id=normalization_id,
        verifier_kind=VerifierKind.LLM_JUDGE_STUB,
        raw_input_ref=None,
        normalized_verifier_result_ref=verifier_id,
        normalization_status=NormalizationStatus.NORMALIZED,
        reason="LLM judge stub normalized into VerifierResult without calling real LLM.",
        warnings=(),
        errors=(),
        created_at=_NORMALIZATION_TIMESTAMP,
    )
    return report, result


# ---------------------------------------------------------------------------
# ContextAdequacyVerifierStub
# ---------------------------------------------------------------------------


_CONTEXT_ADEQUACY_STATUS_MAP: dict[ContextAdequacyStatus, VerifierResultStatus] = {
    ContextAdequacyStatus.ADEQUATE: VerifierResultStatus.PASS,
    ContextAdequacyStatus.PARTIAL: VerifierResultStatus.NEEDS_REVIEW,
    ContextAdequacyStatus.INSUFFICIENT: VerifierResultStatus.FAIL,
    ContextAdequacyStatus.UNSAFE: VerifierResultStatus.FAIL,
}


def normalize_context_adequacy(
    *,
    context_adequacy_report: ContextAdequacyReport,
    source_trace_event_ref: TraceEventRef,
    evidence_refs: tuple[EvidenceRef, ...] = (),
) -> tuple[VerifierNormalizationReport, VerifierResult]:
    """Normalize a ContextAdequacyReport into a VerifierResult.

    adequate     → PASS
    partial      → NEEDS_REVIEW
    insufficient → FAIL
    unsafe       → FAIL
    """
    normalization_id = _new_normalization_id()
    verifier_id = _new_verifier_id("context_adequacy")

    status = _CONTEXT_ADEQUACY_STATUS_MAP[context_adequacy_report.status]
    confidence = context_adequacy_report.adequacy_score or 0.5

    reason = f"Context adequacy status: {context_adequacy_report.status.value}"

    if context_adequacy_report.uncertainty_notes:
        reason += f" (notes: {'; '.join(context_adequacy_report.uncertainty_notes)})"

    limitations = (
        "Context adequacy verifier only checks explicit context adequacy flags, "
        "not open-domain semantic completeness.",
    )

    result = VerifierResult(
        verifier_id=verifier_id,
        verifier_kind=VerifierKind.CONTEXT_ADEQUACY,
        target_ref=context_adequacy_report.context_adequacy_id,
        status=status,
        confidence=confidence,
        reason=reason,
        limitations=limitations,
        evidence_refs=evidence_refs,
        source_trace_event_ref=source_trace_event_ref,
        normalized_from=None,
        created_at=_NORMALIZATION_TIMESTAMP,
    )

    report = VerifierNormalizationReport(
        normalization_id=normalization_id,
        verifier_kind=VerifierKind.CONTEXT_ADEQUACY,
        raw_input_ref=context_adequacy_report.context_adequacy_id,
        normalized_verifier_result_ref=verifier_id,
        normalization_status=NormalizationStatus.NORMALIZED,
        reason="Context adequacy report normalized into VerifierResult.",
        warnings=(),
        errors=(),
        created_at=_NORMALIZATION_TIMESTAMP,
    )
    return report, result


# ---------------------------------------------------------------------------
# EvidenceIntegrityVerifierStub
# ---------------------------------------------------------------------------


def normalize_evidence_integrity(
    *,
    evidence_ref: EvidenceRef,
    source_trace_event_ref: TraceEventRef,
    expected_source_event_hash: str | None = None,
    target_ref: str = "",
) -> tuple[VerifierNormalizationReport, VerifierResult]:
    """Normalize a structural evidence integrity check into a VerifierResult.

    Checks:
    - EvidenceRef exists
    - EvidenceRef has source TraceEventRef
    - content_hash exists
    - source_event_hash matches when available
    """
    normalization_id = _new_normalization_id()
    verifier_id = _new_verifier_id("evidence_integrity")

    checks_passed: list[str] = []
    checks_failed: list[str] = []

    # EvidenceRef exists
    if evidence_ref.evidence_id:
        checks_passed.append("evidence_ref_exists")
    else:
        checks_failed.append("evidence_ref_missing_id")

    # Has source TraceEventRef
    if evidence_ref.source_trace_event_ref is not None:
        checks_passed.append("evidence_ref_has_trace_ref")
    else:
        checks_failed.append("evidence_ref_missing_trace_ref")

    # content_hash exists
    if evidence_ref.content_hash:
        checks_passed.append("content_hash_exists")
    else:
        checks_failed.append("content_hash_missing")

    # source_event_hash matches
    if expected_source_event_hash is not None and evidence_ref.source_trace_event_ref is not None:
        if expected_source_event_hash == evidence_ref.source_trace_event_ref.event_hash:
            checks_passed.append("source_event_hash_matches")
        else:
            checks_failed.append("source_event_hash_mismatch")

    if checks_failed:
        status = VerifierResultStatus.FAIL
        confidence = 1.0
        reason = f"Evidence integrity failed: {'; '.join(checks_failed)}"
    else:
        status = VerifierResultStatus.PASS
        confidence = 1.0
        reason = f"Evidence integrity passed: {'; '.join(checks_passed)}"

    limitations = (
        "Evidence integrity verifier checks structural evidence integrity, "
        "not truth of the underlying claim.",
    )

    result = VerifierResult(
        verifier_id=verifier_id,
        verifier_kind=VerifierKind.EVIDENCE_INTEGRITY,
        target_ref=target_ref or evidence_ref.evidence_id,
        status=status,
        confidence=confidence,
        reason=reason,
        limitations=limitations,
        evidence_refs=(evidence_ref,),
        source_trace_event_ref=source_trace_event_ref,
        normalized_from=None,
        created_at=_NORMALIZATION_TIMESTAMP,
    )

    report = VerifierNormalizationReport(
        normalization_id=normalization_id,
        verifier_kind=VerifierKind.EVIDENCE_INTEGRITY,
        raw_input_ref=evidence_ref.evidence_id,
        normalized_verifier_result_ref=verifier_id,
        normalization_status=NormalizationStatus.NORMALIZED,
        reason="Evidence integrity check normalized into VerifierResult.",
        warnings=(),
        errors=(),
        created_at=_NORMALIZATION_TIMESTAMP,
    )
    return report, result
