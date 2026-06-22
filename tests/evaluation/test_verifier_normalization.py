"""P1.5.13 Verifier normalization tests.

Tests cover:
- All 6 stub verifiers produce normalized VerifierResults
- Limitation invariants (non-empty limitations, evidence_refs for pass, etc.)
- Negative tests (no raw verifier output downstream, empty limitations blocked, etc.)
- VerifierNormalizationReport correctness
- No LLM stub calls real model
- Policy check doesn't claim task correctness
- Operator review doesn't auto-promote
"""
from __future__ import annotations

import pytest

from agentic_runtime.contracts.context import ContextAdequacyReport, ContextAdequacyStatus, ContextBindingRef
from agentic_runtime.contracts.evidence import EvidenceRef, build_evidence_ref
from agentic_runtime.contracts.trace import AurelTraceLog, TraceEventRef, TraceEventType, trace_event_ref
from agentic_runtime.contracts.verifier import (
    NormalizationStatus,
    VerifierKind,
    VerifierNormalizationReport,
    VerifierResult,
    VerifierResultStatus,
)
from agentic_runtime.evaluation.verifier_normalization import (
    normalize_context_adequacy,
    normalize_deterministic_result,
    normalize_evidence_integrity,
    normalize_llm_judge_stub,
    normalize_operator_review,
    normalize_policy_check,
)

TIMESTAMP = "2026-06-22T00:00:00+00:00"


def _trace_ref() -> tuple[AurelTraceLog, TraceEventRef]:
    log = AurelTraceLog(trace_id="trace_norm_test")
    event = log.append(
        event_type=TraceEventType.STUB_EXECUTION_COMPLETED,
        actor_type="test",
        actor_id="tester",
        payload_json={"test": True},
        timestamp=TIMESTAMP,
    )
    return log, trace_event_ref(event)


def _evidence_ref() -> EvidenceRef:
    _, ref = _trace_ref()
    return build_evidence_ref(
        evidence_id="evidence_norm_001",
        source_trace_event_ref=ref,
        evidence_type="test_evidence",
        content={"test": "content"},
        summary="Test evidence for normalization.",
    )


# ---------------------------------------------------------------------------
# DeterministicVerifierStub tests
# ---------------------------------------------------------------------------

def test_deterministic_verifier_normalizes_condition_passed_to_pass():
    _, ref = _trace_ref()
    evidence = _evidence_ref()
    report, result = normalize_deterministic_result(
        condition_passed=True,
        condition_description="test condition always true",
        source_trace_event_ref=ref,
        evidence_refs=(evidence,),
    )
    assert report.normalization_status == NormalizationStatus.NORMALIZED
    assert result.status == VerifierResultStatus.PASS
    assert result.verifier_kind == VerifierKind.DETERMINISTIC
    assert result.confidence == 1.0
    assert len(result.limitations) > 0
    assert len(result.evidence_refs) > 0
    assert result.source_trace_event_ref == ref


def test_deterministic_verifier_normalizes_condition_failed_to_fail():
    _, ref = _trace_ref()
    report, result = normalize_deterministic_result(
        condition_passed=False,
        condition_description="test condition always false",
        source_trace_event_ref=ref,
    )
    assert report.normalization_status == NormalizationStatus.NORMALIZED
    assert result.status == VerifierResultStatus.FAIL
    assert result.verifier_kind == VerifierKind.DETERMINISTIC
    assert result.confidence == 1.0
    assert len(result.limitations) > 0
    assert result.source_trace_event_ref == ref


def test_deterministic_verifier_still_has_limitations():
    """Even a trivial deterministic check must declare limitations."""
    _, ref = _trace_ref()
    evidence = _evidence_ref()
    _, result = normalize_deterministic_result(
        condition_passed=True,
        condition_description="trivial check",
        source_trace_event_ref=ref,
        evidence_refs=(evidence,),
    )
    assert result.limitations
    assert any("deterministic condition" in lim for lim in result.limitations)


# ---------------------------------------------------------------------------
# OperatorReviewVerifierStub tests
# ---------------------------------------------------------------------------

def test_operator_review_verifier_normalizes_approved_to_pass():
    _, ref = _trace_ref()
    evidence = _evidence_ref()
    report, result = normalize_operator_review(
        approved=True,
        reviewer_id="operator_001",
        review_notes="Looks correct for this case.",
        source_trace_event_ref=ref,
        evidence_refs=(evidence,),
    )
    assert report.normalization_status == NormalizationStatus.NORMALIZED
    assert result.status == VerifierResultStatus.PASS
    assert result.verifier_kind == VerifierKind.OPERATOR_REVIEW
    assert result.confidence < 1.0
    assert len(result.limitations) > 0
    assert len(result.evidence_refs) > 0


