"""P1.5.12 Evaluation case extraction logic.

Extracts candidate evaluation/regression records from trace-bound capability evidence.
Nothing is auto-accepted; nothing is promoted to memory, skill, reflex, or capability.
"""
from __future__ import annotations

import uuid

from agentic_runtime.contracts.capability import (
    CapabilityEvidenceRecord,
    CapabilityEvidenceStatus,
    EvidenceStrengthLevel,
)
from agentic_runtime.contracts.context import (
    ContextAdequacyReport,
    ContextAdequacyStatus,
)
from agentic_runtime.contracts.evaluation_cases import (
    EvaluationCase,
    EvaluationCaseExtractionReport,
    EvaluationCaseKind,
    EvaluationCaseStatus,
    ExtractionStatus,
    FailureMode,
    RegressionCandidate,
    RegressionPriority,
)
from agentic_runtime.contracts.evidence import EvidenceRef
from agentic_runtime.contracts.trace import TraceEventRef
from agentic_runtime.contracts.verifier import (
    VerifierResult,
    VerifierResultStatus,
)

_EXTRACTION_TIMESTAMP = "2026-06-22T00:00:00+00:00"


def _new_extraction_id() -> str:
    return f"extraction_{uuid.uuid4().hex[:12]}"


def _new_case_id() -> str:
    return f"eval_case_{uuid.uuid4().hex[:12]}"


def _new_regression_id() -> str:
    return f"regression_{uuid.uuid4().hex[:12]}"


def _map_failure_mode(
    *,
    capability: CapabilityEvidenceRecord,
    verifier: VerifierResult,
    context_adequacy: ContextAdequacyReport | None,
) -> FailureMode:
    """Map status signals to a deterministic FailureMode.

    Priority order: verifier fail > context unsafe/insufficient > missing evidence
    > weak evidence > hash mismatch > failed capability > missing limitations.
    """
    if verifier.status == VerifierResultStatus.FAIL:
        return FailureMode.VERIFIER_FAILED

    if context_adequacy is not None:
        if context_adequacy.status == ContextAdequacyStatus.UNSAFE:
            return FailureMode.UNSAFE_CONTEXT
        if context_adequacy.status == ContextAdequacyStatus.INSUFFICIENT:
            return FailureMode.INSUFFICIENT_CONTEXT

    if not capability.evidence_refs:
        return FailureMode.MISSING_EVIDENCE

    if capability.evidence_strength in (EvidenceStrengthLevel.NONE, EvidenceStrengthLevel.WEAK):
        return FailureMode.WEAK_EVIDENCE

    if (
        capability.source_trace_event_ref is not None
        and capability.source_event_hash is not None
        and capability.source_event_hash != capability.source_trace_event_ref.event_hash
    ):
        return FailureMode.HASH_MISMATCH

    if capability.status == CapabilityEvidenceStatus.FAILED:
        return FailureMode.VERIFIER_FAILED

    if not capability.limitations:
        return FailureMode.MISSING_LIMITATIONS

    return FailureMode.UNKNOWN


def _evidence_ref_ids(evidence_refs: tuple[EvidenceRef, ...]) -> tuple[str, ...]:
    return tuple(ref.evidence_id for ref in evidence_refs)


def _resolve_safe_trace_ref(
    *,
    capability: CapabilityEvidenceRecord,
    verifier: VerifierResult,
    trace_event_ref: TraceEventRef | None,
) -> TraceEventRef:
    """Resolve a TraceEventRef that is guaranteed to be valid for record construction."""
    return capability.source_trace_event_ref or trace_event_ref or verifier.source_trace_event_ref


def _resolve_safe_event_hash(
    *,
    capability: CapabilityEvidenceRecord,
    safe_trace_ref: TraceEventRef,
) -> str:
    """Resolve a source_event_hash that matches the safe_trace_ref."""
    if capability.source_event_hash and capability.source_trace_event_ref is not None:
        if capability.source_event_hash == capability.source_trace_event_ref.event_hash:
            return capability.source_event_hash
    return safe_trace_ref.event_hash


def _is_review(
    capability: CapabilityEvidenceRecord,
    verifier: VerifierResult,
    context_adequacy: ContextAdequacyReport | None,
) -> bool:
    return (
        verifier.status == VerifierResultStatus.NEEDS_REVIEW
        or capability.status == CapabilityEvidenceStatus.INCONCLUSIVE
        or (
            context_adequacy is not None
            and context_adequacy.status == ContextAdequacyStatus.PARTIAL
        )
    )


