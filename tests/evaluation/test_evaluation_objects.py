"""P1.5.1 core evaluation object model tests."""
from __future__ import annotations

import json
import pytest

from agentic_runtime.evaluation.evaluation_objects import (
    EvaluationConfidenceClass,
    EvaluationCriterionResult,
    EvaluationEvidenceQuality,
    EvaluationFailureMode,
    EvaluationOutcome,
    EvaluationResult,
    EvaluationResultStatus,
    EvaluationVerdict,
    validate_evaluation_criterion_result,
    validate_evaluation_result,
)


def test_evaluation_result_status_closed_world():
    assert EvaluationResultStatus.COMPLETED.value == "COMPLETED"
    assert len(EvaluationResultStatus) >= 6


def test_evaluation_outcome_closed_world():
    assert EvaluationOutcome.PASSED.value == "PASSED"
    assert EvaluationOutcome.INCONCLUSIVE.value == "INCONCLUSIVE"
    assert len(EvaluationOutcome) >= 7


def test_evaluation_verdict_closed_world():
    assert EvaluationVerdict.SUPPORTED.value == "SUPPORTED"
    assert not hasattr(EvaluationVerdict, "VERIFIED")
    assert "VERIFIED" not in {v.value for v in EvaluationVerdict}


def test_evaluation_confidence_class_closed_world():
    assert EvaluationConfidenceClass.MODERATE.value == "MODERATE"
    assert len(EvaluationConfidenceClass) >= 5


def test_evaluation_evidence_quality_closed_world():
    assert EvaluationEvidenceQuality.ADEQUATE.value == "ADEQUATE"
    assert len(EvaluationEvidenceQuality) >= 7


def test_evaluation_failure_mode_closed_world():
    assert EvaluationFailureMode.REQUIRED_CRITERION_FAILED.value == "REQUIRED_CRITERION_FAILED"
    assert len(EvaluationFailureMode) >= 15


def test_build_criterion_result():
    cr = EvaluationCriterionResult(
        criterion_id="c1", outcome=EvaluationOutcome.PASSED,
        verdict=EvaluationVerdict.SUPPORTED,
        evidence_quality=EvaluationEvidenceQuality.ADEQUATE,
        evidence_refs=("ev1",), summary="ok",
    )
    assert cr.criterion_id == "c1"
    assert validate_evaluation_criterion_result(cr) == ()


def test_validate_criterion_result_rejects_empty_id():
    cr = EvaluationCriterionResult(
        criterion_id="", outcome=EvaluationOutcome.PASSED,
        verdict=EvaluationVerdict.SUPPORTED,
        evidence_quality=EvaluationEvidenceQuality.ADEQUATE,
        evidence_refs=("ev1",),
    )
    assert any("criterion_id" in e for e in validate_evaluation_criterion_result(cr))


def test_validate_supported_criterion_requires_evidence():
    cr = EvaluationCriterionResult(
        criterion_id="c1", outcome=EvaluationOutcome.PASSED,
        verdict=EvaluationVerdict.SUPPORTED,
        evidence_quality=EvaluationEvidenceQuality.ADEQUATE,
        evidence_refs=(),
    )
    assert any("evidence_refs" in e for e in validate_evaluation_criterion_result(cr))


def test_validate_supported_criterion_requires_adequate_or_strong():
    cr = EvaluationCriterionResult(
        criterion_id="c1", outcome=EvaluationOutcome.PASSED,
        verdict=EvaluationVerdict.SUPPORTED,
        evidence_quality=EvaluationEvidenceQuality.WEAK,
        evidence_refs=("ev1",),
    )
    assert any("ADEQUATE" in e for e in validate_evaluation_criterion_result(cr))


def test_validate_blocked_criterion_requires_blockers():
    cr = EvaluationCriterionResult(
        criterion_id="c1", outcome=EvaluationOutcome.BLOCKED,
        verdict=EvaluationVerdict.BLOCKED,
        evidence_quality=EvaluationEvidenceQuality.NONE,
        blockers=(),
    )
    assert any("blockers" in e for e in validate_evaluation_criterion_result(cr))