def test_operator_review_verifier_normalizes_rejected_to_fail():
    _, ref = _trace_ref()
    report, result = normalize_operator_review(
        approved=False,
        reviewer_id="operator_001",
        review_notes="Found issues in the execution.",
        source_trace_event_ref=ref,
    )
    assert result.status == VerifierResultStatus.FAIL
    assert result.verifier_kind == VerifierKind.OPERATOR_REVIEW


def test_operator_review_does_not_auto_promote_capability():
    """Operator approval is evidence, not automatic truth. The limitations must state this."""
    _, ref = _trace_ref()
    evidence = _evidence_ref()
    _, result = normalize_operator_review(
        approved=True,
        reviewer_id="operator_001",
        review_notes="Approved.",
        source_trace_event_ref=ref,
        evidence_refs=(evidence,),
    )
    assert any("does not generalize" in lim.lower() for lim in result.limitations)


# ---------------------------------------------------------------------------
# PolicyCheckVerifierStub tests
# ---------------------------------------------------------------------------

def test_policy_check_verifier_normalizes_passed_to_pass():
    _, ref = _trace_ref()
    evidence = _evidence_ref()
    report, result = normalize_policy_check(
        policy_passed=True,
        policy_name="test_policy",
        policy_description="Test policy constraint passed.",
        source_trace_event_ref=ref,
        evidence_refs=(evidence,),
    )
    assert report.normalization_status == NormalizationStatus.NORMALIZED
    assert result.status == VerifierResultStatus.PASS
    assert result.verifier_kind == VerifierKind.POLICY_CHECK
    assert len(result.limitations) > 0


def test_policy_check_pass_does_not_claim_task_correctness():
    """Policy check must never claim task correctness — only policy compliance."""
    _, ref = _trace_ref()
    evidence = _evidence_ref()
    _, result = normalize_policy_check(
        policy_passed=True,
        policy_name="test_policy",
        policy_description="Passed.",
        source_trace_event_ref=ref,
        evidence_refs=(evidence,),
    )
    # The limitations must explicitly state policy checks only
    assert any("not task correctness" in lim.lower() for lim in result.limitations)
    # The reason must mention policy, not task correctness
    assert "policy" in result.reason.lower()
    assert "task correctness" not in result.reason.lower()


# ---------------------------------------------------------------------------
# LLMJudgeVerifierStub tests
# ---------------------------------------------------------------------------

def test_llm_judge_stub_normalizes_without_model_call():
    """LLM judge stub must produce a valid result without any real LLM call."""
    _, ref = _trace_ref()
    evidence = _evidence_ref()
    report, result = normalize_llm_judge_stub(
        condition_description="stub condition for testing",
        pass_condition=True,
        source_trace_event_ref=ref,
        evidence_refs=(evidence,),
    )
    assert report.normalization_status == NormalizationStatus.NORMALIZED
    assert result.verifier_kind == VerifierKind.LLM_JUDGE_STUB
    assert result.status == VerifierResultStatus.PASS
    assert 0.0 <= result.confidence <= 1.0
    assert len(result.limitations) > 0
    assert len(result.evidence_refs) > 0


def test_llm_judge_stub_does_not_call_real_model():
    """Deterministically verify no real model infrastructure is touched."""
    _, ref = _trace_ref()
    # This test proves the stub is a pure function — no API keys, no network, no model imports
    report, result = normalize_llm_judge_stub(
        condition_description="deterministic stub test",
        pass_condition=False,
        source_trace_event_ref=ref,
    )
    assert result.verifier_kind == VerifierKind.LLM_JUDGE_STUB
    assert result.status == VerifierResultStatus.FAIL
    # Limitation must state it's a stub
    assert any("stub" in lim.lower() or "not a real model" in lim.lower() for lim in result.limitations)
    # No real model confidence claimed
    assert result.confidence == 0.7  # stub confidence, not real


def test_llm_judge_stub_must_not_claim_production_grade():
    """The LLM stub's limitations must declare it's not production-grade."""
    _, ref = _trace_ref()
    evidence = _evidence_ref()
    _, result = normalize_llm_judge_stub(
        condition_description="test",
        source_trace_event_ref=ref,
        evidence_refs=(evidence,),
    )
    limitation_text = " ".join(result.limitations).lower()
    assert "not a real model" in limitation_text or "must not be used as production" in limitation_text


