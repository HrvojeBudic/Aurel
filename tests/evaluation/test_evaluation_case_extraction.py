"""P1.5.12 Evaluation case extraction tests.

Covers positive, regression, review extraction, candidate-only guards,
and impossible-state validation.
"""
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
from agentic_runtime.contracts.evaluation_cases import (
    EvaluationCase,
    EvaluationCaseKind,
    EvaluationCaseStatus,
    ExtractionStatus,
    FailureMode,
    RegressionCandidate,
    RegressionPriority,
    evaluation_case_to_dict,
    extraction_report_to_dict,
    regression_candidate_to_dict,
)
from agentic_runtime.contracts.evidence import EvidenceRef
from agentic_runtime.contracts.trace import (
    AurelTraceLog,
    TraceEventRef,
    TraceEventStatus,
    TraceEventType,
    hash_json,
    trace_event_ref,
)
from agentic_runtime.contracts.verifier import (
    VerifierKind,
    VerifierResult,
    VerifierResultStatus,
)
from agentic_runtime.evaluation.extraction import (
    _map_failure_mode,
    extract_evaluation_case_from_capability_evidence,
)

_TIMESTAMP = "2026-06-22T00:00:00+00:00"


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


def _make_trace_ref() -> tuple[AurelTraceLog, TraceEventRef]:
    log = AurelTraceLog(trace_id="trace_test_001")
    event = log.append(
        event_type=TraceEventType.STUB_EXECUTION_COMPLETED,
        actor_type="test",
        actor_id="test_extraction",
        payload_json={"test": True},
        timestamp=_TIMESTAMP,
        status=TraceEventStatus.COMPLETED,
    )
    return log, trace_event_ref(event)


def _evidence_ref(source: TraceEventRef | None = None) -> EvidenceRef:
    ref = source or _make_trace_ref()[1]
    return EvidenceRef(
        evidence_id="ev_test_001",
        source_trace_event_ref=ref,
        evidence_type="test_evidence",
        content_hash=hash_json({"test": "content"}),
        summary="Test evidence for extraction.",
        is_canonical=False,
    )


def _context_binding_ref() -> ContextBindingRef:
    return ContextBindingRef(
        context_id="ctx_test_001",
        context_type="test_context",
        source_refs=(),
        assumptions=(),
        created_at=_TIMESTAMP,
    )


def _context_adequacy(
    status: ContextAdequacyStatus = ContextAdequacyStatus.ADEQUATE,
) -> ContextAdequacyReport:
    return ContextAdequacyReport(
        context_adequacy_id="cad_test_001",
        context_binding_ref=_context_binding_ref(),
        status=status,
        missing_context_flags=(),
        stale_context_flags=(),
        contradicted_context_flags=(),
        uncertainty_notes=(),
        safe_to_act=(status != ContextAdequacyStatus.UNSAFE),
        requires_operator_clarification=(
            status == ContextAdequacyStatus.INSUFFICIENT
        ),
        created_at=_TIMESTAMP,
        adequacy_score=1.0 if status == ContextAdequacyStatus.ADEQUATE else 0.5,
    )


def _verifier(
    status: VerifierResultStatus = VerifierResultStatus.PASS,
    evidence_refs: tuple[EvidenceRef, ...] | None = None,
) -> VerifierResult:
    ref = _make_trace_ref()[1]
    if evidence_refs is None:
        evidence_refs = (_evidence_ref(ref),)
    return VerifierResult(
        verifier_id="ver_test_001",
        verifier_kind=VerifierKind.DETERMINISTIC,
        target_ref="target_test_001",
        status=status,
        confidence=1.0 if status == VerifierResultStatus.PASS else 0.5,
        reason="Test verifier result.",
        limitations=("Test verifier limitation.",),
        evidence_refs=evidence_refs,
        source_trace_event_ref=ref,
        created_at=_TIMESTAMP,
    )


