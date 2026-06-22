"""P1.5.1 evaluation result resolution and aggregation tests."""
from __future__ import annotations

from agentic_runtime.evaluation.evaluation_objects import (
    EvaluationConfidenceClass,
    EvaluationCriterionResult,
    EvaluationEvidenceQuality,
    EvaluationFailureMode,
    EvaluationOutcome,
    EvaluationResult,
    EvaluationResultStatus,
    EvaluationVerdict,
    aggregate_evaluation_results,
    resolve_evaluation_result_from_criteria,
)


def _passed_cr(cid: str = "c1", refs: tuple[str, ...] = ("ev1",)) -> EvaluationCriterionResult:
    return EvaluationCriterionResult(
        criterion_id=cid, outcome=EvaluationOutcome.PASSED,
        verdict=EvaluationVerdict.SUPPORTED,
        evidence_quality=EvaluationEvidenceQuality.ADEQUATE,
        evidence_refs=refs, summary="passed",
    )


def test_resolve_no_criteria_to_insufficient_evidence():
    r = resolve_evaluation_result_from_criteria(
        result_id="r1", run_id="run1", criterion_results=(),
    )
    assert r.outcome == EvaluationOutcome.INCONCLUSIVE
    assert r.verdict == EvaluationVerdict.INSUFFICIENT_EVIDENCE


def test_resolve_all_passed_to_supported():
    r = resolve_evaluation_result_from_criteria(
        result_id="r1", run_id="run1",
        criterion_results=(_passed_cr(),),
        evidence_refs=("ev1",),
    )
    assert r.outcome == EvaluationOutcome.PASSED
    assert r.verdict == EvaluationVerdict.SUPPORTED
    assert r.verdict.value != "VERIFIED"


def test_resolve_missing_evidence_to_insufficient_evidence():
    cr = EvaluationCriterionResult(
        criterion_id="c1", outcome=EvaluationOutcome.PASSED,
        verdict=EvaluationVerdict.SUPPORTED,
        evidence_quality=EvaluationEvidenceQuality.WEAK,
        evidence_refs=(), summary="weak",
    )
    r = resolve_evaluation_result_from_criteria(
        result_id="r1", run_id="run1", criterion_results=(cr,),
    )
    assert r.verdict == EvaluationVerdict.INSUFFICIENT_EVIDENCE


def test_resolve_required_failure_to_failed_rejected():
    cr = EvaluationCriterionResult(
        criterion_id="c1", outcome=EvaluationOutcome.FAILED,
        verdict=EvaluationVerdict.REJECTED,
        evidence_quality=EvaluationEvidenceQuality.WEAK,
        failure_modes=(EvaluationFailureMode.REQUIRED_CRITERION_FAILED,),
        summary="required failed",
    )
    r = resolve_evaluation_result_from_criteria(
        result_id="r1", run_id="run1", criterion_results=(cr,),
    )
    assert r.outcome == EvaluationOutcome.FAILED
    assert r.verdict == EvaluationVerdict.REJECTED


def test_resolve_conflicted_evidence_to_conflicted():
    cr = EvaluationCriterionResult(
        criterion_id="c1", outcome=EvaluationOutcome.INCONCLUSIVE,
        verdict=EvaluationVerdict.CONFLICTED,
        evidence_quality=EvaluationEvidenceQuality.CONFLICTED,
        summary="conflict",
    )
    r = resolve_evaluation_result_from_criteria(
        result_id="r1", run_id="run1", criterion_results=(cr,),
    )
    assert r.verdict == EvaluationVerdict.CONFLICTED


def test_resolve_blocked_criterion_to_blocked():
    cr = EvaluationCriterionResult(
        criterion_id="c1", outcome=EvaluationOutcome.BLOCKED,
        verdict=EvaluationVerdict.BLOCKED,
        evidence_quality=EvaluationEvidenceQuality.NONE,
        blockers=("policy blocked",), summary="blocked",
    )
    r = resolve_evaluation_result_from_criteria(
        result_id="r1", run_id="run1", criterion_results=(cr,),
    )
    assert r.outcome == EvaluationOutcome.BLOCKED
    assert r.verdict == EvaluationVerdict.BLOCKED