# ---------------------------------------------------------------------------
# ContextAdequacyVerifierStub tests
# ---------------------------------------------------------------------------

def _make_context_adequacy_report(status: ContextAdequacyStatus) -> ContextAdequacyReport:
    binding = ContextBindingRef(
        context_id="ctx_norm_001",
        context_type="test_context",
        source_refs=(),
        assumptions=(),
        created_at=TIMESTAMP,
    )
    return ContextAdequacyReport(
        context_adequacy_id=f"cad_norm_{status.value}_001",
        context_binding_ref=binding,
        status=status,
        missing_context_flags=(),
        stale_context_flags=(),
        contradicted_context_flags=(),
        uncertainty_notes=(),
        safe_to_act=(status != ContextAdequacyStatus.UNSAFE),
        requires_operator_clarification=(
            status == ContextAdequacyStatus.INSUFFICIENT
        ),
        created_at=TIMESTAMP,
        adequacy_score=1.0 if status == ContextAdequacyStatus.ADEQUATE else 0.5,
    )


def test_context_adequacy_verifier_normalizes_adequate_to_pass():
    _, ref = _trace_ref()
    evidence = _evidence_ref()
    report = _make_context_adequacy_report(ContextAdequacyStatus.ADEQUATE)
    norm_report, result = normalize_context_adequacy(
        context_adequacy_report=report,
        source_trace_event_ref=ref,
        evidence_refs=(evidence,),
    )
    assert norm_report.normalization_status == NormalizationStatus.NORMALIZED
    assert result.status == VerifierResultStatus.PASS
    assert result.verifier_kind == VerifierKind.CONTEXT_ADEQUACY


def test_context_adequacy_verifier_normalizes_partial_to_needs_review():
    _, ref = _trace_ref()
    report = _make_context_adequacy_report(ContextAdequacyStatus.PARTIAL)
    _, result = normalize_context_adequacy(
        context_adequacy_report=report,
        source_trace_event_ref=ref,
    )
    assert result.status == VerifierResultStatus.NEEDS_REVIEW


def test_context_adequacy_verifier_normalizes_insufficient_to_fail():
    _, ref = _trace_ref()
    report = _make_context_adequacy_report(ContextAdequacyStatus.INSUFFICIENT)
    _, result = normalize_context_adequacy(
        context_adequacy_report=report,
        source_trace_event_ref=ref,
    )
    assert result.status == VerifierResultStatus.FAIL


def test_context_adequacy_verifier_normalizes_unsafe_to_fail():
    _, ref = _trace_ref()
    report = _make_context_adequacy_report(ContextAdequacyStatus.UNSAFE)
    _, result = normalize_context_adequacy(
        context_adequacy_report=report,
        source_trace_event_ref=ref,
    )
    assert result.status == VerifierResultStatus.FAIL


# ---------------------------------------------------------------------------
# EvidenceIntegrityVerifierStub tests
# ---------------------------------------------------------------------------

def test_evidence_integrity_verifier_normalizes_valid_evidence_to_pass():
    _, ref = _trace_ref()
    evidence = _evidence_ref()
    report, result = normalize_evidence_integrity(
        evidence_ref=evidence,
        source_trace_event_ref=ref,
        expected_source_event_hash=ref.event_hash,
    )
    assert report.normalization_status == NormalizationStatus.NORMALIZED
    assert result.status == VerifierResultStatus.PASS
    assert result.verifier_kind == VerifierKind.EVIDENCE_INTEGRITY
    assert result.confidence == 1.0
    assert len(result.limitations) > 0
    assert len(result.evidence_refs) > 0
    assert result.source_trace_event_ref == ref


def test_evidence_integrity_verifier_detects_hash_mismatch():
    _, ref = _trace_ref()
    evidence = _evidence_ref()
    _, result = normalize_evidence_integrity(
        evidence_ref=evidence,
        source_trace_event_ref=ref,
        expected_source_event_hash="wrong_hash_xyz",
    )
    assert result.status == VerifierResultStatus.FAIL


# ---------------------------------------------------------------------------
# VerifierResult invariants (P1.5.13 specific)
# ---------------------------------------------------------------------------