def _make_verified_capability(
    evidence_refs: tuple[EvidenceRef, ...] | None = None,
    source_trace_event_ref: TraceEventRef | None = None,
    source_event_hash: str | None = None,
    strength: EvidenceStrengthLevel = EvidenceStrengthLevel.VERIFIED,
    limitations: tuple[str, ...] | None = None,
) -> CapabilityEvidenceRecord:
    """Create a verified capability using the factory.

    Requires valid context adequacy, so this only works for ADEQUATE context tests.
    """
    ref = source_trace_event_ref or _make_trace_ref()[1]
    if evidence_refs is None:
        evidence_refs = (_evidence_ref(ref),)
    if limitations is None:
        limitations = ("Test capability limitation.",)
    if source_event_hash is None:
        source_event_hash = ref.event_hash

    ctx = _context_binding_ref()
    context_adequacy = _context_adequacy()
    verifier = _verifier(evidence_refs=evidence_refs)

    return create_verified_capability_evidence_record(
        capability_evidence_id="cap_ev_test_001",
        capability_id="cap.test.extraction",
        source_trace_event_ref=ref,
        source_event_hash=source_event_hash,
        evidence_refs=evidence_refs,
        verifier_result=verifier,
        context_binding_ref=ctx,
        context_adequacy_report=context_adequacy,
        evidence_strength=strength,
        limitations=limitations,
        created_at=_TIMESTAMP,
    )


def _make_failed_capability(
    evidence_refs: tuple[EvidenceRef, ...] | None = None,
    trace_ref: TraceEventRef | None = None,
    source_hash: str | None = None,
    strength: EvidenceStrengthLevel = EvidenceStrengthLevel.NONE,
    limitations: tuple[str, ...] | None = None,
) -> CapabilityEvidenceRecord:
    """Construct a FAILED capability directly (no factory seal needed)."""
    ref = trace_ref or _make_trace_ref()[1]
    if evidence_refs is None:
        evidence_refs = (_evidence_ref(ref),)
    if limitations is None:
        limitations = ("Test limitation.",)
    if source_hash is None:
        source_hash = ref.event_hash
    return CapabilityEvidenceRecord(
        capability_evidence_id="cap_ev_failed_001",
        capability_id="cap.test.failed",
        status=CapabilityEvidenceStatus.FAILED,
        source_trace_event_ref=ref,
        source_event_hash=source_hash,
        evidence_refs=evidence_refs,
        verifier_result_ref="ver_test_001",
        evidence_strength=strength,
        limitations=limitations,
        created_at=_TIMESTAMP,
    )


def _make_inconclusive_capability(
    trace_ref: TraceEventRef | None = None,
    source_hash: str | None = None,
) -> CapabilityEvidenceRecord:
    ref = trace_ref or _make_trace_ref()[1]
    ev = _evidence_ref(ref)
    if source_hash is None:
        source_hash = ref.event_hash
    return CapabilityEvidenceRecord(
        capability_evidence_id="cap_ev_inconclusive_001",
        capability_id="cap.test.inconclusive",
        status=CapabilityEvidenceStatus.INCONCLUSIVE,
        source_trace_event_ref=ref,
        source_event_hash=source_hash,
        evidence_refs=(ev,),
        verifier_result_ref="ver_test_001",
        evidence_strength=EvidenceStrengthLevel.WEAK,
        limitations=("Test limitation.",),
        created_at=_TIMESTAMP,
    )


# ---------------------------------------------------------------------------
# Positive extraction tests
# ---------------------------------------------------------------------------


def test_positive_case_requires_verified_capability_evidence():
    cap = _make_failed_capability()
    ver = _verifier()
    ctx = _context_adequacy()
    report, case = extract_evaluation_case_from_capability_evidence(
        capability=cap, verifier=ver, context_adequacy=ctx,
    )
    assert case is None


