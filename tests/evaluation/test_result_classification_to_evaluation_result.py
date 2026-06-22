"""Conversion tests — P1.5.6."""
from __future__ import annotations

from agentic_runtime.evaluation.result_classification import (
    CriterionClassificationDecision,
    EvaluationObservation,
    EvaluationObservationStatus,
    EvaluationObservationType,
    criterion_decision_to_result,
    result_classification_to_evaluation_result,
)
from agentic_runtime.evaluation.evaluation_objects import (
    EvaluationConfidenceClass,
    EvaluationEvidenceQuality,
    EvaluationFailureMode,
    EvaluationOutcome,
    EvaluationResult,
    EvaluationVerdict,
)


def _make_decision(**kwargs: object) -> CriterionClassificationDecision:
    defaults: dict[str, object] = {
        "criterion_id": "crit_001",
        "outcome": EvaluationOutcome.PASSED,
        "verdict": EvaluationVerdict.SUPPORTED,
        "confidence": EvaluationConfidenceClass.MODERATE,
        "evidence_quality": EvaluationEvidenceQuality.ADEQUATE,
        "failure_modes": (),
        "evidence_refs": ("ref_01",),
        "warnings": (),
        "blockers": (),
        "summary": "Test decision",
    }
    defaults.update(kwargs)
    return CriterionClassificationDecision(**defaults)  # type: ignore[arg-type]


def test_criterion_decision_to_evaluation_criterion_result():
    d = _make_decision()
    result = criterion_decision_to_result(d)
    assert result.criterion_id == "crit_001"
    assert result.outcome == EvaluationOutcome.PASSED
    assert result.verdict == EvaluationVerdict.SUPPORTED
    assert result.evidence_quality == EvaluationEvidenceQuality.ADEQUATE


def test_conversion_preserves_failure_modes():
    d = _make_decision(failure_modes=(EvaluationFailureMode.MISSING_EVIDENCE,))
    result = criterion_decision_to_result(d)
    assert EvaluationFailureMode.MISSING_EVIDENCE in result.failure_modes


def test_conversion_preserves_evidence_refs():
    d = _make_decision(evidence_refs=("ref_a", "ref_b"))
    result = criterion_decision_to_result(d)
    assert "ref_a" in result.evidence_refs
    assert "ref_b" in result.evidence_refs


def test_conversion_preserves_warnings_and_blockers():
    d = _make_decision(warnings=("w1",), blockers=("b1",))
    result = criterion_decision_to_result(d)
    assert "w1" in result.warnings
    assert "b1" in result.blockers


def test_result_classification_to_evaluation_result():
    d1 = _make_decision(criterion_id="crit_001", evidence_refs=("ref_01",))
    d2 = _make_decision(criterion_id="crit_002", evidence_refs=("ref_02",))

    from agentic_runtime.evaluation.result_classification import ResultClassificationDecision

    rcd = ResultClassificationDecision(
        run_id="r1",
        status="READY",
        outcome=EvaluationOutcome.PASSED,
        verdict=EvaluationVerdict.SUPPORTED,
        confidence=EvaluationConfidenceClass.MODERATE,
        evidence_quality=EvaluationEvidenceQuality.ADEQUATE,
        criterion_decisions=(d1, d2),
        failure_modes=(),
        evidence_refs=("ref_01", "ref_02"),
    )

    result = result_classification_to_evaluation_result(
        result_id="result_001",
        decision=rcd,
    )
    assert isinstance(result, EvaluationResult)
    assert result.result_id == "result_001"
    assert result.run_id == "r1"
    assert len(result.criterion_results) == 2


def test_conversion_does_not_create_capability_evidence_record():
    d = _make_decision()
    result = criterion_decision_to_result(d)
    assert not hasattr(result, "capability_evidence_record")
    assert not hasattr(result, "evidence_record")


def test_conversion_does_not_verify_capability():
    d = _make_decision()
    result = criterion_decision_to_result(d)
    assert result.verdict.value != "VERIFIED"


def test_conversion_blocked_decision_is_blocked():
    from agentic_runtime.evaluation.result_classification import ResultClassificationDecision

    rcd = ResultClassificationDecision(
        run_id="r1",
        status="BLOCKED",
        outcome=EvaluationOutcome.BLOCKED,
        verdict=EvaluationVerdict.BLOCKED,
        confidence=EvaluationConfidenceClass.NONE,
        evidence_quality=EvaluationEvidenceQuality.NONE,
        criterion_decisions=(),
        failure_modes=(),
        blockers=("blocker1",),
    )

    result = result_classification_to_evaluation_result(
        result_id="result_001",
        decision=rcd,
    )
    assert result.outcome == EvaluationOutcome.BLOCKED
    assert result.verdict == EvaluationVerdict.BLOCKED