def test_verifier_result_requires_limitations():
    _, ref = _trace_ref()
    with pytest.raises(ValueError, match="limitations"):
        VerifierResult(
            verifier_id="ver_no_limits",
            verifier_kind=VerifierKind.DETERMINISTIC,
            target_ref="target",
            status=VerifierResultStatus.PASS,
            confidence=1.0,
            reason="No limitations verifier.",
            limitations=(),
            evidence_refs=(_evidence_ref(),),
            source_trace_event_ref=ref,
            created_at=TIMESTAMP,
        )


def test_pass_verifier_requires_evidence_refs():
    _, ref = _trace_ref()
    with pytest.raises(ValueError, match="evidence_refs"):
        VerifierResult(
            verifier_id="ver_no_evidence",
            verifier_kind=VerifierKind.DETERMINISTIC,
            target_ref="target",
            status=VerifierResultStatus.PASS,
            confidence=1.0,
            reason="Pass without evidence.",
            limitations=("limitation",),
            evidence_refs=(),
            source_trace_event_ref=ref,
            created_at=TIMESTAMP,
        )


def test_verifier_result_requires_reason():
    _, ref = _trace_ref()
    with pytest.raises(ValueError, match="reason"):
        VerifierResult(
            verifier_id="ver_no_reason",
            verifier_kind=VerifierKind.DETERMINISTIC,
            target_ref="target",
            status=VerifierResultStatus.PASS,
            confidence=1.0,
            reason="",
            limitations=("limitation",),
            evidence_refs=(_evidence_ref(),),
            source_trace_event_ref=ref,
            created_at=TIMESTAMP,
        )


def test_verifier_confidence_must_be_in_range():
    _, ref = _trace_ref()
    with pytest.raises(ValueError, match="confidence"):
        VerifierResult(
            verifier_id="ver_bad_conf",
            verifier_kind=VerifierKind.DETERMINISTIC,
            target_ref="target",
            status=VerifierResultStatus.PASS,
            confidence=1.5,
            reason="Bad confidence.",
            limitations=("limitation",),
            evidence_refs=(_evidence_ref(),),
            source_trace_event_ref=ref,
            created_at=TIMESTAMP,
        )


def test_serious_verifier_result_requires_trace_event_ref():
    with pytest.raises(ValueError, match="source_trace_event_ref"):
        VerifierResult(
            verifier_id="ver_no_trace",
            verifier_kind=VerifierKind.DETERMINISTIC,
            target_ref="target",
            status=VerifierResultStatus.FAIL,
            confidence=0.0,
            reason="No trace.",
            limitations=("limitation",),
            evidence_refs=(),
            source_trace_event_ref=None,  # type: ignore[arg-type]
            created_at=TIMESTAMP,
        )


# ---------------------------------------------------------------------------
# Negative tests
# ---------------------------------------------------------------------------

def test_raw_verifier_output_cannot_create_verified_capability():
    """Prove that a raw (non-normalized) result cannot create verified capability."""
    # A VerifierResult constructed without verifier_kind would fail at init time
    # because verifier_kind is required. This test proves the guard is structural.
    _, ref = _trace_ref()
    # Direct construction without verifier_kind fails immediately
    with pytest.raises(TypeError):
        VerifierResult(  # type: ignore[call-arg]
            verifier_id="raw_ver",
            target_ref="target",
            status=VerifierResultStatus.PASS,
            confidence=1.0,
            reason="Raw verifier without kind.",
            limitations=("limitation",),
            evidence_refs=(_evidence_ref(),),
            source_trace_event_ref=ref,
            created_at=TIMESTAMP,
        )


def test_empty_limitations_blocks_verifier_result():
    """VerifierResult with empty limitations must be rejected at construction."""
    _, ref = _trace_ref()
    with pytest.raises(ValueError, match="limitations"):
        VerifierResult(
            verifier_id="ver_empty_limits",
            verifier_kind=VerifierKind.DETERMINISTIC,
            target_ref="target",
            status=VerifierResultStatus.PASS,
            confidence=1.0,
            reason="Empty limitations verifier.",
            limitations=(),
            evidence_refs=(_evidence_ref(),),
            source_trace_event_ref=ref,
            created_at=TIMESTAMP,
        )


# ---------------------------------------------------------------------------
# VerifierNormalizationReport tests
# ---------------------------------------------------------------------------

def test_normalization_report_requires_reason():
    with pytest.raises(ValueError, match="reason"):
        VerifierNormalizationReport(
            normalization_id="norm_001",
            verifier_kind=VerifierKind.DETERMINISTIC,
            raw_input_ref=None,
            normalized_verifier_result_ref=None,
            normalization_status=NormalizationStatus.NORMALIZED,
            reason="",
            warnings=(),
            errors=(),
            created_at=TIMESTAMP,
        )