def test_positive_case_requires_pass_verifier():
    cap = _make_verified_capability()
    ver = _verifier(status=VerifierResultStatus.FAIL)
    ctx = _context_adequacy()
    report, case = extract_evaluation_case_from_capability_evidence(
        capability=cap, verifier=ver, context_adequacy=ctx,
    )
    assert case is None


def test_positive_case_requires_trace_event_ref():
    # Create a capability with None trace ref and non-matching hash
    ev_ref = _make_trace_ref()[1]
    ev = _evidence_ref(ev_ref)
    cap = CapabilityEvidenceRecord(
        capability_evidence_id="cap_no_trace_001",
        capability_id="cap.test.no_trace",
        status=CapabilityEvidenceStatus.UNVERIFIED,
        source_trace_event_ref=None,
        source_event_hash="abc123",
        evidence_refs=(ev,),
        verifier_result_ref="ver_test_001",
        evidence_strength=EvidenceStrengthLevel.VERIFIED,
        limitations=("Limitation.",),
        created_at=_TIMESTAMP,
    )
    ver = _verifier()
    ctx = _context_adequacy()
    report, case = extract_evaluation_case_from_capability_evidence(
        capability=cap, verifier=ver, context_adequacy=ctx,
    )
    assert case is None


def test_positive_case_requires_matching_source_event_hash():
    ref = _make_trace_ref()[1]
    cap = _make_failed_capability(
        trace_ref=ref,
        source_hash="mismatched_hash_abc123",
    )
    ver = _verifier()
    ctx = _context_adequacy()
    report, case = extract_evaluation_case_from_capability_evidence(
        capability=cap, verifier=ver, context_adequacy=ctx,
    )
    assert case is None


def test_positive_case_requires_evidence_refs():
    ref = _make_trace_ref()[1]
    cap = _make_failed_capability(evidence_refs=(), trace_ref=ref)
    ver = _verifier()
    ctx = _context_adequacy()
    report, case = extract_evaluation_case_from_capability_evidence(
        capability=cap, verifier=ver, context_adequacy=ctx,
    )
    assert case is None


def test_positive_case_requires_limitations():
    ref = _make_trace_ref()[1]
    cap = _make_failed_capability(limitations=(), trace_ref=ref)
    ver = _verifier()
    ctx = _context_adequacy()
    report, case = extract_evaluation_case_from_capability_evidence(
        capability=cap, verifier=ver, context_adequacy=ctx,
    )
    assert case is None


def test_positive_case_blocks_unsafe_context():
    """Unsafe context routes to regression, preventing positive extraction."""
    cap = _make_verified_capability()
    ver = _verifier()
    ctx = _context_adequacy(status=ContextAdequacyStatus.UNSAFE)
    report, case = extract_evaluation_case_from_capability_evidence(
        capability=cap, verifier=ver, context_adequacy=ctx,
    )
    assert case is None, "unsafe context must not produce positive EvaluationCase"
    assert report.extracted_regression_id is not None, (
        "unsafe context should produce regression candidate"
    )
    assert report.extraction_status == ExtractionStatus.EXTRACTED
    assert "unsafe" in report.reason


def test_positive_case_blocks_insufficient_context():
    """Insufficient context routes to regression, preventing positive extraction."""
    cap = _make_verified_capability()
    ver = _verifier()
    ctx = _context_adequacy(status=ContextAdequacyStatus.INSUFFICIENT)
    report, case = extract_evaluation_case_from_capability_evidence(
        capability=cap, verifier=ver, context_adequacy=ctx,
    )
    assert case is None, "insufficient context must not produce positive EvaluationCase"
    assert report.extracted_regression_id is not None, (
        "insufficient context should produce regression candidate"
    )
    assert report.extraction_status == ExtractionStatus.EXTRACTED
    assert "insufficient" in report.reason