def _is_regression(
    capability: CapabilityEvidenceRecord,
    verifier: VerifierResult,
    context_adequacy: ContextAdequacyReport | None,
    source_ref: TraceEventRef | None,
    source_hash: str | None,
) -> bool:
    return (
        capability.status == CapabilityEvidenceStatus.FAILED
        or verifier.status == VerifierResultStatus.FAIL
        or (
            context_adequacy is not None
            and context_adequacy.status
            in (ContextAdequacyStatus.INSUFFICIENT, ContextAdequacyStatus.UNSAFE)
        )
        or capability.evidence_strength in (EvidenceStrengthLevel.NONE, EvidenceStrengthLevel.WEAK)
        or (source_hash is not None
            and source_ref is not None
            and source_hash != source_ref.event_hash)
        or len(capability.evidence_refs) == 0
        or len(capability.limitations) == 0
    )


def _is_positive(
    capability: CapabilityEvidenceRecord,
    verifier: VerifierResult,
    source_ref: TraceEventRef | None,
    source_hash: str | None,
) -> bool:
    return (
        capability.status == CapabilityEvidenceStatus.VERIFIED
        and verifier.status == VerifierResultStatus.PASS
        and source_ref is not None
        and source_hash is not None
        and source_hash == source_ref.event_hash
        and len(capability.evidence_refs) > 0
        and len(capability.limitations) > 0
    )


def _build_review_case(
    extraction_id: str,
    capability: CapabilityEvidenceRecord,
    verifier: VerifierResult,
    context_adequacy: ContextAdequacyReport | None,
    trace_event_ref: TraceEventRef | None,
) -> tuple[EvaluationCaseExtractionReport, EvaluationCase]:
    safe_ref = _resolve_safe_trace_ref(
        capability=capability, verifier=verifier, trace_event_ref=trace_event_ref,
    )
    safe_hash = _resolve_safe_event_hash(capability=capability, safe_trace_ref=safe_ref)
    case_id = _new_case_id()
    evidence_ids = _evidence_ref_ids(capability.evidence_refs)
    case = EvaluationCase(
        case_id=case_id,
        case_kind=EvaluationCaseKind.REVIEW,
        source_capability_evidence_id=capability.capability_evidence_id,
        source_trace_event_ref=safe_ref,
        source_event_hash=safe_hash,
        evidence_refs=evidence_ids,
        verifier_result_ref=verifier.verifier_id,
        context_adequacy_ref=(
            context_adequacy.context_adequacy_id if context_adequacy else None
        ),
        input_snapshot_ref=None,
        expected_behavior=None,
        success_criteria=(),
        known_limitations=capability.limitations,
        failure_mode=None,
        regression_priority=None,
        created_at=_EXTRACTION_TIMESTAMP,
        status=EvaluationCaseStatus.NEEDS_REVIEW,
    )
    return (
        EvaluationCaseExtractionReport(
            extraction_id=extraction_id,
            source_capability_evidence_id=capability.capability_evidence_id,
            extracted_case_id=case_id,
            extracted_regression_id=None,
            extraction_status=ExtractionStatus.NEEDS_REVIEW,
            reason="review evaluation case extracted from needs-review/inconclusive/partial outcomes",
            warnings=(),
            errors=(),
            created_at=_EXTRACTION_TIMESTAMP,
        ),
        case,
    )


def _build_positive_case(
    extraction_id: str,
    capability: CapabilityEvidenceRecord,
    verifier: VerifierResult,
    context_adequacy: ContextAdequacyReport | None,
    source_ref: TraceEventRef,
    source_hash: str,
) -> tuple[EvaluationCaseExtractionReport, EvaluationCase]:
    case_id = _new_case_id()
    evidence_ids = _evidence_ref_ids(capability.evidence_refs)
    case = EvaluationCase(
        case_id=case_id,
        case_kind=EvaluationCaseKind.POSITIVE,
        source_capability_evidence_id=capability.capability_evidence_id,
        source_trace_event_ref=source_ref,
        source_event_hash=source_hash,
        evidence_refs=evidence_ids,
        verifier_result_ref=verifier.verifier_id,
        context_adequacy_ref=(
            context_adequacy.context_adequacy_id if context_adequacy else None
        ),
        input_snapshot_ref=None,
        expected_behavior=None,
        success_criteria=(),
        known_limitations=capability.limitations,
        failure_mode=None,
        regression_priority=None,
        created_at=_EXTRACTION_TIMESTAMP,
        status=EvaluationCaseStatus.CANDIDATE,
    )
    return (
        EvaluationCaseExtractionReport(
            extraction_id=extraction_id,
            source_capability_evidence_id=capability.capability_evidence_id,
            extracted_case_id=case_id,
            extracted_regression_id=None,
            extraction_status=ExtractionStatus.EXTRACTED,
            reason="positive evaluation case extracted from verified capability evidence",
            warnings=(),
            errors=(),
            created_at=_EXTRACTION_TIMESTAMP,
        ),
        case,
    )