def test_resolve_mixed_results_to_partially_supported():
    passed = _passed_cr("c1")
    partial = EvaluationCriterionResult(
        criterion_id="c2", outcome=EvaluationOutcome.SKIPPED,
        verdict=EvaluationVerdict.PARTIALLY_SUPPORTED,
        evidence_quality=EvaluationEvidenceQuality.ADEQUATE,
        evidence_refs=("ev2",), summary="skipped",
    )
    r = resolve_evaluation_result_from_criteria(
        result_id="r1", run_id="run1", criterion_results=(passed, partial),
        evidence_refs=("ev1", "ev2"),
    )
    assert r.outcome == EvaluationOutcome.PARTIAL
    assert r.verdict == EvaluationVerdict.PARTIALLY_SUPPORTED


def _make_result(outcome, verdict, quality=EvaluationEvidenceQuality.ADEQUATE):
    return EvaluationResult(
        result_id=f"r_{outcome.value}", run_id="run1",
        status=EvaluationResultStatus.COMPLETED,
        outcome=outcome, verdict=verdict,
        confidence=EvaluationConfidenceClass.MODERATE,
        evidence_quality=quality,
    )


def test_aggregate_empty_results_inconclusive_or_blocked():
    rs = aggregate_evaluation_results(result_set_id="rs1", run_id="run1", results=())
    assert rs.aggregate_outcome == EvaluationOutcome.INCONCLUSIVE
    assert rs.blockers


def test_aggregate_blocked_dominates():
    blocked = _make_result(EvaluationOutcome.BLOCKED, EvaluationVerdict.BLOCKED, EvaluationEvidenceQuality.NONE)
    passed = _make_result(EvaluationOutcome.PASSED, EvaluationVerdict.SUPPORTED)
    rs = aggregate_evaluation_results(result_set_id="rs1", run_id="run1", results=(passed, blocked))
    assert rs.aggregate_outcome == EvaluationOutcome.BLOCKED


def test_aggregate_conflicted_blocks_supported():
    conflicted = _make_result(EvaluationOutcome.INCONCLUSIVE, EvaluationVerdict.CONFLICTED, EvaluationEvidenceQuality.CONFLICTED)
    passed = _make_result(EvaluationOutcome.PASSED, EvaluationVerdict.SUPPORTED)
    rs = aggregate_evaluation_results(result_set_id="rs1", run_id="run1", results=(passed, conflicted))
    assert rs.aggregate_verdict != EvaluationVerdict.SUPPORTED


def test_aggregate_failed_dominates_partial():
    failed = _make_result(EvaluationOutcome.FAILED, EvaluationVerdict.UNSUPPORTED, EvaluationEvidenceQuality.WEAK)
    partial = _make_result(EvaluationOutcome.PARTIAL, EvaluationVerdict.PARTIALLY_SUPPORTED)
    rs = aggregate_evaluation_results(result_set_id="rs1", run_id="run1", results=(partial, failed))
    assert rs.aggregate_outcome == EvaluationOutcome.FAILED


def test_aggregate_partial_dominates_passed():
    partial = _make_result(EvaluationOutcome.PARTIAL, EvaluationVerdict.PARTIALLY_SUPPORTED)
    passed = _make_result(EvaluationOutcome.PASSED, EvaluationVerdict.SUPPORTED)
    rs = aggregate_evaluation_results(result_set_id="rs1", run_id="run1", results=(passed, partial))
    assert rs.aggregate_outcome == EvaluationOutcome.PARTIAL


def test_aggregate_does_not_average_numeric_scores():
    rs = aggregate_evaluation_results(
        result_set_id="rs1", run_id="run1",
        results=(_make_result(EvaluationOutcome.PASSED, EvaluationVerdict.SUPPORTED),),
    )
    assert not hasattr(rs, "score")
    assert not hasattr(rs, "numeric_score")
    assert not hasattr(rs, "average_score")