def test_positive_case_extracts_with_valid_inputs():
    cap = _make_verified_capability()
    ver = _verifier()
    ctx = _context_adequacy()
    report, case = extract_evaluation_case_from_capability_evidence(
        capability=cap, verifier=ver, context_adequacy=ctx,
    )
    assert case is not None
    assert case.case_kind == EvaluationCaseKind.POSITIVE
    assert case.status == EvaluationCaseStatus.CANDIDATE
    assert case.source_capability_evidence_id == cap.capability_evidence_id
    assert case.source_event_hash == cap.source_event_hash
    assert len(case.evidence_refs) > 0
    assert len(case.known_limitations) > 0
    assert case.failure_mode is None
    assert case.regression_priority is None
    assert report.extraction_status == ExtractionStatus.EXTRACTED
    assert report.extracted_case_id == case.case_id


# ---------------------------------------------------------------------------
# Regression extraction tests
# ---------------------------------------------------------------------------


def test_failed_verifier_extracts_regression_candidate():
    cap = _make_verified_capability()
    ver = _verifier(status=VerifierResultStatus.FAIL)
    ctx = _context_adequacy()
    report, case = extract_evaluation_case_from_capability_evidence(
        capability=cap, verifier=ver, context_adequacy=ctx,
    )
    assert case is None
    assert report.extracted_regression_id is not None
    assert report.extraction_status == ExtractionStatus.EXTRACTED
    assert "verifier_failed" in report.reason


def test_failed_capability_extracts_regression_candidate():
    cap = _make_failed_capability()
    ver = _verifier()
    ctx = _context_adequacy()
    report, case = extract_evaluation_case_from_capability_evidence(
        capability=cap, verifier=ver, context_adequacy=ctx,
    )
    assert case is None
    assert report.extracted_regression_id is not None
    assert report.extraction_status == ExtractionStatus.EXTRACTED


def test_unsafe_context_extracts_regression_candidate():
    cap = _make_verified_capability()
    ver = _verifier()
    ctx = _context_adequacy(status=ContextAdequacyStatus.UNSAFE)
    report, case = extract_evaluation_case_from_capability_evidence(
        capability=cap, verifier=ver, context_adequacy=ctx,
    )
    assert case is None
    assert report.extracted_regression_id is not None
    assert report.extraction_status == ExtractionStatus.EXTRACTED
    assert "unsafe" in report.reason


def test_insufficient_context_extracts_regression_candidate():
    cap = _make_verified_capability()
    ver = _verifier()
    ctx = _context_adequacy(status=ContextAdequacyStatus.INSUFFICIENT)
    report, case = extract_evaluation_case_from_capability_evidence(
        capability=cap, verifier=ver, context_adequacy=ctx,
    )
    assert case is None
    assert report.extracted_regression_id is not None
    assert report.extraction_status == ExtractionStatus.EXTRACTED
    assert "insufficient" in report.reason


def test_weak_evidence_extracts_regression_candidate():
    cap = _make_failed_capability(strength=EvidenceStrengthLevel.WEAK)
    ver = _verifier()
    ctx = _context_adequacy()
    report, case = extract_evaluation_case_from_capability_evidence(
        capability=cap, verifier=ver, context_adequacy=ctx,
    )
    assert case is None
    assert report.extracted_regression_id is not None
    assert report.extraction_status == ExtractionStatus.EXTRACTED


def test_hash_mismatch_extracts_regression_candidate():
    ref = _make_trace_ref()[1]
    cap = _make_failed_capability(
        trace_ref=ref,
        source_hash="mismatched_abc123",
    )
    ver = _verifier()
    ctx = _context_adequacy()
    report, case = extract_evaluation_case_from_capability_evidence(
        capability=cap, verifier=ver, context_adequacy=ctx,
    )
    assert case is None
    assert report.extracted_regression_id is not None
    assert report.extraction_status == ExtractionStatus.EXTRACTED


def test_missing_evidence_extracts_regression_candidate():
    ref = _make_trace_ref()[1]
    cap = _make_failed_capability(evidence_refs=(), trace_ref=ref)
    ver = _verifier()
    ctx = _context_adequacy()
    report, case = extract_evaluation_case_from_capability_evidence(
        capability=cap, verifier=ver, context_adequacy=ctx,
    )
    assert case is None
    assert report.extracted_regression_id is not None
    assert report.extraction_status == ExtractionStatus.EXTRACTED