def test_validate_failed_criterion_requires_failure_modes():
    cr = EvaluationCriterionResult(
        criterion_id="c1", outcome=EvaluationOutcome.FAILED,
        verdict=EvaluationVerdict.UNSUPPORTED,
        evidence_quality=EvaluationEvidenceQuality.WEAK,
        failure_modes=(),
    )
    assert any("failure_modes" in e for e in validate_evaluation_criterion_result(cr))


def test_evaluation_result_json_serializable():
    from agentic_runtime.evaluation.evaluation_objects import (
        evaluation_result_to_dict, example_supported_evaluation_result,
    )
    r = example_supported_evaluation_result()
    d = evaluation_result_to_dict(r)
    assert json.loads(json.dumps(d))["result_id"] == r.result_id


def test_completed_result_requires_criterion_results():
    r = EvaluationResult(
        result_id="r1", run_id="run1",
        status=EvaluationResultStatus.COMPLETED,
        outcome=EvaluationOutcome.PASSED, verdict=EvaluationVerdict.SUPPORTED,
        confidence=EvaluationConfidenceClass.MODERATE,
        evidence_quality=EvaluationEvidenceQuality.ADEQUATE,
        criterion_results=(),
    )
    assert any("criterion_results" in e for e in validate_evaluation_result(r))


def test_supported_result_requires_adequate_or_strong_evidence():
    r = EvaluationResult(
        result_id="r1", run_id="run1",
        status=EvaluationResultStatus.COMPLETED,
        outcome=EvaluationOutcome.PASSED, verdict=EvaluationVerdict.SUPPORTED,
        confidence=EvaluationConfidenceClass.LOW,
        evidence_quality=EvaluationEvidenceQuality.WEAK,
        criterion_results=(
            EvaluationCriterionResult(
                "c1", EvaluationOutcome.PASSED, EvaluationVerdict.SUPPORTED,
                EvaluationEvidenceQuality.ADEQUATE, evidence_refs=("ev1",),
            ),
        ),
    )
    assert any("ADEQUATE" in e for e in validate_evaluation_result(r))


def test_blocked_result_requires_blockers():
    r = EvaluationResult(
        result_id="r1", run_id="run1",
        status=EvaluationResultStatus.COMPLETED,
        outcome=EvaluationOutcome.BLOCKED, verdict=EvaluationVerdict.BLOCKED,
        confidence=EvaluationConfidenceClass.NONE,
        evidence_quality=EvaluationEvidenceQuality.NONE,
        blockers=(),
    )
    assert any("blockers" in e for e in validate_evaluation_result(r))


def test_failed_result_requires_failure_modes():
    r = EvaluationResult(
        result_id="r1", run_id="run1",
        status=EvaluationResultStatus.COMPLETED,
        outcome=EvaluationOutcome.FAILED, verdict=EvaluationVerdict.UNSUPPORTED,
        confidence=EvaluationConfidenceClass.LOW,
        evidence_quality=EvaluationEvidenceQuality.WEAK,
        failure_modes=(),
    )
    assert any("failure_modes" in e for e in validate_evaluation_result(r))


def test_error_result_requires_error_failure_mode():
    r = EvaluationResult(
        result_id="r1", run_id="run1",
        status=EvaluationResultStatus.ERROR,
        outcome=EvaluationOutcome.ERROR, verdict=EvaluationVerdict.UNKNOWN,
        confidence=EvaluationConfidenceClass.UNKNOWN,
        evidence_quality=EvaluationEvidenceQuality.UNKNOWN,
        failure_modes=(),
    )
    assert any("EVALUATOR_ERROR" in e for e in validate_evaluation_result(r))


def test_result_does_not_claim_capability_verified():
    from agentic_runtime.evaluation.evaluation_objects import example_supported_evaluation_result
    r = example_supported_evaluation_result()
    assert not hasattr(r, "verified")
    assert not hasattr(r, "capability_verified")
    assert "VERIFIED" not in r.verdict.value