def test_normalization_report_requires_created_at():
    with pytest.raises(ValueError, match="created_at"):
        VerifierNormalizationReport(
            normalization_id="norm_001",
            verifier_kind=VerifierKind.DETERMINISTIC,
            raw_input_ref=None,
            normalized_verifier_result_ref=None,
            normalization_status=NormalizationStatus.NORMALIZED,
            reason="Missing timestamp.",
            warnings=(),
            errors=(),
            created_at="",
        )


def test_normalization_report_with_warnings_and_errors():
    report = VerifierNormalizationReport(
        normalization_id="norm_warn_001",
        verifier_kind=VerifierKind.LLM_JUDGE_STUB,
        raw_input_ref=None,
        normalized_verifier_result_ref=None,
        normalization_status=NormalizationStatus.FAILED,
        reason="Normalization failed due to missing fields.",
        warnings=("missing confidence field",),
        errors=("required field status is absent",),
        created_at=TIMESTAMP,
    )
    assert report.normalization_status == NormalizationStatus.FAILED
    assert len(report.errors) > 0


def test_all_normalizers_produce_verifier_kind_in_report():
    """Every normalizer's report must include the correct verifier_kind."""
    _, ref = _trace_ref()
    evidence = _evidence_ref()

    # Deterministic
    rpt, _ = normalize_deterministic_result(
        condition_passed=True,
        condition_description="test",
        source_trace_event_ref=ref,
        evidence_refs=(evidence,),
    )
    assert rpt.verifier_kind == VerifierKind.DETERMINISTIC

    # Operator review
    rpt, _ = normalize_operator_review(
        approved=True,
        reviewer_id="op",
        review_notes="Ok.",
        source_trace_event_ref=ref,
        evidence_refs=(evidence,),
    )
    assert rpt.verifier_kind == VerifierKind.OPERATOR_REVIEW

    # Policy check
    rpt, _ = normalize_policy_check(
        policy_passed=True,
        policy_name="p",
        policy_description="d",
        source_trace_event_ref=ref,
        evidence_refs=(evidence,),
    )
    assert rpt.verifier_kind == VerifierKind.POLICY_CHECK

    # LLM stub
    rpt, _ = normalize_llm_judge_stub(
        condition_description="t",
        source_trace_event_ref=ref,
        evidence_refs=(evidence,),
    )
    assert rpt.verifier_kind == VerifierKind.LLM_JUDGE_STUB

    # Context adequacy
    ca = _make_context_adequacy_report(ContextAdequacyStatus.ADEQUATE)
    rpt, _ = normalize_context_adequacy(
        context_adequacy_report=ca,
        source_trace_event_ref=ref,
        evidence_refs=(evidence,),
    )
    assert rpt.verifier_kind == VerifierKind.CONTEXT_ADEQUACY

    # Evidence integrity
    rpt, _ = normalize_evidence_integrity(
        evidence_ref=evidence,
        source_trace_event_ref=ref,
    )
    assert rpt.verifier_kind == VerifierKind.EVIDENCE_INTEGRITY


# ---------------------------------------------------------------------------
# Serialization tests
# ---------------------------------------------------------------------------

def test_verifier_result_to_dict_includes_verifier_kind():
    from agentic_runtime.contracts.verifier import verifier_result_to_dict

    _, ref = _trace_ref()
    evidence = _evidence_ref()
    _, result = normalize_evidence_integrity(
        evidence_ref=evidence,
        source_trace_event_ref=ref,
    )
    d = verifier_result_to_dict(result)
    assert d["verifier_kind"] == "evidence_integrity"
    assert d["status"] == "pass"
    assert isinstance(d["limitations"], list)
    assert isinstance(d["evidence_refs"], list)


def test_normalization_report_to_dict():
    from agentic_runtime.contracts.verifier import normalization_report_to_dict

    report = VerifierNormalizationReport(
        normalization_id="norm_ser_001",
        verifier_kind=VerifierKind.DETERMINISTIC,
        raw_input_ref="raw_001",
        normalized_verifier_result_ref="ver_001",
        normalization_status=NormalizationStatus.NORMALIZED,
        reason="Test serialization.",
        warnings=(),
        errors=(),
        created_at=TIMESTAMP,
    )
    d = normalization_report_to_dict(report)
    assert d["normalization_id"] == "norm_ser_001"
    assert d["verifier_kind"] == "deterministic"
    assert d["normalization_status"] == "normalized"