def test_missing_limitations_extracts_regression_candidate():
    ref = _make_trace_ref()[1]
    cap = _make_failed_capability(limitations=(), trace_ref=ref)
    ver = _verifier()
    ctx = _context_adequacy()
    report, case = extract_evaluation_case_from_capability_evidence(
        capability=cap, verifier=ver, context_adequacy=ctx,
    )
    assert case is None
    assert report.extracted_regression_id is not None
    assert report.extraction_status == ExtractionStatus.EXTRACTED


# ---------------------------------------------------------------------------
# Review extraction tests
# ---------------------------------------------------------------------------


def test_needs_review_verifier_extracts_review_case():
    cap = _make_verified_capability()
    ver = _verifier(status=VerifierResultStatus.NEEDS_REVIEW)
    ctx = _context_adequacy()
    report, case = extract_evaluation_case_from_capability_evidence(
        capability=cap, verifier=ver, context_adequacy=ctx,
    )
    assert case is not None
    assert case.case_kind == EvaluationCaseKind.REVIEW
    assert case.status == EvaluationCaseStatus.NEEDS_REVIEW
    assert report.extraction_status == ExtractionStatus.NEEDS_REVIEW


def test_inconclusive_capability_extracts_review_case():
    cap = _make_inconclusive_capability()
    ver = _verifier()
    ctx = _context_adequacy()
    report, case = extract_evaluation_case_from_capability_evidence(
        capability=cap, verifier=ver, context_adequacy=ctx,
    )
    assert case is not None
    assert case.case_kind == EvaluationCaseKind.REVIEW
    assert case.status == EvaluationCaseStatus.NEEDS_REVIEW
    assert report.extraction_status == ExtractionStatus.NEEDS_REVIEW


def test_partial_context_extracts_review_case():
    cap = _make_verified_capability()
    ver = _verifier()
    ctx = _context_adequacy(status=ContextAdequacyStatus.PARTIAL)
    report, case = extract_evaluation_case_from_capability_evidence(
        capability=cap, verifier=ver, context_adequacy=ctx,
    )
    assert case is not None
    assert case.case_kind == EvaluationCaseKind.REVIEW
    assert case.status == EvaluationCaseStatus.NEEDS_REVIEW
    assert report.extraction_status == ExtractionStatus.NEEDS_REVIEW


# ---------------------------------------------------------------------------
# Candidate-only tests
# ---------------------------------------------------------------------------


def test_extracted_evaluation_case_is_candidate_by_default():
    cap = _make_verified_capability()
    ver = _verifier()
    ctx = _context_adequacy()
    _, case = extract_evaluation_case_from_capability_evidence(
        capability=cap, verifier=ver, context_adequacy=ctx,
    )
    assert case is not None
    assert case.status == EvaluationCaseStatus.CANDIDATE
    assert case.status != EvaluationCaseStatus.ACCEPTED


def test_regression_extraction_returns_candidate():
    cap = _make_failed_capability()
    ver = _verifier()
    ctx = _context_adequacy()
    report, _ = extract_evaluation_case_from_capability_evidence(
        capability=cap, verifier=ver, context_adequacy=ctx,
    )
    assert report.extracted_regression_id is not None
    assert "regression candidate" in report.reason.lower()


def test_extraction_does_not_promote_capability():
    cap = _make_verified_capability()
    ver = _verifier()
    ctx = _context_adequacy()
    _, case = extract_evaluation_case_from_capability_evidence(
        capability=cap, verifier=ver, context_adequacy=ctx,
    )
    assert case is not None
    assert case.status == EvaluationCaseStatus.CANDIDATE
    assert case.status != EvaluationCaseStatus.ACCEPTED