def _build_regression_candidate(
    extraction_id: str,
    capability: CapabilityEvidenceRecord,
    verifier: VerifierResult,
    context_adequacy: ContextAdequacyReport | None,
    trace_event_ref: TraceEventRef | None,
) -> tuple[EvaluationCaseExtractionReport, None]:
    failure_mode = _map_failure_mode(
        capability=capability, verifier=verifier, context_adequacy=context_adequacy,
    )
    regression_id = _new_regression_id()
    safe_ref = _resolve_safe_trace_ref(
        capability=capability, verifier=verifier, trace_event_ref=trace_event_ref,
    )
    safe_hash = _resolve_safe_event_hash(capability=capability, safe_trace_ref=safe_ref)
    evidence_ids = _evidence_ref_ids(capability.evidence_refs)

    _priority = RegressionPriority.MEDIUM
    if failure_mode in (FailureMode.VERIFIER_FAILED, FailureMode.UNSAFE_CONTEXT):
        _priority = RegressionPriority.HIGH
    elif failure_mode == FailureMode.WEAK_EVIDENCE:
        _priority = RegressionPriority.LOW

    # Construct to validate, then extract id for report
    RegressionCandidate(
        regression_id=regression_id,
        source_case_id=None,
        source_capability_evidence_id=capability.capability_evidence_id,
        source_trace_event_ref=safe_ref,
        source_event_hash=safe_hash,
        failure_mode=failure_mode,
        reproduction_hint=None,
        priority=_priority,
        evidence_refs=evidence_ids,
        verifier_result_ref=verifier.verifier_id,
        context_adequacy_ref=(
            context_adequacy.context_adequacy_id if context_adequacy else None
        ),
        created_at=_EXTRACTION_TIMESTAMP,
        status=EvaluationCaseStatus.CANDIDATE,
    )

    return (
        EvaluationCaseExtractionReport(
            extraction_id=extraction_id,
            source_capability_evidence_id=capability.capability_evidence_id,
            extracted_case_id=None,
            extracted_regression_id=regression_id,
            extraction_status=ExtractionStatus.EXTRACTED,
            reason=f"regression candidate extracted: {failure_mode.value}",
            warnings=(),
            errors=(),
            created_at=_EXTRACTION_TIMESTAMP,
        ),
        None,
    )


def extract_evaluation_case_from_capability_evidence(
    *,
    capability: CapabilityEvidenceRecord,
    verifier: VerifierResult,
    context_adequacy: ContextAdequacyReport | None = None,
    trace_event_ref: TraceEventRef | None = None,
) -> tuple[EvaluationCaseExtractionReport, EvaluationCase | None]:
    """Extract an EvaluationCase from trace-bound capability evidence.

    Returns (report, case) where case may be None if extraction was skipped or failed.
    The extracted case is always candidate or needs_review — never accepted.

    Routing priority: review > regression > positive.
    """
    extraction_id = _new_extraction_id()
    source_ref = capability.source_trace_event_ref or trace_event_ref
    source_hash = capability.source_event_hash

    # --- Review case (highest priority) ---
    if _is_review(capability, verifier, context_adequacy):
        return _build_review_case(
            extraction_id=extraction_id,
            capability=capability,
            verifier=verifier,
            context_adequacy=context_adequacy,
            trace_event_ref=trace_event_ref,
        )

    # --- Regression candidate (checked before positive) ---
    if _is_regression(capability, verifier, context_adequacy, source_ref, source_hash):
        return _build_regression_candidate(
            extraction_id=extraction_id,
            capability=capability,
            verifier=verifier,
            context_adequacy=context_adequacy,
            trace_event_ref=trace_event_ref,
        )

    # --- Positive case ---
    if _is_positive(capability, verifier, source_ref, source_hash):
        return _build_positive_case(
            extraction_id=extraction_id,
            capability=capability,
            verifier=verifier,
            context_adequacy=context_adequacy,
            source_ref=source_ref,
            source_hash=source_hash,
        )

    # --- No extraction match ---
    return (
        EvaluationCaseExtractionReport(
            extraction_id=extraction_id,
            source_capability_evidence_id=capability.capability_evidence_id,
            extracted_case_id=None,
            extracted_regression_id=None,
            extraction_status=ExtractionStatus.SKIPPED,
            reason="capability evidence does not meet extraction criteria",
            warnings=(),
            errors=(),
            created_at=_EXTRACTION_TIMESTAMP,
        ),
        None,
    )