def test_extraction_does_not_create_memory():
    """Extraction produces candidate records only — no memory operations."""
    cap = _make_verified_capability()
    ver = _verifier()
    ctx = _context_adequacy()
    _, case = extract_evaluation_case_from_capability_evidence(
        capability=cap, verifier=ver, context_adequacy=ctx,
    )
    assert case is not None
    assert not hasattr(case, "memory_entry_id")
    assert not hasattr(case, "memory_context")


def test_extraction_does_not_create_skill():
    """Extraction produces candidate records only — no skill creation."""
    cap = _make_verified_capability()
    ver = _verifier()
    ctx = _context_adequacy()
    _, case = extract_evaluation_case_from_capability_evidence(
        capability=cap, verifier=ver, context_adequacy=ctx,
    )
    assert case is not None
    assert not hasattr(case, "skill_id")
    assert not hasattr(case, "skill_manifest")


def test_extraction_does_not_create_reflex():
    """Extraction produces candidate records only — no reflex creation."""
    cap = _make_verified_capability()
    ver = _verifier()
    ctx = _context_adequacy()
    _, case = extract_evaluation_case_from_capability_evidence(
        capability=cap, verifier=ver, context_adequacy=ctx,
    )
    assert case is not None
    assert not hasattr(case, "reflex_id")
    assert not hasattr(case, "reflex_policy")


# ---------------------------------------------------------------------------
# EvaluationCase direct validation tests (impossible states)
# ---------------------------------------------------------------------------


def test_positive_case_cannot_construct_with_failure_mode():
    ref = _make_trace_ref()[1]
    with pytest.raises(ValueError, match="failure_mode"):
        EvaluationCase(
            case_id="case_001",
            case_kind=EvaluationCaseKind.POSITIVE,
            source_capability_evidence_id="cap_001",
            source_trace_event_ref=ref,
            source_event_hash=ref.event_hash,
            evidence_refs=("ev_001",),
            verifier_result_ref="ver_001",
            context_adequacy_ref=None,
            input_snapshot_ref=None,
            expected_behavior=None,
            success_criteria=(),
            known_limitations=("limitation_1",),
            failure_mode=FailureMode.VERIFIER_FAILED,
            regression_priority=None,
            status=EvaluationCaseStatus.CANDIDATE,
            created_at=_TIMESTAMP,
        )


def test_evaluation_case_cannot_construct_with_accepted_status():
    ref = _make_trace_ref()[1]
    with pytest.raises(ValueError):
        EvaluationCase(
            case_id="case_002",
            case_kind=EvaluationCaseKind.POSITIVE,
            source_capability_evidence_id="cap_002",
            source_trace_event_ref=ref,
            source_event_hash=ref.event_hash,
            evidence_refs=("ev_002",),
            verifier_result_ref="ver_002",
            context_adequacy_ref=None,
            input_snapshot_ref=None,
            expected_behavior=None,
            success_criteria=(),
            known_limitations=("limitation_1",),
            failure_mode=None,
            regression_priority=None,
            status=EvaluationCaseStatus.ACCEPTED,
            created_at=_TIMESTAMP,
        )


def test_positive_case_requires_evidence_refs_non_empty():
    ref = _make_trace_ref()[1]
    with pytest.raises(ValueError, match="evidence_refs"):
        EvaluationCase(
            case_id="case_003",
            case_kind=EvaluationCaseKind.POSITIVE,
            source_capability_evidence_id="cap_003",
            source_trace_event_ref=ref,
            source_event_hash=ref.event_hash,
            evidence_refs=(),
            verifier_result_ref="ver_003",
            context_adequacy_ref=None,
            input_snapshot_ref=None,
            expected_behavior=None,
            success_criteria=(),
            known_limitations=("limitation_1",),
            failure_mode=None,
            regression_priority=None,
            status=EvaluationCaseStatus.CANDIDATE,
            created_at=_TIMESTAMP,
        )


def test_positive_case_requires_known_limitations_non_empty():
    ref = _make_trace_ref()[1]
    with pytest.raises(ValueError, match="known_limitations"):
        EvaluationCase(
            case_id="case_004",
            case_kind=EvaluationCaseKind.POSITIVE,
            source_capability_evidence_id="cap_004",
            source_trace_event_ref=ref,
            source_event_hash=ref.event_hash,
            evidence_refs=("ev_004",),
            verifier_result_ref="ver_004",
            context_adequacy_ref=None,
            input_snapshot_ref=None,
            expected_behavior=None,
            success_criteria=(),
            known_limitations=(),
            failure_mode=None,
            regression_priority=None,
            status=EvaluationCaseStatus.CANDIDATE,
            created_at=_TIMESTAMP,
        )


def test_evaluation_case_requires_matching_source_hash():
    ref = _make_trace_ref()[1]
    with pytest.raises(ValueError, match="source_event_hash"):
        EvaluationCase(
            case_id="case_005",
            case_kind=EvaluationCaseKind.POSITIVE,
            source_capability_evidence_id="cap_005",
            source_trace_event_ref=ref,
            source_event_hash="mismatched_hash_xyz",
            evidence_refs=("ev_005",),
            verifier_result_ref="ver_005",
            context_adequacy_ref=None,
            input_snapshot_ref=None,
            expected_behavior=None,
            success_criteria=(),
            known_limitations=("limitation_1",),
            failure_mode=None,
            regression_priority=None,
            status=EvaluationCaseStatus.CANDIDATE,
            created_at=_TIMESTAMP,
        )


def test_review_case_requires_needs_review_status():
    ref = _make_trace_ref()[1]
    with pytest.raises(ValueError, match="needs_review"):
        EvaluationCase(
            case_id="case_006",
            case_kind=EvaluationCaseKind.REVIEW,
            source_capability_evidence_id="cap_006",
            source_trace_event_ref=ref,
            source_event_hash=ref.event_hash,
            evidence_refs=("ev_006",),
            verifier_result_ref="ver_006",
            context_adequacy_ref=None,
            input_snapshot_ref=None,
            expected_behavior=None,
            success_criteria=(),
            known_limitations=(),
            failure_mode=None,
            regression_priority=None,
            status=EvaluationCaseStatus.CANDIDATE,
            created_at=_TIMESTAMP,
        )


# ---------------------------------------------------------------------------
# FailureMode mapping tests
# ---------------------------------------------------------------------------


def test_failure_mode_verifier_failed():
    cap = _make_verified_capability()
    ver = _verifier(status=VerifierResultStatus.FAIL)
    ctx = _context_adequacy()
    mode = _map_failure_mode(capability=cap, verifier=ver, context_adequacy=ctx)
    assert mode == FailureMode.VERIFIER_FAILED


def test_failure_mode_unsafe_context():
    cap = _make_verified_capability()
    ver = _verifier()
    ctx = _context_adequacy(status=ContextAdequacyStatus.UNSAFE)
    mode = _map_failure_mode(capability=cap, verifier=ver, context_adequacy=ctx)
    assert mode == FailureMode.UNSAFE_CONTEXT


def test_failure_mode_insufficient_context():
    cap = _make_verified_capability()
    ver = _verifier()
    ctx = _context_adequacy(status=ContextAdequacyStatus.INSUFFICIENT)
    mode = _map_failure_mode(capability=cap, verifier=ver, context_adequacy=ctx)
    assert mode == FailureMode.INSUFFICIENT_CONTEXT


def test_failure_mode_weak_evidence():
    ref = _make_trace_ref()[1]
    cap = _make_failed_capability(strength=EvidenceStrengthLevel.WEAK, trace_ref=ref)
    ver = _verifier()
    ctx = _context_adequacy()
    mode = _map_failure_mode(capability=cap, verifier=ver, context_adequacy=ctx)
    assert mode == FailureMode.WEAK_EVIDENCE


def test_failure_mode_missing_evidence():
    ref = _make_trace_ref()[1]
    cap = _make_failed_capability(evidence_refs=(), trace_ref=ref)
    ver = _verifier()
    ctx = _context_adequacy()
    mode = _map_failure_mode(capability=cap, verifier=ver, context_adequacy=ctx)
    assert mode == FailureMode.MISSING_EVIDENCE


# ---------------------------------------------------------------------------
# RegressionCandidate direct validation tests
# ---------------------------------------------------------------------------


def test_regression_candidate_cannot_construct_with_accepted_status():
    ref = _make_trace_ref()[1]
    with pytest.raises(ValueError, match="accepted"):
        RegressionCandidate(
            regression_id="reg_001",
            source_case_id=None,
            source_capability_evidence_id="cap_001",
            source_trace_event_ref=ref,
            source_event_hash=ref.event_hash,
            failure_mode=FailureMode.VERIFIER_FAILED,
            reproduction_hint=None,
            priority=RegressionPriority.HIGH,
            evidence_refs=("ev_001",),
            verifier_result_ref="ver_001",
            context_adequacy_ref=None,
            status=EvaluationCaseStatus.ACCEPTED,
            created_at=_TIMESTAMP,
        )


def test_regression_candidate_missing_evidence_allows_empty_evidence_refs():
    ref = _make_trace_ref()[1]
    candidate = RegressionCandidate(
        regression_id="reg_002",
        source_case_id=None,
        source_capability_evidence_id="cap_002",
        source_trace_event_ref=ref,
        source_event_hash=ref.event_hash,
        failure_mode=FailureMode.MISSING_EVIDENCE,
        reproduction_hint=None,
        priority=RegressionPriority.LOW,
        evidence_refs=(),
        verifier_result_ref="ver_002",
        context_adequacy_ref=None,
        status=EvaluationCaseStatus.CANDIDATE,
        created_at=_TIMESTAMP,
    )
    assert candidate.failure_mode == FailureMode.MISSING_EVIDENCE
    assert candidate.evidence_refs == ()


# ---------------------------------------------------------------------------
# Serialization round-trip smoke tests
# ---------------------------------------------------------------------------


def test_evaluation_case_to_dict_roundtrip():
    cap = _make_verified_capability()
    ver = _verifier()
    ctx = _context_adequacy()
    _, case = extract_evaluation_case_from_capability_evidence(
        capability=cap, verifier=ver, context_adequacy=ctx,
    )
    assert case is not None
    d = evaluation_case_to_dict(case)
    assert d["case_id"] == case.case_id
    assert d["case_kind"] == "positive"
    assert d["status"] == "candidate"


def test_regression_candidate_to_dict_roundtrip():
    ref = _make_trace_ref()[1]
    candidate =         RegressionCandidate(
            regression_id="reg_ser_001",
            source_case_id=None,
            source_capability_evidence_id="cap_ser_001",
            source_trace_event_ref=ref,
            source_event_hash=ref.event_hash,
            failure_mode=FailureMode.VERIFIER_FAILED,
            reproduction_hint=None,
            priority=RegressionPriority.HIGH,
            evidence_refs=("ev_ser_001",),
            verifier_result_ref="ver_ser_001",
            context_adequacy_ref=None,
            status=EvaluationCaseStatus.CANDIDATE,
            created_at=_TIMESTAMP,
        )
    d = regression_candidate_to_dict(candidate)
    assert d["regression_id"] == "reg_ser_001"
    assert d["failure_mode"] == "verifier_failed"
    assert d["status"] == "candidate"


def test_extraction_report_to_dict_roundtrip():
    cap = _make_verified_capability()
    ver = _verifier()
    ctx = _context_adequacy()
    report, _ = extract_evaluation_case_from_capability_evidence(
        capability=cap, verifier=ver, context_adequacy=ctx,
    )
    d = extraction_report_to_dict(report)
    assert d["extraction_id"] == report.extraction_id
    assert d["extraction_status"] == "extracted"
